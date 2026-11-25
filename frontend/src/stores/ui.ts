import { reactive, ref } from 'vue'
import {
  chooseCheckInScene,
  resolveStreakMilestone,
  type CelebrationOrigin,
  type CheckInScene,
} from '@/utils/celebrationEngine'

export const toast = reactive({ message: '', error: false, version: 0 })

export const notify = (message: string, error = false) =>
  Object.assign(toast, { message, error, version: toast.version + 1 })

export const activeDialogs = ref(0)

export interface CheckInCelebrationState {
  id: number
  active: boolean
  scene: CheckInScene
  origin: CelebrationOrigin
  streak: number
  milestoneTitle: string | null
}

export const checkInCelebration = reactive<CheckInCelebrationState>({
  id: 0,
  active: false,
  scene: 'chronos-bloom',
  origin: { x: 0, y: 0 },
  streak: 1,
  milestoneTitle: null,
})

export function triggerCheckInCelebration(payload: {
  origin: CelebrationOrigin
  streak: number
  scene?: CheckInScene
}) {
  const streak = Math.max(1, Math.round(payload.streak || 1))
  checkInCelebration.id += 1
  checkInCelebration.scene = payload.scene ?? chooseCheckInScene()
  checkInCelebration.origin = payload.origin
  checkInCelebration.streak = streak
  checkInCelebration.milestoneTitle = resolveStreakMilestone(streak)
  checkInCelebration.active = true
}

export function updateCheckInCelebrationStreak(streak: number) {
  if (!checkInCelebration.active || streak <= 0) return
  checkInCelebration.streak = streak
  checkInCelebration.milestoneTitle = resolveStreakMilestone(streak)
}

export function clearCheckInCelebration(expectedId?: number) {
  if (expectedId !== undefined && checkInCelebration.id !== expectedId) return
  checkInCelebration.active = false
}
