<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Bell,
  BookMarked,
  CalendarDays,
  ChartNoAxesCombined,
  CheckCircle2,
  CircleUserRound,
  ListChecks,
  ShieldCheck,
  Timer as TimerIcon,
  X,
} from 'lucide-vue-next'
import AuthGate from './components/AuthGate.vue'
import FloatingClock from './components/FloatingClock.vue'
import MessageCenter from './components/MessageCenter.vue'
import BrandMark from './components/ui/BrandMark.vue'
import PageSkeleton from './components/ui/PageSkeleton.vue'
import {
  api,
  ApiError,
  duration,
  focusCompletion,
  notify,
  preferences,
  resetFocusObservation,
  session,
  setSession,
  syncTimer,
  tickClock,
  timer,
  timerSeconds,
  timerText,
  toast,
  todayFocusSeconds,
} from './state'
import { playCompletionChime } from './utils/soundscape'
import type { Session } from './types'

const router = useRouter()
const route = useRoute()

const checking = ref(true)
const initialized = ref(true)
const startupProblem = ref('')
const mobileNav = ref<HTMLElement | null>(null)
const messages = ref<InstanceType<typeof MessageCenter> | null>(null)
const clockPanelOpen = ref(false)
const showToast = ref(false)

const unread = computed(() => messages.value?.unread ?? 0)
const clockAccount = computed(() => (session.value ? `${session.value.user.id}:${session.value.user.username}` : ''))
const goalRatio = computed(() =>
  Math.min(100, Math.round((todayFocusSeconds.value / Math.max(60, preferences.value.daily_focus_goal_minutes * 60)) * 100)),
)

const nav = computed(() => [
  { name: 'today', label: '今日', icon: CalendarDays },
  { name: 'timer', label: '专注', icon: TimerIcon },
  { name: 'plan', label: '计划', icon: ListChecks },
  { name: 'reviews', label: '复盘', icon: BookMarked },
  { name: 'stats', label: '统计', icon: ChartNoAxesCombined },
  { name: 'me', label: '我的', icon: CircleUserRound },
  ...(session.value?.user.role === 'admin' ? [{ name: 'admin', label: '后台', icon: ShieldCheck }] : []),
])

const mobileNavItems = computed(() => nav.value)

let toastTimer = 0
let clockInterval = 0
let syncInterval = 0
let completionToast = -1

watch(
  () => toast.version,
  () => {
    showToast.value = true
    window.clearTimeout(toastTimer)
    toastTimer = window.setTimeout(() => {
      showToast.value = false
    }, 3800)
  },
)

watch(focusCompletion, id => {
  if (id) {
    playCompletionChime()
    if (!clockPanelOpen.value || route.name === 'timer') {
      notify('本轮专注已完成，已自动记入专注统计')
      completionToast = toast.version
    }
  }
})

function clockOpenChanged(open: boolean) {
  clockPanelOpen.value = open
  if (open && completionToast === toast.version) showToast.value = false
}

watch([session, () => route.name], () => {
  if (session.value && session.value.user.role !== 'admin' && route.name === 'admin') {
    void router.replace({ name: 'today' })
  }
})

watch(
  () => [session.value?.csrf, session.value?.user.must_change],
  () => {
    void syncTimer()
  },
)

async function bootstrap() {
  checking.value = true
  startupProblem.value = ''
  try {
    try {
      setSession(await api<Session>('/auth/me'))
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 401)) throw error
      initialized.value = (await api<{ initialized: boolean }>('/status')).initialized
    }
  } catch (error) {
    startupProblem.value = (error as Error).message
  } finally {
    checking.value = false
  }
}

function syncForeground() {
  if (!document.hidden) void syncTimer()
  void messages.value?.sync()
}

function onForeground() {
  if (!document.hidden) {
    tickClock()
    syncForeground()
  }
}

function onVisibility() {
  if (document.hidden) {
    resetFocusObservation()
    void messages.value?.sync()
  } else {
    onForeground()
  }
}

