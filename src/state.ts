import { computed, reactive, ref, shallowRef, watchEffect } from 'vue'
import type { Day, Mode, Mood, Palette, Preferences, Session, Timer, TimerAction, TimerResponse } from './types'

export const defaults: Preferences = {
  focus_minutes: 25,
  break_minutes: 5,
  countdown_minutes: 30,
  auto_break: false,
  daily_focus_goal_minutes: 180,
  appearance: 'light',
  palette: 'blue',
}

export const PALETTES: ReadonlyArray<{ id: Palette; label: string; desc: string; swatch: string; swatch2: string }> = [
  { id: 'blue', label: '晴空蓝', desc: '澄澈克制', swatch: '#2563eb', swatch2: '#0ea5e9' },
  { id: 'mint', label: '青岚翠', desc: '清朗自然', swatch: '#0d9488', swatch2: '#10b981' },
  { id: 'lilac', label: '暮雾紫', desc: '雅致静谧', swatch: '#7c3aed', swatch2: '#a855f7' },
  { id: 'amber', label: '暖砂金', desc: '温润书香', swatch: '#c26d18', swatch2: '#f59e0b' },
  { id: 'rose', label: '晨樱绯', desc: '轻盈柔和', swatch: '#e11d48', swatch2: '#f43f5e' },
]

export const MOODS: ReadonlyArray<{ id: Mood; label: string; short: string; glyph: string; tone: string }> = [
  { id: 'great', label: '状态极佳', short: '极佳', glyph: '✦', tone: '#0ea5e9' },
  { id: 'good', label: '充实顺畅', short: '充实', glyph: '◉', tone: '#10b981' },
  { id: 'neutral', label: '平稳推进', short: '平稳', glyph: '○', tone: '#64748b' },
  { id: 'tired', label: '略感疲惫', short: '疲惫', glyph: '◐', tone: '#f59e0b' },
  { id: 'stressed', label: '有些焦虑', short: '焦虑', glyph: '△', tone: '#f43f5e' },
]

export const REVIEW_ISSUES = ['走神', '网课吸收不足', '错题未消化', '背诵不牢', '拖延', '其他'] as const

export const session = ref<Session | null>(null)
export const preferences = computed(() => session.value?.preferences ?? defaults)
export const today = ref('')
export const todayFocusSeconds = ref(0)
export const timer = shallowRef<Timer | null>(null)
export const clock = ref(0)
export const timerReady = ref(false)
export const timerBusy = ref(false)
export const focusCompletion = ref<string | null>(null)
export const learningRevision = ref(0)
export const toast = reactive({ message: '', error: false, version: 0 })
export const notify = (message: string, error = false) =>
  Object.assign(toast, { message, error, version: toast.version + 1 })

let lastServerTime = 0
let syncedAt = 0
let epoch = 0
let reading = false
let timerWriteVersion = 0
let pendingStart: { signature: string; id: string } | null = null
let observedFocus: { id: string; end: number } | null = null
let observationVersion = 0
const completionWindow = 10

const preferredDark = window.matchMedia('(prefers-color-scheme: dark)')
const osDark = ref(preferredDark.matches)
preferredDark.addEventListener('change', e => {
  osDark.value = e.matches
})

export const dark = computed(
  () => preferences.value.appearance === 'dark' || (preferences.value.appearance === 'system' && osDark.value),
)

watchEffect(() => {
  document.documentElement.dataset.appearance = dark.value ? 'dark' : 'light'
  document.documentElement.dataset.palette = preferences.value.palette
  document.documentElement.style.colorScheme = dark.value ? 'dark' : 'light'
  const meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')
  if (meta) meta.content = dark.value ? '#0b0e14' : '#f4f6fa'
})

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
  }
}

export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET' && session.value) headers['X-CSRF-Token'] = session.value.csrf
  const { csrf } = session.value ?? {}
  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: 'no-store',
    })
  } catch {
    throw new ApiError('无法连接本机服务，请稍后重试', 0)
  }
  if (!response.ok) {
    const result = await response.json().catch(() => ({}))
    if (response.status === 401 && csrf && session.value?.csrf === csrf) clearSession()
    throw new ApiError(typeof result.detail === 'string' ? result.detail : '请求未完成，请重试', response.status)
  }
  return response.json()
}

export function setSession(value: Session) {
  if (session.value?.csrf !== value.csrf) {
    epoch++
    timer.value = null
    timerReady.value = false
    pendingStart = null
    focusCompletion.value = null
    resetFocusObservation()
  }
  session.value = value
  today.value = value.today
}

