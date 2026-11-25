<script setup lang="ts">
import { ref, watch } from 'vue'
import { cancelAdminDispatchApi, cancelAdminUserMessageApi, fetchAdminDispatchDetailApi } from '@/api/admin'
import { ApiError } from '@/api/client'
import GlassModal from '@/components/ui/GlassModal.vue'
import { MESSAGE_KINDS } from '@/constants/messages'
import { notify } from '@/stores/ui'
import type { DispatchDetail } from '@/types'
import { formatMessageTime } from '@/utils/date'

type CancelTarget =
  | { type: 'batch'; key: string; name: string }
  | { type: 'single'; uid: number; messageId: number; name: string }

const open = defineModel<boolean>({ required: true })
const props = defineProps<{
  dispatchKey: string
  timezone: string
}>()
const emit = defineEmits<{ changed: [] }>()

const record = ref<DispatchDetail | null>(null)
const detailError = ref('')
const busy = ref(false)
const cancelTarget = ref<CancelTarget | null>(null)
let recordVersion = 0

async function loadDetail() {
  const version = ++recordVersion
  const key = props.dispatchKey
  detailError.value = ''
  if (!key) return
  try {
    const data = await fetchAdminDispatchDetailApi(key)
    if (version === recordVersion) record.value = data
  } catch (e) {
    if (version === recordVersion) {
      record.value = null
      detailError.value = (e as Error).message
    }
  }
}

watch(
  () => props.dispatchKey,
  key => {
    cancelTarget.value = null
    if (key) {
      record.value = null
      void loadDetail()
    } else {
      recordVersion++
    }
  },
  { immediate: true },
)

async function confirmCancel() {
  const target = cancelTarget.value
  if (!target || busy.value) return
  busy.value = true
  detailError.value = ''
  try {
    if (target.type === 'batch') await cancelAdminDispatchApi(target.key)
    else await cancelAdminUserMessageApi(target.uid, target.messageId)
    notify('已取消待发消息')
    cancelTarget.value = null
    await loadDetail()
    emit('changed')
  } catch (e) {
    if (e instanceof ApiError && (e.status === 404 || e.status === 409)) {
      cancelTarget.value = null
      await loadDetail()
      emit('changed')
    }
    detailError.value = (e as Error).message
  } finally {
    busy.value = false
  }
}

function reload() {
  if (props.dispatchKey && !cancelTarget.value) void loadDetail()
}

defineExpose({ reload })
</script>

<template>
  <GlassModal v-model="open" title="发送详情与已读回执" :busy="busy" drawer>
    <div v-if="cancelTarget" class="form-stack">
      <h3>确认取消待发消息</h3>
      <p class="muted">{{ cancelTarget.name }}</p>
      <p v-if="detailError" class="error-text" role="alert">{{ detailError }}</p>
      <div class="dialog-actions">
        <button type="button" class="btn ghost" :disabled="busy" @click="cancelTarget = null">返回</button>
        <button type="button" class="btn danger" :disabled="busy" @click="confirmCancel">确认取消</button>
      </div>
    </div>

    <div v-else-if="record" class="form-stack">
      <p class="muted">{{ MESSAGE_KINDS[record.kind].label }} · 投递时间 {{ formatMessageTime(record.due_at, timezone) }}</p>
      <p class="glass-inset" style="padding: 14px; white-space: pre-wrap; line-height: 1.65">{{ record.body }}</p>
      <div class="section-head">
        <strong style="font-size: 14px">收件人 · {{ record.recipient_count }} 人</strong>
        <button
          v-if="record.pending"
          type="button"
          class="btn danger-ghost sm"
          @click="cancelTarget = { type: 'batch', key: record.key, name: `取消本批次剩余 ${record.pending} 条待发消息？` }"
        >
          取消整个批次
        </button>
      </div>
      <ul class="receipt-list">
        <li v-for="user in record.recipients" :key="user.message_id" class="receipt-row">
          <strong>{{ user.username }}</strong>
          <span v-if="user.canceled_at !== null" class="pill">已取消</span>
          <template v-else-if="record.pending">
            <span class="pill warning">待发</span>
            <button
              type="button"
              class="btn ghost sm"
              @click="
                cancelTarget = {
                  type: 'single',
                  uid: user.id,
                  messageId: user.message_id,
                  name: `取消给 ${user.username} 的待发消息？`,
                }
              "
            >
              取消
            </button>
          </template>
          <span v-else-if="user.read_at !== null" class="pill success">已读 · {{ formatMessageTime(user.read_at, timezone) }}</span>
          <span v-else class="pill">未读</span>
        </li>
      </ul>
    </div>
    <p v-else-if="detailError" class="error-text" role="alert">{{ detailError }}</p>
    <p v-else class="muted">正在加载详情…</p>
  </GlassModal>
</template>

<style scoped>
.receipt-list {
  display: grid;
  gap: 6px;
}
.receipt-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 12px;
  background: var(--surface-subtle);
}
.receipt-row strong {
  margin-right: auto;
  font-size: 13px;
}
</style>