onMounted(() => {
  void bootstrap()
  clockInterval = window.setInterval(tickClock, 250)
  syncInterval = window.setInterval(syncForeground, 12000)
  document.addEventListener('visibilitychange', onVisibility)
  window.addEventListener('focus', onForeground)
})

onUnmounted(() => {
  window.clearInterval(clockInterval)
  window.clearInterval(syncInterval)
  window.clearTimeout(toastTimer)
  document.removeEventListener('visibilitychange', onVisibility)
  window.removeEventListener('focus', onForeground)
})
</script>

<template>
  <div v-if="checking || startupProblem" class="boot-stage">
    <div class="boot-card glass-card">
      <PageSkeleton v-if="checking" layout="session" />
      <template v-else>
        <p class="error-text" role="alert">{{ startupProblem }}</p>
        <button type="button" class="btn secondary" @click="bootstrap">重试连接</button>
      </template>
    </div>
  </div>

  <AuthGate v-else-if="!session || session.user.must_change" :initialized="initialized" @retry="bootstrap" />

  <div v-else class="studio-shell">
    <!-- Desktop Floating Glass Sidebar -->
    <aside class="glass-sidebar glass-card" aria-label="侧边导航栏">
      <RouterLink :to="{ name: 'today' }" class="sidebar-brand" aria-label="拾刻学习">
        <BrandMark />
      </RouterLink>

      <nav class="sidebar-nav" aria-label="主导航">
        <RouterLink
          v-for="item in nav"
          :key="item.name"
          :to="{ name: item.name }"
          class="nav-pill"
          :class="{ 'is-admin': item.name === 'admin' }"
        >
          <component :is="item.icon" :size="18" :stroke-width="1.9" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <!-- Mini Daily Focus Goal Widget -->
      <div class="sidebar-foot">
        <div class="mini-goal glass-inset">
          <div class="mini-goal-head">
            <span>今日专注目标</span>
            <strong class="tabular">{{ goalRatio }}%</strong>
          </div>
          <div class="mini-goal-track">
            <span :style="{ width: `${goalRatio}%` }"></span>
          </div>
          <small class="tertiary tabular">
            {{ duration(todayFocusSeconds) }} / {{ Math.round(preferences.daily_focus_goal_minutes / 60 * 10) / 10 }} 小时
          </small>
        </div>

        <button
          v-if="session.user.role === 'user'"
          type="button"
          class="bell-row"
          @click="messages?.showInbox()"
        >
          <Bell :size="17" />
          <span>消息中心</span>
          <span v-if="unread" class="unread-badge tabular">{{ unread > 99 ? '99+' : unread }}</span>
        </button>

        <RouterLink :to="{ name: 'me' }" class="account-pill">
          <span class="avatar-circle">{{ session.user.username.slice(0, 1).toUpperCase() }}</span>
          <span class="account-meta">
            <strong>{{ session.user.username }}</strong>
            <small>{{ session.user.role === 'admin' ? '超级管理员' : '学习者' }}</small>
          </span>
        </RouterLink>
      </div>
    </aside>

    <!-- Mobile Sticky Frosted Header -->
    <header class="mobile-bar">
      <RouterLink :to="{ name: 'today' }" aria-label="拾刻学习">
        <BrandMark compact />
      </RouterLink>
      <div class="mobile-bar-right">
        <RouterLink
          v-if="timer && route.name !== 'timer'"
          :to="{ name: 'timer' }"
          class="mobile-live-timer tabular"
          aria-label="查看进行中的专注计时"
        >
          <span class="live-dot" :class="{ paused: timer.running_since === null }"></span>
          <span>{{ timerText(timerSeconds) }}</span>
        </RouterLink>
        <button
          v-if="session.user.role === 'user'"
          type="button"
          class="icon-btn mobile-bell"
          aria-label="消息中心"
          @click="messages?.showInbox()"
        >
          <Bell :size="18" />
          <span v-if="unread" class="mobile-badge tabular">{{ unread > 99 ? '99+' : unread }}</span>
        </button>
        <RouterLink :to="{ name: 'me' }" class="avatar-circle mobile-avatar" aria-label="我的账号">
          {{ session.user.username.slice(0, 1).toUpperCase() }}
        </RouterLink>
      </div>
    </header>

    <!-- Main Workspace -->
    <main id="main-content" class="studio-main" tabindex="-1">
      <RouterView v-slot="{ Component, route: current }">
        <Transition name="page-fade" mode="out-in">
          <component
            :is="Component"
            :key="current.name"
            v-if="current.name !== 'admin' || session.user.role === 'admin'"
          />
        </Transition>
      </RouterView>
    </main>

    <!-- Mobile Floating Capsule Dock -->
    <nav ref="mobileNav" class="mobile-dock glass-card-solid" aria-label="移动导航">
      <RouterLink v-for="item in mobileNavItems" :key="item.name" :to="{ name: item.name }" class="dock-item">
        <component :is="item.icon" :size="19" :stroke-width="1.9" />
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>

    <FloatingClock
      v-if="route.name !== 'timer'"
      :key="clockAccount"
      :account="clockAccount"
      :bottom-nav="mobileNav"
      @open-change="clockOpenChanged"
    />

    <MessageCenter
      v-if="session.user.role === 'user'"
      ref="messages"
      :key="session.csrf"
      :timezone="session.timezone"
      :clock-open="clockPanelOpen"
    />
  </div>

  <!-- Global Frosted Toast -->
  <Teleport to="body">
    <Transition name="toast-slide">
      <div
        v-if="showToast"
        class="studio-toast glass-card-solid"
        :class="{ 'is-error': toast.error }"
        :role="toast.error ? 'alert' : 'status'"
      >
        <CheckCircle2 v-if="!toast.error" :size="17" class="accent-text" />
        <span>{{ toast.message }}</span>
        <button type="button" class="icon-btn sm" aria-label="关闭提示" @click="showToast = false">
          <X :size="14" />
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.boot-stage {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 24px;
}
.boot-card {
  width: min(100%, 320px);
  padding: 28px 24px;
  display: grid;
  gap: 14px;
  justify-items: center;
}

