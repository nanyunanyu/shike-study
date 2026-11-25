import type { InboxMessage, InboxPage, MessagePreview, MessageStatus } from '@/types'
import { api } from './client'

export const fetchMessageStatusApi = () => api<MessageStatus>('/messages/status')

export const claimMessagePreviewApi = () => api<MessagePreview | null>('/messages/preview', 'POST')

export const fetchInboxApi = (before?: number | null) => api<InboxPage>(`/messages${before ? `?before=${before}` : ''}`)

export const markMessageReadApi = (messageId: number) => api<InboxMessage>(`/messages/${messageId}/read`, 'PUT')

export const deleteInboxMessageApi = (messageId: number) => api<{ ok: boolean }>(`/messages/${messageId}`, 'DELETE')
