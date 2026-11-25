<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { ArrowLeft, ArrowRight, Bell, Trash2, X } from 'lucide-vue-next'
import { activeDialogs, messageKinds, messageTime } from '../messages'
import { api, notify } from '../state'
import type { InboxMessage, InboxPage, MessagePreview } from '../types'
import GlassModal from './ui/GlassModal.vue'

const props = defineProps<{ timezone: string; clockOpen: boolean }>()

const unread = ref(0)
const pendingPreview = ref<MessagePreview | null>(null)
const hidden = ref(document.hidden)
const open = ref(false)
const selected = ref<InboxMessage | null>(null)
const items = ref<InboxMessage[]>([])
const before = ref<number | null>(null)
const loading = ref(false)
const listError = ref('')
const readError = ref('')
const deleteTarget = ref<InboxMessage | null>(null)
const deleting = ref(false)
const deleteError = ref('')

const blocked = computed(() => hidden.value || props.clockOpen || open.value || activeDialogs.value > 0)
const showFloat = computed(() => !blocked.value && pendingPreview.value !== null)
let disposed = false
let syncing = false
let readVersion = 0
let listVersion = 0
let autoHide = 0

async function sync() {
  hidden.value = document.hidden
  if (hidden.value || syncing || disposed) return
  syncing = true
  const version = readVersion
  try {
    const status = await api<{ unread: number; pending: boolean }>('/messages/status')
    if (disposed || version !== readVersion) return
    unread.value = status.unread
    if (status.pending && !blocked.value && !pendingPreview.value) {
      const preview = await api<MessagePreview | null>('/messages/preview', 'POST')
      if (!disposed && version === readVersion) pendingPreview.value = preview
    }
  } catch {
    /* retry later */
  } finally {
    syncing = false
    if (version !== readVersion && !disposed) void sync()
  }
}

async function load(next = false) {
  const version = ++listVersion
  loading.value = true
  listError.value = ''
  try {
    const result = await api<InboxPage>(`/messages${next ? `?before=${before.value}` : ''}`)
    if (disposed || version !== listVersion) return
    const detailItem = selected.value
    const page = result.items.map(item => (item.id === detailItem?.id && detailItem.read_at !== null ? detailItem : item))
    items.value = next ? [...items.value, ...page] : page
    before.value = result.next_before
  } catch (e) {
    if (version === listVersion) listError.value = (e as Error).message
  } finally {
    if (version === listVersion) loading.value = false
  }
}

async function markRead(message: InboxMessage) {
  if (message.read_at !== null) return
  readError.value = ''
  try {
    const result = await api<InboxMessage>(`/messages/${message.id}/read`, 'PUT')
    if (disposed) return
    if (selected.value?.id === result.id) selected.value = result
    items.value = items.value.map(item => (item.id === result.id ? result : item))
    readVersion++
    void sync()
  } catch (e) {
    if (selected.value?.id === message.id) readError.value = (e as Error).message
  }
}

function openDetail(message: InboxMessage) {
  selected.value = message
  readError.value = ''
  void markRead(message)
}

async function removeMessage() {
  const message = deleteTarget.value
  if (!message || deleting.value) return
  deleting.value = true
  deleteError.value = ''
  try {
    await api(`/messages/${message.id}`, 'DELETE')
    if (disposed) return
    listVersion++
    loading.value = false
    items.value = items.value.filter(item => item.id !== message.id)
    if (pendingPreview.value?.message.id === message.id) pendingPreview.value = null
    if (selected.value?.id === message.id) selected.value = null
    deleteTarget.value = null
    readVersion++
    void sync()
    if (!items.value.length) void load()
    notify('消息已删除')
  } catch (e) {
    if (!disposed) deleteError.value = (e as Error).message
  } finally {
    deleting.value = false
  }
}

function showInbox(message?: InboxMessage) {
  selected.value = null
  readError.value = ''
  items.value = []
  before.value = null
  deleteTarget.value = null
  deleteError.value = ''
  if (message) pendingPreview.value = null
  open.value = true
  if (message) openDetail(message)
  void load()
}

watch(showFloat, visible => {
  window.clearTimeout(autoHide)
  if (visible) {
    autoHide = window.setTimeout(() => {
      pendingPreview.value = null
    }, 8000)
  }
})

watch(blocked, value => {
  if (!value) void sync()
})

onMounted(sync)
onUnmounted(() => {
  disposed = true
  window.clearTimeout(autoHide)
})

defineExpose({ sync, showInbox, unread })
</script>

