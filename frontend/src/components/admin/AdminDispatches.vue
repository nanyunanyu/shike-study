<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronRight, RefreshCw } from 'lucide-vue-next'
import { fetchAdminDispatchesApi } from '@/api/admin'
import PageSkeleton from '@/components/ui/PageSkeleton.vue'
import { DISPATCH_TABS, MESSAGE_KINDS } from '@/constants/messages'
import type { AdminAccount, Dispatch, MessageKind } from '@/types'
import { formatMessageTime } from '@/utils/date'
import AdminDispatchDrawer from './AdminDispatchDrawer.vue'

const props = defineProps<{ accounts: AdminAccount[]; timezone: string; revision: number }>()
const emit = defineEmits<{ changed: [] }>()
const route = useRoute()
const router = useRouter()

const status = computed(() => DISPATCH_TABS.find(item => item.id === route.query.status)?.id ?? 'pending')
const recipient = computed(() =>
  typeof route.query.recipient === 'string' && /^[1-9][0-9]*$/.test(route.query.recipient) ? route.query.recipient : '',
)
const kind = computed<MessageKind | ''>(() =>
  route.query.kind === 'reminder' || route.query.kind === 'encouragement' ? route.query.kind : '',
)
const selectedKey = computed(() => (typeof route.query.dispatch === 'string' ? route.query.dispatch : ''))

const items = ref<Dispatch[]>([])
const cursor = ref<string | null>(null)
const loading = ref(false)
const error = ref('')
const drawerRef = ref<InstanceType<typeof AdminDispatchDrawer> | null>(null)

const learners = computed(() => props.accounts.filter(user => user.role === 'user'))
const dialog = computed({
  get: () => !!selectedKey.value,
  set: value => {
    if (!value) void navigate({ dispatch: undefined }, true)
  },
})

let listVersion = 0

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
  try {
    const page = await fetchAdminDispatchesApi({
      status: status.value,
      kind: kind.value,
      recipientId: recipient.value,
      cursor: append ? cursor.value : null,
    })
    if (version !== listVersion) return
    items.value = append ? [...items.value, ...page.items] : page.items
    cursor.value = page.next_cursor
  } catch (e) {
    if (version === listVersion) error.value = (e as Error).message
  } finally {
    if (version === listVersion) loading.value = false
  }
}

watch([status, recipient, kind, () => props.revision], () => void load(), { immediate: true })

function refresh() {
  void load()
  drawerRef.value?.reload()
  emit('changed')
}

function onDrawerChanged() {
  void load()
  emit('changed')
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
          v-for="tab in DISPATCH_TABS"
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
        <option v-for="(item, id) in MESSAGE_KINDS" :key="id" :value="id">{{ item.label }}</option>
      </select>
    </div>

    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    <PageSkeleton v-else-if="loading && !items.length" layout="dispatches" />
    <div v-else-if="!loading && !items.length" class="empty-box compact">暂无此类消息记录</div>

    <ul v-else class="dispatch-list">
      <li v-for="item in items" :key="item.key">
        <button type="button" class="dispatch-row" @click="navigate({ dispatch: item.key })">
          <span class="disp-icon"><component :is="MESSAGE_KINDS[item.kind].icon" :size="16" /></span>
          <span class="disp-body">
            <strong>{{ item.body }}</strong>
            <small class="tertiary">{{ MESSAGE_KINDS[item.kind].label }} · {{ formatMessageTime(item.due_at, timezone) }}</small>
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

    <AdminDispatchDrawer
      ref="drawerRef"
      v-model="dialog"
      :dispatch-key="selectedKey"
      :timezone="timezone"
      @changed="onDrawerChanged"
    />
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
