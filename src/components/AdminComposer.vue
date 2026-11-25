<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowLeft, Send } from 'lucide-vue-next'
import type { AdminAccount } from '../admin'
import type { MessageKind } from '../types'
import { messageKinds } from '../messages'
import { api, ApiError, notify, session } from '../state'
import GlassModal from './ui/GlassModal.vue'

const props = defineProps<{ accounts: AdminAccount[]; initialRecipients: number[]; timezone: string }>()
const emit = defineEmits<{ sent: [key: string, scheduled: boolean]; refresh: []; 'after-leave': [] }>()
const open = defineModel<boolean>({ required: true })

const kind = ref<MessageKind>('reminder')
const body = ref('')
const scheduled = ref(false)
const dateTime = ref('')
const search = ref('')
const checkin = ref('all')
const selected = ref(new Set(props.initialRecipients))
const allActive = ref(false)
const error = ref('')
const busy = ref(false)
const reviewing = ref(false)

const active = computed(() =>
  props.accounts.filter(user => user.role === 'user' && user.active).sort((a, b) => a.username.localeCompare(b.username)),
)
const recipients = computed(() => active.value.filter(user => selected.value.has(user.id)))
const options = computed(() =>
  active.value.filter(
    user =>
      user.username.toLowerCase().includes(search.value.trim().toLowerCase()) &&
      (checkin.value === 'all' || user.checked_today === (checkin.value === 'checked')),
  ),
)
const length = computed(() => Array.from(body.value.trim()).length)
const valid = computed(
  () => recipients.value.length > 0 && length.value > 0 && length.value <= 300 && (!scheduled.value || !!dateTime.value),
)
const title = computed(() =>
  props.initialRecipients.length === 1 && recipients.value.length === 1
    ? `发消息给 ${recipients.value[0]!.username}`
    : '新建站内消息',
)

type Draft = { recipient_ids: number[]; kind: MessageKind; body: string; scheduled_for: string | null; all_active: boolean }
const reviewed = ref<{ payload: Draft; names: string[] } | null>(null)
const pendingAttempts = new Map<string, string>()

function toHex(bytes: Uint8Array) {
  return Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('')
}

function getAttempt(signature: string) {
  let attempt = pendingAttempts.get(signature)
  if (!attempt) {
    attempt = toHex(crypto.getRandomValues(new Uint8Array(16)))
    pendingAttempts.set(signature, attempt)
  }
  return attempt
}

watch(active, users => {
  const eligible = new Set(users.map(user => user.id))
  selected.value = allActive.value ? eligible : new Set([...selected.value].filter(id => eligible.has(id)))
})

function chooseAll() {
  selected.value = new Set(active.value.map(user => user.id))
  allActive.value = true
}

function reviewDraft() {
  if (!valid.value) return
  const payload: Draft = {
    recipient_ids: recipients.value.map(user => user.id).sort((a, b) => a - b),
    kind: kind.value,
    body: body.value.trim(),
    scheduled_for: scheduled.value ? dateTime.value : null,
    all_active: allActive.value,
  }
  reviewed.value = { payload, names: recipients.value.map(user => user.username) }
  error.value = ''
  reviewing.value = true
}