<template>
  <Teleport to="body">
    <Transition name="toast-slide">
      <aside v-if="showFloat && pendingPreview" class="float-notice glass-card-solid" aria-label="站内新消息">
        <div class="notice-icon">
          <component :is="messageKinds[pendingPreview.message.kind].icon" :size="17" />
        </div>
        <div class="notice-copy">
          <div class="notice-top">
            <strong>{{ messageKinds[pendingPreview.message.kind].label }}</strong>
            <span class="tertiary">{{ pendingPreview.message.sender }}</span>
          </div>
          <p>{{ pendingPreview.message.body }}</p>
          <small v-if="pendingPreview.more" class="accent-text">另有 {{ pendingPreview.more }} 条未读消息</small>
        </div>
        <div class="notice-actions">
          <button type="button" class="icon-btn sm" aria-label="查看详情" @click="showInbox(pendingPreview.message)">
            <ArrowRight :size="15" />
          </button>
          <button type="button" class="icon-btn sm" aria-label="暂不查看" @click="pendingPreview = null">
            <X :size="15" />
          </button>
        </div>
      </aside>
    </Transition>
  </Teleport>

  <GlassModal v-model="open" title="消息中心" subtitle="来自管理员的提醒与鼓励" :busy="deleting" drawer>
    <div v-if="deleteTarget" class="delete-box glass-inset">
      <p>确定从消息中心删除这条消息？</p>
      <p v-if="deleteError" class="error-text" role="alert">{{ deleteError }}</p>
      <div class="dialog-actions">
        <button type="button" class="btn ghost sm" :disabled="deleting" @click="deleteTarget = null">取消</button>
        <button type="button" class="btn danger sm" :disabled="deleting" @click="removeMessage">
          {{ deleting ? '删除中…' : '确认删除' }}
        </button>
      </div>
    </div>

    <article v-if="selected" class="detail-view">
      <button type="button" class="btn ghost sm back-btn" @click="selected = null; if (!loading) void load()">
        <ArrowLeft :size="15" />返回列表
      </button>
      <div class="detail-head">
        <span class="pill accent">
          <component :is="messageKinds[selected.kind].icon" :size="13" />
          {{ messageKinds[selected.kind].label }}
        </span>
        <span class="muted">{{ selected.sender }} · {{ messageTime(selected.due_at, timezone) }}</span>
      </div>
      <p class="detail-body glass-inset">{{ selected.body }}</p>
      <p v-if="readError" class="error-text" role="alert">
        {{ readError }} <button type="button" class="btn ghost sm" @click="markRead(selected)">重试</button>
      </p>
      <div>
        <button type="button" class="btn danger-ghost sm" @click="deleteTarget = selected">
          <Trash2 :size="15" />删除消息
        </button>
      </div>
    </article>

    <div v-else class="inbox-view">
      <p v-if="listError" class="error-text" role="alert">
        {{ listError }} <button type="button" class="btn ghost sm" @click="load()">重试</button>
      </p>
      <div v-if="!loading && !listError && !items.length" class="empty-box compact">
        <Bell :size="22" class="tertiary" />
        <p>目前没有站内消息</p>
      </div>
      <ul v-else class="inbox-list">
        <li v-for="item in items" :key="item.id" class="inbox-row">
          <button type="button" class="inbox-main" @click="openDetail(item)">
            <span class="inbox-icon" :class="{ unread: item.read_at === null }">
              <component :is="messageKinds[item.kind].icon" :size="16" />
            </span>
            <span class="inbox-text">
              <span class="inbox-meta">
                <strong>{{ messageKinds[item.kind].label }}</strong>
                <span v-if="item.read_at === null" class="unread-dot">未读</span>
                <small class="tertiary">{{ messageTime(item.due_at, timezone) }}</small>
              </span>
              <span class="inbox-snippet">{{ item.body }}</span>
            </span>
          </button>
          <button type="button" class="icon-btn sm danger-ghost" aria-label="删除消息" @click="deleteTarget = item">
            <Trash2 :size="15" />
          </button>
        </li>
      </ul>
      <p v-if="loading" class="muted" style="text-align: center; padding: 12px">正在加载…</p>
      <button v-else-if="before !== null" type="button" class="btn secondary sm full" @click="load(true)">加载更早消息</button>
    </div>
  </GlassModal>
</template>

<style scoped>
.float-notice {
  position: fixed;
  z-index: 90;
  top: max(14px, env(safe-area-inset-top));
  left: 50%;
  transform: translateX(-50%);
  width: min(400px, calc(100vw - 28px));
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 13px 12px 13px 15px;
  border-radius: 18px;
}
.notice-icon {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  flex: none;
  background: var(--accent-soft);
  color: var(--accent);
}
.notice-copy {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 3px;
}
.notice-top {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
}
.notice-copy p {
  font-size: 13px;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.notice-actions {
  display: flex;
  gap: 2px;
  flex: none;
}
.delete-box {
  padding: 14px;
  display: grid;
  gap: 10px;
  margin-bottom: 14px;
}
.detail-view {
  display: grid;
  gap: 14px;
}
.back-btn {
  justify-self: start;
}
.detail-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 12.5px;
}
.detail-body {
  padding: 16px;
  white-space: pre-wrap;
  line-height: 1.7;
  overflow-wrap: anywhere;
}
.inbox-list {
  display: grid;
  gap: 8px;
}
.inbox-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  border-radius: 14px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
}
.inbox-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 8px 6px 8px 10px;
  text-align: left;
  border-radius: 11px;
}
.inbox-main:hover {
  background: var(--surface-hover);
}
.inbox-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  flex: none;
  background: var(--surface-solid);
  color: var(--ink-secondary);
}
.inbox-icon.unread {
  background: var(--accent-soft);
  color: var(--accent);
}
.inbox-text {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 3px;
}
.inbox-meta {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
}
.inbox-meta small {
  margin-left: auto;
  font-size: 11px;
}
.unread-dot {
  padding: 1px 6px;
  border-radius: var(--radius-pill);
  background: var(--accent);
  color: var(--on-accent);
  font-size: 10px;
  font-weight: 650;
}
.inbox-snippet {
  font-size: 13px;
  color: var(--ink-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
