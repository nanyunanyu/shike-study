import type { MessageKind, User } from './types'

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

export const dispatchTabs = [
  { id: 'pending', label: '待发送' },
  { id: 'sent', label: '已发送' },
  { id: 'canceled', label: '已取消' },
] as const
