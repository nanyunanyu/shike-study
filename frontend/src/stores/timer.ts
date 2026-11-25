import { computed, ref, shallowRef, watch } from 'vue'
import { fetchDay } from '@/api/days'
import { fetchTimerApi, postTimerActionApi, postTimerStartApi } from '@/api/timer'
import { bumpLearningRevision, session, sessionEpoch, today } from '@/stores/session'
import { notify } from '@/stores/ui'
import type { Mode, Timer, TimerAction, TimerResponse } from '@/types'

export const timer = shallowRef<Timer | null>(null)
export const clock = ref(0)
export const timerReady = ref(false)
export const timerBusy = ref(false)
export const focusCompletion = ref<string | null>(null)

let lastServerTime = 0
let syncedAt = 0
let reading = false
let timerWriteVersion = 0
let pendingStart: { signature: string; id: string } | null = null
let observedFocus: { id: string; end: number } | null = null
let observationVersion = 0
let expiryAttempt = 0
const completionWindow = 10

export function resetFocusObservation() {
  observedFocus = null
  observationVersion++
}

watch(
  sessionEpoch,
  () => {
    timer.value = null
    timerReady.value = false
    timerBusy.value = false
    pendingStart = null
    focusCompletion.value = null
    resetFocusObservation()
  },
  { flush: 'sync' },
)

function observeFocus(result: TimerResponse, previous: Timer | null) {
  const item = result.timer
  const tracked = observedFocus
  const end =
    item?.stage === 'focus' && item.running_since !== null && item.duration !== null
      ? item.running_since + item.duration - item.elapsed
      : null
  observedFocus = !document.hidden && item && end !== null && end > result.now ? { id: item.id, end } : null
  if (document.hidden || !tracked || previous?.stage !== 'focus' || previous.id !== tracked.id) return
  if (
    (item?.id === tracked.id && item.stage === 'focus') ||
    result.now < tracked.end ||
    result.now > tracked.end + completionWindow
  ) {
    return
  }

  const version = observationVersion
  const received = performance.now()
  function celebrate(id: string) {
    if (
      version !== observationVersion ||
      document.hidden ||
      focusCompletion.value === id ||
      performance.now() - received > completionWindow * 1000
    ) {
      return
    }
    focusCompletion.value = id
  }

  if (previous.mode === 'pomodoro' && item?.id === tracked.id && (item.stage === 'offer' || item.stage === 'break')) {
    celebrate(tracked.id)
  } else if (previous.mode === 'countdown') {
    void fetchDay(previous.date)
      .then(day => {
        if (
          day.focus.some(
            entry =>
              entry.id === tracked.id &&
              entry.mode === 'countdown' &&
              entry.ended_at === tracked.end &&
              entry.seconds === previous.duration,
          )
        ) {
          celebrate(tracked.id)
        }
      })
      .catch(() => {})
  }
}

function updateTimer(result: TimerResponse) {
  const previous = timer.value
  if (previous?.stage === 'focus' && (result.timer?.stage !== 'focus' || result.timer.id !== previous.id)) {
    bumpLearningRevision()
  }
  if (today.value && result.today !== today.value) bumpLearningRevision()
  today.value = result.today
  timer.value = result.timer
  timerReady.value = true
  lastServerTime = result.now
  syncedAt = performance.now()
  clock.value = result.now
  observeFocus(result, previous)
}

export const timerElapsed = computed(() =>
  timer.value
    ? timer.value.elapsed + (timer.value.running_since === null ? 0 : Math.max(0, clock.value - timer.value.running_since))
    : 0,
)

export const timerSeconds = computed(() =>
  timer.value?.duration != null ? Math.max(0, timer.value.duration - timerElapsed.value) : timerElapsed.value,
)

export const timerProgress = computed(() => {
  const item = timer.value
  if (item?.stage === 'offer') return 1
  return item?.duration && item.duration > 0 ? Math.min(1, Math.max(0, timerElapsed.value / item.duration)) : null
})

export const timerStatus = computed(() => {
  const item = timer.value
  if (!item) return timerReady.value ? '准备专注' : '正在同步'
  if (item.stage === 'offer') return '本轮已完成'
  if (item.stage === 'break') return item.running_since === null ? '休息已暂停' : '轻松休息中'
  return item.running_since === null ? '已暂停' : '深度专注中'
})

export async function syncTimer() {
  if (!session.value || session.value.user.must_change || reading || timerBusy.value) return
  reading = true
  const generation = sessionEpoch.value
  const version = timerWriteVersion
  try {
    const result = await fetchTimerApi()
    if (sessionEpoch.value === generation && version === timerWriteVersion && !timerBusy.value) updateTimer(result)
  } catch {
    /* retry on next poll */
  } finally {
    reading = false
  }
}

export function tickClock() {
  if (!timerReady.value) return
  clock.value = lastServerTime + Math.floor((performance.now() - syncedAt) / 1000)
  const item = timer.value
  if (item?.running_since != null && item.duration != null && timerSeconds.value === 0 && performance.now() >= expiryAttempt) {
    expiryAttempt = performance.now() + 1000
    void syncTimer()
  }
}

async function runTimerMutation(request: () => Promise<TimerResponse>) {
  if (timerBusy.value) return false
  timerWriteVersion++
  timerBusy.value = true
  const generation = sessionEpoch.value
  try {
    const result = await request()
    if (sessionEpoch.value !== generation) return false
    updateTimer(result)
    return true
  } catch (error) {
    notify((error as Error).message, true)
    return false
  } finally {
    if (sessionEpoch.value === generation) {
      timerBusy.value = false
      void syncTimer()
    }
  }
}

export async function startTimer(mode: Mode, task: string | null, minutes?: number) {
  const signature = JSON.stringify([today.value, mode, task, minutes])
  if (pendingStart?.signature !== signature) pendingStart = { signature, id: crypto.randomUUID() }
  const id = pendingStart.id
  if (await runTimerMutation(() => postTimerStartApi({ id, date: today.value, mode, task_id: task, minutes }))) {
    pendingStart = null
  }
}

export function actTimer(action: TimerAction) {
  if (!timer.value) return Promise.resolve(false)
  const { id, revision } = timer.value
  return runTimerMutation(() => postTimerActionApi({ id, revision, action }))
}

export async function finishTimer() {
  const item = timer.value
  if ((await actTimer('finish')) && item?.stage === 'focus' && focusCompletion.value !== item.id) {
    notify('专注已记录')
  }
}
