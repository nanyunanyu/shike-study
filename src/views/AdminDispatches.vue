<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronRight, RefreshCw } from 'lucide-vue-next'
import { dispatchTabs, type AdminAccount, type Dispatch, type DispatchDetail } from '../admin'
import { messageKinds, messageTime } from '../messages'
import { api, ApiError, notify } from '../state'
import GlassModal from '../components/ui/GlassModal.vue'
import PageSkeleton from '../components/ui/PageSkeleton.vue'

const props = defineProps<{ accounts: AdminAccount[]; timezone: string; revision: number }>()
const emit = defineEmits<{ changed: [] }>()
const route = useRoute()
const router = useRouter()

const status = computed(() => dispatchTabs.find(item => item.id === route.query.status)?.id ?? 'pending')
const recipient = computed(() =>
  typeof route.query.recipient === 'string' && /^[1-9][0-9]*$/.test(route.query.recipient) ? route.query.recipient : '',
)
const kind = computed(() =>
  route.query.kind === 'reminder' || route.query.kind === 'encouragement' ? route.query.kind : '',
)
const selectedKey = computed(() => (typeof route.query.dispatch === 'string' ? route.query.dispatch : ''))

const items = ref<Dispatch[]>([])
const cursor = ref<string | null>(null)
const loading = ref(false)
const error = ref('')
const record = ref<DispatchDetail | null>(null)
const detailError = ref('')
const busy = ref(false)
const cancelTarget = ref<{ path: string; name: string } | null>(null)

const learners = computed(() => props.accounts.filter(user => user.role === 'user'))
const dialog = computed({
  get: () => !!selectedKey.value,
  set: value => {
    if (!value) void navigate({ dispatch: undefined }, true)
  },
})

let listVersion = 0
let recordVersion = 0

function navigate(changes: Record<string, string | undefined>, replace = false) {
  const target = { name: 'admin', query: { ...route.query, section: 'messages', ...changes } }
  return replace ? router.replace(target) : router.push(target)
}

async function load(append = false) {
  const version = ++listVersion
  loading.value = true
  error.value = ''
  if (!append) {
    cursor.value = null
    items.value = []
  }
  const query = new URLSearchParams({ status: status.value })
  if (kind.value) query.set('kind', kind.value)
  if (recipient.value) query.set('recipient_id', recipient.value)
  if (append && cursor.value) query.set('cursor', cursor.value)
  try {
    const page = await api<{ items: Dispatch[]; next_cursor: string | null }>(`/admin/dispatches?${query}`)
    if (version !== listVersion) return
    items.value = append ? [...items.value, ...page.items] : page.items
    cursor.value = page.next_cursor
  } catch (e) {
    if (version === listVersion) error.value = (e as Error).message
  } finally {
    if (version === listVersion) loading.value = false
  }
}

async function loadDetail() {
  const version = ++recordVersion
  const key = selectedKey.value
  detailError.value = ''
  if (!key) return
  try {
    const data = await api<DispatchDetail>(`/admin/dispatches/${encodeURIComponent(key)}`)
    if (version === recordVersion) record.value = data
  } catch (e) {
    if (version === recordVersion) {
      record.value = null
      detailError.value = (e as Error).message
    }
  }
}

