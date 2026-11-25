import type { Appearance, Palette } from './common'

export interface User {
  id: number
  username: string
  role: 'admin' | 'user'
  active: boolean
  must_change: boolean
}

export interface Preferences {
  focus_minutes: number
  break_minutes: number
  countdown_minutes: number
  auto_break: boolean
  daily_focus_goal_minutes: number
  appearance: Appearance
  palette: Palette
}

export interface Session {
  user: User
  csrf: string
  today: string
  timezone: string
  preferences: Preferences
}

export interface LoginPayload {
  username: string
  password: string
}

export interface ChangePasswordPayload {
  current: string
  password: string
}
