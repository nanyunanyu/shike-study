import type { User } from './auth'
import type { MessageKind } from './common'

export interface AdminAccount extends User {
  last_checkin_date: string | null
  checked_today: boolean
}

export interface AdminTrendDay {
  date: string
  checked: number
  focus_seconds: number
}

export interface AdminOverview {
  date: string
  active_accounts: number
  checked_today: number
  focus_seconds: number
  pending_dispatches: number
  trend: AdminTrendDay[]
  accounts: AdminAccount[]
}

export type DispatchStatus = 'pending' | 'sent' | 'canceled'

export interface Dispatch {
  key: string
  kind: MessageKind
  body: string
  created_at: number
  due_at: number
  recipient_count: number
  pending: number
  sent: number
  canceled: number
  read: number
}

export interface DispatchRecipient {
  message_id: number
  id: number
  username: string
  read_at: number | null
  canceled_at: number | null
}

export interface DispatchDetail extends Dispatch {
  recipients: DispatchRecipient[]
}

export interface DispatchPage {
  items: Dispatch[]
  next_cursor: string | null
}

export interface NewDispatchPayload {
  request_id: string
  recipient_ids: number[]
  kind: MessageKind
  body: string
  scheduled_for: string | null
  all_active: boolean
}

export interface CreateAdminUserPayload {
  username: string
  password: string
  must_change: boolean
}

export interface ResetAdminPasswordPayload {
  password: string
  must_change: boolean
}
