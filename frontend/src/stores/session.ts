import { computed, ref, watchEffect } from 'vue'
import { configureApiAuth } from '@/api/client'
import { DEFAULT_PREFERENCES } from '@/constants/theme'
import type { Preferences, Session } from '@/types'

export const session = ref<Session | null>(null)
export const preferences = computed(() => session.value?.preferences ?? DEFAULT_PREFERENCES)
export const today = ref('')
export const todayFocusSeconds = ref(0)
export const learningRevision = ref(0)
export const sessionEpoch = ref(0)

const preferredDark = window.matchMedia('(prefers-color-scheme: dark)')
const osDark = ref(preferredDark.matches)
preferredDark.addEventListener('change', event => {
  osDark.value = event.matches
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

export function setSession(value: Session) {
  if (session.value?.csrf !== value.csrf) {
    sessionEpoch.value++
  }
  session.value = value
  today.value = value.today
}

export function clearSession() {
  sessionEpoch.value++
  session.value = null
  todayFocusSeconds.value = 0
}

export function updatePreferences(value: Preferences) {
  if (session.value) session.value.preferences = value
}

export function bumpLearningRevision() {
  learningRevision.value++
}

configureApiAuth({
  getCsrf: () => session.value?.csrf,
  onUnauthorized: csrf => {
    if (session.value?.csrf === csrf) clearSession()
  },
})