export function clearSession() {
  epoch++
  session.value = null
  timer.value = null
  timerReady.value = false
  timerBusy.value = false
  pendingStart = null
  focusCompletion.value = null
  todayFocusSeconds.value = 0
  resetFocusObservation()
}

export function updatePreferences(value: Preferences) {
  if (session.value) session.value.preferences = value
}

export function resetFocusObservation() {
  observedFocus = null
  observationVersion++
}

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
    void api<Day>(`/days/${previous.date}`)
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
    learningRevision.value++
  }
  if (today.value && result.today !== today.value) learningRevision.value++
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

export const timerModeLabels: Record<Mode, string> = {
  pomodoro: '番茄钟',
  stopwatch: '正计时',
  countdown: '倒计时',
}

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
  const generation = epoch
  const version = timerWriteVersion
  try {
    const result = await api<TimerResponse>('/timer')
    if (epoch === generation && version === timerWriteVersion && !timerBusy.value) updateTimer(result)
  } catch {
    /* retry on next poll */
  } finally {
    reading = false
  }
}

let expiryAttempt = 0
export function tickClock() {
  if (!timerReady.value) return
  clock.value = lastServerTime + Math.floor((performance.now() - syncedAt) / 1000)
  const item = timer.value
  if (item?.running_since != null && item.duration != null && timerSeconds.value === 0 && performance.now() >= expiryAttempt) {
    expiryAttempt = performance.now() + 1000
    void syncTimer()
  }
}

async function sendTimer(path: string, body: unknown) {
  if (timerBusy.value) return false
  timerWriteVersion++
  timerBusy.value = true
  const generation = epoch
  try {
    const result = await api<TimerResponse>(path, 'POST', body)
    if (epoch !== generation) return false
    updateTimer(result)
    return true
  } catch (error) {
    notify((error as Error).message, true)
    return false
  } finally {
    if (epoch === generation) {
      timerBusy.value = false
      void syncTimer()
    }
  }
}

export async function startTimer(mode: Mode, task: string | null, minutes?: number) {
  const signature = JSON.stringify([today.value, mode, task, minutes])
  if (pendingStart?.signature !== signature) pendingStart = { signature, id: crypto.randomUUID() }
  if (await sendTimer('/timer/start', { id: pendingStart.id, date: today.value, mode, task_id: task, minutes })) {
    pendingStart = null
  }
}

export function actTimer(action: TimerAction) {
  if (!timer.value) return Promise.resolve(false)
  const { id, revision } = timer.value
  return sendTimer('/timer/action', { id, revision, action })
}

export async function finishTimer() {
  const item = timer.value
  if ((await actTimer('finish')) && item?.stage === 'focus' && focusCompletion.value !== item.id) {
    notify('专注已记录')
  }
}

export function duration(seconds: number) {
  if (!seconds) return '0 分钟'
  if (seconds < 60) return `${seconds} 秒`
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor(seconds / 60) % 60
  return [hours && `${hours} 小时`, minutes && `${minutes} 分钟`].filter(Boolean).join(' ')
}

export function timerText(seconds: number) {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor(seconds / 60) % 60
  return [...(hours > 0 ? [hours] : []), minutes, seconds % 60]
    .map(n => String(n).padStart(2, '0'))
    .join(':')
}

export function shiftDate(value: string, offset: number) {
  const date = new Date(`${value}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + offset)
  return date.toISOString().slice(0, 10)
}

export function labelDate(value: string, style: 'long' | 'short' = 'long') {
  return !value
    ? ''
    : new Intl.DateTimeFormat('zh-CN', {
        month: 'long',
        day: 'numeric',
        ...(style === 'long' ? { weekday: 'long' } : {}),
        timeZone: 'UTC',
      }).format(new Date(`${value}T00:00:00Z`))
}

export function greetingForHour(hour: number) {
  if (hour < 6) return '夜深静学'
  if (hour < 11) return '早安，开启澄澈一日'
  if (hour < 14) return '午安，保持平稳节奏'
  if (hour < 18) return '下午好，沉浸专注此刻'
  return '晚安，收获今日沉淀'
}

export function currentHHMM(timezone?: string): string {
  const now = new Date()
  try {
    const parts = new Intl.DateTimeFormat('en-GB', {
      timeZone: timezone || 'Asia/Shanghai',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).formatToParts(now)
    const h = parts.find(p => p.type === 'hour')?.value ?? '09'
    const m = parts.find(p => p.type === 'minute')?.value ?? '00'
    return `${h === '24' ? '00' : h}:${m}`
  } catch {
    return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  }
}