.studio-shell {
  --sidebar-w: 238px;
  --sidebar-gap: 14px;
  --sidebar-offset: calc(var(--sidebar-w) + var(--sidebar-gap));
  min-height: 100dvh;
}

.glass-sidebar {
  position: fixed;
  top: var(--sidebar-gap);
  left: var(--sidebar-gap);
  bottom: var(--sidebar-gap);
  width: var(--sidebar-w);
  z-index: 40;
  padding: 20px 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  border-radius: 24px;
}

.sidebar-brand {
  padding: 2px 6px;
}

.sidebar-nav {
  display: grid;
  gap: 4px;
}

.nav-pill {
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 42px;
  padding: 0 13px;
  border-radius: 13px;
  color: var(--ink-secondary);
  font-size: 13.5px;
  font-weight: 560;
  transition: background 0.18s var(--ease-out), color 0.18s, transform 0.15s;
}

.nav-pill:hover {
  background: var(--surface-hover);
  color: var(--ink);
}

.nav-pill.router-link-exact-active {
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 640;
  box-shadow: inset 0 0 0 1px var(--accent-border);
}

.nav-pill.is-admin {
  margin-top: 10px;
  position: relative;
}

.nav-pill.is-admin::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 10px;
  right: 10px;
  height: 1px;
  background: var(--border);
}

.sidebar-foot {
  margin-top: auto;
  display: grid;
  gap: 10px;
}

.mini-goal {
  padding: 11px 12px;
  display: grid;
  gap: 7px;
  border-radius: 14px;
}

.mini-goal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11.5px;
  color: var(--ink-secondary);
}

.mini-goal-head strong {
  color: var(--accent);
  font-weight: 680;
}

.mini-goal-track {
  height: 5px;
  border-radius: var(--radius-pill);
  background: var(--surface-hover);
  overflow: hidden;
}

.mini-goal-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  transition: width 0.5s var(--ease-spring);
}

.mini-goal small {
  font-size: 11px;
}

