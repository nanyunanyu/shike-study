import type { Mode } from './common'
import type { FocusTask } from './study'

export interface Timer {
  id: string
  date: string
  revision: number
  mode: Mode
  stage: 'focus' | 'break' | 'offer'
  task: FocusTask | null
  elapsed: number
  running_since: number | null
  started_at: number
  duration: number | null
  auto_break: boolean
  break_seconds: number
}

export interface TimerResponse {
  timer: Timer | null
  now: number
  today: string
}

export type TimerAction = 'pause' | 'resume' | 'finish' | 'start_break' | 'dismiss'

export interface TimerStartPayload {
  id: string
  date: string
  mode: Mode
  task_id: string | null
  minutes?: number
}

export interface TimerActionPayload {
  id: string
  revision: number
  action: TimerAction
}