watch([status, recipient, kind, () => props.revision], () => void load(), { immediate: true })
watch(
  selectedKey,
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

function refresh() {
  void load()
  if (selectedKey.value && !cancelTarget.value) void loadDetail()
  emit('changed')
}

async function confirmCancel() {
  if (!cancelTarget.value || busy.value) return
  busy.value = true
  detailError.value = ''
  try {
    await api(cancelTarget.value.path, 'DELETE')
    notify('已取消待发消息')
    cancelTarget.value = null
    refresh()
  } catch (e) {
    if (e instanceof ApiError && (e.status === 404 || e.status === 409)) {
      cancelTarget.value = null
      await Promise.all([loadDetail(), load()])
      emit('changed')
    }
    detailError.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="glass-card admin-card">
    <header class="section-head">
      <h2>消息发送记录</h2>
      <button type="button" class="btn ghost sm" :disabled="loading" @click="refresh"><RefreshCw :size="14" />刷新</button>
    </header>

    <div class="dispatch-filters">
      <div class="segmented" role="group" aria-label="消息状态">
        <button
          v-for="tab in dispatchTabs"
          :key="tab.id"
          type="button"
          :aria-pressed="tab.id === status"
          @click="navigate({ status: tab.id, dispatch: undefined })"
        >
          {{ tab.label }}
        </button>
      </div>
      <select :value="recipient" style="max-width: 170px" @change="navigate({ recipient: ($event.target as HTMLSelectElement).value || undefined }, true)">
        <option value="">全部收件人</option>
        <option v-for="user in learners" :key="user.id" :value="String(user.id)">{{ user.username }}</option>
      </select>
      <select :value="kind" style="max-width: 150px" @change="navigate({ kind: ($event.target as HTMLSelectElement).value || undefined }, true)">
        <option value="">全部类型</option>
        <option v-for="(item, id) in messageKinds" :key="id" :value="id">{{ item.label }}</option>
      </select>
    </div>

    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    <PageSkeleton v-else-if="loading && !items.length" layout="dispatches" />
    <div v-else-if="!loading && !items.length" class="empty-box compact">暂无此类消息记录</div>

    <ul v-else class="dispatch-list">
      <li v-for="item in items" :key="item.key">
        <button type="button" class="dispatch-row" @click="navigate({ dispatch: item.key })">
          <span class="disp-icon"><component :is="messageKinds[item.kind].icon" :size="16" /></span>
          <span class="disp-body">
            <strong>{{ item.body }}</strong>
            <small class="tertiary">{{ messageKinds[item.kind].label }} · {{ messageTime(item.due_at, timezone) }}</small>
          </span>
          <span class="pill tabular">
            {{ item.recipient_count }} 人<template v-if="item.sent"> · {{ item.read }} 已读</template>
          </span>
          <ChevronRight :size="16" class="tertiary" />
        </button>
      </li>
    </ul>

    <div v-if="cursor" style="display: flex; justify-content: center">
      <button type="button" class="btn secondary sm" :disabled="loading" @click="load(true)">加载更多</button>
    </div>

    <GlassModal v-model="dialog" title="发送详情与已读回执" :busy="busy" drawer>
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
        <p class="muted">{{ messageKinds[record.kind].label }} · 投递时间 {{ messageTime(record.due_at, timezone) }}</p>
        <p class="glass-inset" style="padding: 14px; white-space: pre-wrap; line-height: 1.65">{{ record.body }}</p>
        <div class="section-head">
          <strong style="font-size: 14px">收件人 · {{ record.recipient_count }} 人</strong>
          <button
            v-if="record.pending"
            type="button"
            class="btn danger-ghost sm"
            @click="cancelTarget = { path: `/admin/dispatches/${record.key}`, name: `取消本批次剩余 ${record.pending} 条待发消息？` }"
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
                @click="cancelTarget = { path: `/admin/users/${user.id}/messages/${user.message_id}`, name: `取消给 ${user.username} 的待发消息？` }"
              >
                取消
              </button>
            </template>
            <span v-else-if="user.read_at !== null" class="pill success">已读 · {{ messageTime(user.read_at, timezone) }}</span>
            <span v-else class="pill">未读</span>
          </li>
        </ul>
      </div>
      <p v-else-if="detailError" class="error-text" role="alert">{{ detailError }}</p>
      <p v-else class="muted">正在加载详情…</p>
    </GlassModal>
  </section>
</template>

<style scoped>
.admin-card {
  padding: 20px 22px;
  display: grid;
  gap: 16px;
}
.admin-card h2 {
  font-size: 16px;
  font-weight: 680;
}
.dispatch-filters {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.dispatch-list {
  display: grid;
  gap: 8px;
}
.dispatch-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 15px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  text-align: left;
  transition: background 0.16s, border-color 0.16s;
}
.dispatch-row:hover {
  background: var(--surface-solid);
  border-color: var(--border-strong);
}
.disp-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  flex: none;
  background: var(--accent-soft);
  color: var(--accent);
}
.disp-body {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 3px;
}
.disp-body strong {
  font-size: 13.5px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
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
@media (max-width: 768px) {
  .admin-card {
    padding: 15px 14px;
    gap: 12px;
  }
  .dispatch-filters {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .dispatch-filters .segmented {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .dispatch-filters select {
    max-width: none !important;
  }
  .dispatch-row {
    padding: 10px 11px;
    gap: 9px;
  }
}
</style>