.bell-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 38px;
  padding: 0 12px;
  border-radius: 12px;
  color: var(--ink-secondary);
  font-size: 13px;
  font-weight: 560;
  transition: background 0.16s, color 0.16s;
}

.bell-row:hover {
  background: var(--surface-hover);
  color: var(--ink);
}

.unread-badge {
  margin-left: auto;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: var(--radius-pill);
  background: var(--accent);
  color: var(--on-accent);
  font-size: 11px;
  font-weight: 700;
  display: grid;
  place-items: center;
}

.account-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--surface-subtle);
  transition: background 0.18s, border-color 0.18s;
}

.account-pill:hover {
  background: var(--surface-hover);
  border-color: var(--border-strong);
}

.account-meta {
  min-width: 0;
  display: grid;
  line-height: 1.2;
}

.account-meta strong {
  font-size: 13px;
  font-weight: 630;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-meta small {
  margin-top: 2px;
  font-size: 11px;
  color: var(--ink-tertiary);
}

.studio-main {
  min-width: 0;
  margin-left: var(--sidebar-offset);
}

.mobile-bar,
.mobile-dock {
  display: none;
}

.studio-toast {
  position: fixed;
  left: 50%;
  bottom: 24px;
  transform: translateX(-50%);
  z-index: 200;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px 8px 16px;
  border-radius: var(--radius-pill);
  font-size: 13px;
  font-weight: 560;
  max-width: calc(100vw - 28px);
}

.studio-toast.is-error {
  color: var(--danger);
  border-color: color-mix(in srgb, var(--danger) 30%, transparent);
}

@media (max-width: 1024px) {
  .studio-shell {
    --sidebar-w: 206px;
  }
}

@media (max-width: 768px) {
  .studio-shell {
    --sidebar-offset: 0px;
  }
  .glass-sidebar {
    display: none;
  }
  .studio-main {
    margin-left: 0;
  }
  .mobile-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 40;
    padding: max(8px, env(safe-area-inset-top)) 14px 8px;
    background: var(--surface-glass);
    backdrop-filter: blur(22px) saturate(175%);
    -webkit-backdrop-filter: blur(22px) saturate(175%);
    border-bottom: 1px solid var(--border);
  }
  .mobile-bar-right {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .mobile-live-timer {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: var(--radius-pill);
    background: var(--accent-soft);
    border: 1px solid var(--accent-border);
    color: var(--accent);
    font-size: 12px;
    font-weight: 660;
  }
  .live-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse-soft 1.6s infinite;
  }
  .live-dot.paused {
    animation: none;
    opacity: 0.45;
  }
  .mobile-bell {
    position: relative;
  }
  .mobile-badge {
    position: absolute;
    top: 2px;
    right: 2px;
    min-width: 15px;
    height: 15px;
    padding: 0 3.5px;
    border-radius: var(--radius-pill);
    background: var(--accent);
    color: var(--on-accent);
    font-size: 9.5px;
    font-weight: 700;
    display: grid;
    place-items: center;
  }
  .mobile-avatar {
    width: 30px;
    height: 30px;
    font-size: 12.5px;
  }
  .mobile-dock {
    display: flex;
    align-items: center;
    position: fixed;
    left: 8px;
    right: 8px;
    bottom: max(8px, env(safe-area-inset-bottom));
    z-index: 50;
    padding: 4px 3px;
    border-radius: 20px;
    gap: 1px;
  }
  .dock-item {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    min-height: 44px;
    padding: 3px 1px;
    border-radius: 14px;
    color: var(--ink-secondary);
    font-size: 9.5px;
    font-weight: 560;
    white-space: nowrap;
    transition: background 0.18s, color 0.18s;
  }
  .dock-item :deep(svg) {
    width: 16px;
    height: 16px;
  }
  .dock-item.router-link-exact-active {
    background: var(--accent-soft);
    color: var(--accent);
    font-weight: 650;
  }
  .studio-toast {
    bottom: calc(68px + env(safe-area-inset-bottom));
  }
}
</style>
