import type { MessageKind } from './common'

export interface MessageStatus {
  unread: number
  pending: boolean
}

export interface MessageContent {
  id: number
  sender: string
  kind: MessageKind
  body: string
  created_at: number
  due_at: number
}

export interface InboxMessage extends MessageContent {
  read_at: number | null
}

export interface InboxPage {
  items: InboxMessage[]
  next_before: number | null
}

export interface MessagePreview {
  message: InboxMessage
  more: number
}
