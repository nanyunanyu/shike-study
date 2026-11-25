<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  BookMarked,
  CalendarDays,
  ChartNoAxesCombined,
  CircleUserRound,
  ListChecks,
  ShieldCheck,
  Timer as TimerIcon,
} from 'lucide-vue-next'
import { fetchMe, fetchStatus } from '@/api/auth'
import { ApiError } from '@/api/client'
import AuthGate from '@/components/auth/AuthGate.vue'
import AppSidebar, { type NavItem } from '@/components/layout/AppSidebar.vue'
import CheckInCelebration from '@/components/layout/CheckInCelebration.vue'
import MobileDock from '@/components/layout/MobileDock.vue'
import MobileTopBar from '@/components/layout/MobileTopBar.vue'
import StudioToast from '@/components/layout/StudioToast.vue'
import MessageCenter from '@/components/messages/MessageCenter.vue'
import FloatingClock from '@/components/timer/FloatingClock.vue'
import PageSkeleton from '@/components/ui/PageSkeleton.vue'
import { session, setSession } from '@/stores/session'
import { floatingClockOpen, focusCompletion, resetFocusObservation, syncTimer, tickClock } from '@/stores/timer'
import { notify, toast } from '@/stores/ui'
import { playCompletionChime } from '@/utils/soundscape'

const router = useRouter()
const route = useRoute()

const checking = ref(true)
const initialized = ref(true)
const startupProblem = ref('')
const mobileTopBar = ref<InstanceType<typeof MobileTopBar> | null>(null)
const mobileDock = ref<InstanceType<typeof MobileDock> | null>(null)
const messages = ref<InstanceType<typeof MessageCenter> | null>(null)
const toastRef = ref<InstanceType<typeof StudioToast> | null>(null)

const unread = computed(() => messages.value?.unread ?? 0)
const clockAccount = computed(() => (session.value ? `${session.value.user.id}:${session.value.user.username}` : ''))

const navItems = computed<NavItem[]>(() => [
  { name: 'today', label: '今日', icon: CalendarDays },
  { name: 'timer', label: '专注', icon: TimerIcon },
  { name: 'plan', label: '计划', icon: ListChecks },
  { name: 'reviews', label: '复盘', icon: BookMarked },
  { name: 'stats', label: '统计', icon: ChartNoAxesCombined },
  { name: 'me', label: '我的', icon: CircleUserRound },
  ...(session.value?.user.role === 'admin' ? [{ name: 'admin', label: '后台', icon: ShieldCheck }] : []),
])

let clockInterval = 0
let syncInterval = 0
let completionToast = -1

watch(focusCompletion, id => {
  if (id) {
    playCompletionChime()
    if (!floatingClockOpen.value || route.name === 'timer') {
      notify('本轮专注已完成，已自动记入专注统计')
      completionToast = toast.version
    }
  }
})

watch(floatingClockOpen, open => {
  if (open && completionToast === toast.version) toastRef.value?.hide()
})

watch(
  () => route.name,
  name => {
    if (name === 'timer') floatingClockOpen.value = false
  },
)

watch([session, () => route.meta.requiresAdmin], () => {
  if (session.value && session.value.user.role !== 'admin' && route.meta.requiresAdmin) {
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
      setSession(await fetchMe())
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 401)) throw error
      initialized.value = (await fetchStatus()).initialized
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
    <AppSidebar :nav-items="navItems" :unread="unread" @open-inbox="messages?.showInbox()" />

    <MobileTopBar ref="mobileTopBar" :unread="unread" @open-inbox="messages?.showInbox()" />

    <main id="main-content" class="studio-main" tabindex="-1">
      <RouterView v-slot="{ Component, route: current }">
        <Transition name="page-fade" mode="out-in">
          <component
            :is="Component"
            :key="current.name"
            v-if="!current.meta.requiresAdmin || session.user.role === 'admin'"
          />
        </Transition>
      </RouterView>
    </main>

    <MobileDock ref="mobileDock" :nav-items="navItems" />

    <FloatingClock
      v-if="route.name !== 'timer'"
      :key="clockAccount"
      :account="clockAccount"
      :top-bar="mobileTopBar?.el ?? null"
      :bottom-nav="mobileDock?.el ?? null"
    />

    <MessageCenter
      v-if="session.user.role === 'user'"
      ref="messages"
      :key="session.csrf"
      :timezone="session.timezone"
      :clock-open="floatingClockOpen"
    />
  </div>

  <CheckInCelebration />
  <StudioToast ref="toastRef" />
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
.studio-main {
  min-width: 0;
  margin-left: var(--sidebar-offset);
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
  .studio-main {
    margin-left: 0;
  }
}
</style>