async function send() {
  const draft = reviewed.value
  if (!draft || busy.value || !session.value) return
  error.value = ''
  busy.value = true
  const signature = JSON.stringify(draft.payload)
  try {
    const result = await api<{ key: string | null }>('/admin/dispatches', 'POST', {
      ...draft.payload,
      request_id: getAttempt(signature),
    })
    pendingAttempts.delete(signature)
    open.value = false
    const planned = draft.payload.scheduled_for !== null
    notify(!result.key ? '收件账号已变化' : planned ? '已安排定时发送' : '消息已发送')
    if (result.key) emit('sent', result.key, planned)
  } catch (e) {
    error.value = (e as Error).message
    if (e instanceof ApiError && e.status >= 400 && e.status < 500) pendingAttempts.delete(signature)
    if (e instanceof ApiError && e.status === 409) {
      reviewing.value = false
      emit('refresh')
    }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <GlassModal v-model="open" :title="title" :busy="busy" drawer @after-leave="emit('after-leave')">
    <form v-if="!reviewing" class="form-stack" @submit.prevent="reviewDraft">
      <div class="field">
        <span class="field-label">选择收件账号（已选 {{ recipients.length }} 人）</span>
        <div class="field-grid">
          <input v-model="search" placeholder="搜索用户名…" />
          <select v-model="checkin">
            <option value="all">全部打卡状态</option>
            <option value="checked">今日已打卡</option>
            <option value="unchecked">今日未打卡</option>
          </select>
        </div>
        <div class="sel-actions">
          <button type="button" class="btn ghost sm" :disabled="!active.length" @click="chooseAll">选择全体已启用</button>
          <button type="button" class="btn ghost sm" :disabled="!selected.size" @click="selected = new Set(); allActive = false">清空</button>
        </div>
        <ul v-if="options.length" class="recipient-list glass-inset">
          <li v-for="user in options" :key="user.id">
            <label class="recipient-check">
              <input v-model="selected" type="checkbox" :value="user.id" @change="allActive = false" />
              <span>{{ user.username }}</span>
              <span class="pill" :class="{ success: user.checked_today }" style="margin-left: auto">
                {{ user.checked_today ? '已打卡' : '未打卡' }}
              </span>
            </label>
          </li>
        </ul>
        <p v-else class="muted" style="font-size: 12.5px">没有符合筛选条件的已启用学习账号</p>
      </div>

      <label class="field">
        <span class="field-label">消息类型</span>
        <select v-model="kind">
          <option v-for="(item, id) in messageKinds" :key="id" :value="id">{{ item.label }}</option>
        </select>
      </label>

      <label class="field">
        <span class="field-label">消息正文（{{ length }} / 300）</span>
        <textarea v-model="body" rows="4" required maxlength="300" placeholder="写一句温和的提醒或加油…" />
      </label>

      <label class="switch-row glass-inset" style="padding: 8px 14px">
        <span>预约定时发送</span>
        <input v-model="scheduled" type="checkbox" role="switch" />
      </label>

      <label v-if="scheduled" class="field">
        <span class="field-label">投递时间（{{ timezone }}）</span>
        <input v-model="dateTime" type="datetime-local" required />
      </label>

      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="dialog-actions">
        <button type="submit" class="btn primary full" :disabled="!valid">下一步：核对名单与内容</button>
      </div>
    </form>

    <div v-else-if="reviewed" class="form-stack">
      <h3>确认发送给 {{ reviewed.names.length }} 位学习者</h3>
      <div class="confirm-tags">
        <span v-for="name in reviewed.names" :key="name" class="pill">{{ name }}</span>
      </div>
      <p class="muted" style="font-size: 12.5px">
        {{ messageKinds[reviewed.payload.kind].label }} ·
        {{ reviewed.payload.scheduled_for ? `${reviewed.payload.scheduled_for.replace('T', ' ')}（${timezone}）` : '立即发送' }}
      </p>
      <p class="glass-inset" style="padding: 14px; white-space: pre-wrap; line-height: 1.65">{{ reviewed.payload.body }}</p>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="dialog-actions">
        <button type="button" class="btn ghost" :disabled="busy" @click="reviewing = false"><ArrowLeft :size="15" />返回修改</button>
        <button type="button" class="btn primary" :disabled="busy" @click="send">
          <Send :size="15" />{{ busy ? '发送中…' : reviewed.payload.scheduled_for ? '确认定时发送' : '确认立即发送' }}
        </button>
      </div>
    </div>
  </GlassModal>
</template>

<style scoped>
.sel-actions {
  display: flex;
  gap: 6px;
}
.recipient-list {
  max-height: 180px;
  overflow-y: auto;
  padding: 6px;
  display: grid;
  gap: 2px;
}
.recipient-check {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 9px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
}
.recipient-check:hover {
  background: var(--surface-hover);
}
.confirm-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
