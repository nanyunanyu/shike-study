import type {
  AdminOverview,
  CreateAdminUserPayload,
  Day,
  DispatchDetail,
  DispatchPage,
  DispatchStatus,
  MessageKind,
  NewDispatchPayload,
  Plan,
  ResetAdminPasswordPayload,
  Statistics,
  User,
} from '@/types'
import { api } from './client'

export const fetchAdminOverview = () => api<AdminOverview>('/admin/overview')

export const createAdminUserApi = (payload: CreateAdminUserPayload) => api<User>('/admin/users', 'POST', payload)

export const resetAdminUserPasswordApi = (uid: number, payload: ResetAdminPasswordPayload) =>
  api<User>(`/admin/users/${uid}/password`, 'PUT', payload)

export const setAdminUserActiveApi = (uid: number, active: boolean) =>
  api<User>(`/admin/users/${uid}/active`, 'PUT', { active })

export const deleteAdminUserApi = (uid: number) => api<{ ok: boolean }>(`/admin/users/${uid}`, 'DELETE')

export const inspectUserDayApi = (uid: number, day: string) => api<Day>(`/admin/users/${uid}/day/${day}`)

export const inspectUserPlanApi = (uid: number) => api<Plan>(`/admin/users/${uid}/plan`)

export function inspectUserStatisticsApi(uid: number, range?: { start: string; end: string }) {
  if (!range) return api<Statistics>(`/admin/users/${uid}/statistics`)
  const params = new URLSearchParams({ start: range.start, end: range.end })
  return api<Statistics>(`/admin/users/${uid}/statistics?${params}`)
}

export interface AdminDispatchesQuery {
  status: DispatchStatus
  kind?: MessageKind | ''
  recipientId?: string
  cursor?: string | null
}

export function fetchAdminDispatchesApi(params: AdminDispatchesQuery) {
  const query = new URLSearchParams({ status: params.status })
  if (params.kind) query.set('kind', params.kind)
  if (params.recipientId) query.set('recipient_id', params.recipientId)
  if (params.cursor) query.set('cursor', params.cursor)
  return api<DispatchPage>(`/admin/dispatches?${query}`)
}

export const fetchAdminDispatchDetailApi = (key: string) =>
  api<DispatchDetail>(`/admin/dispatches/${encodeURIComponent(key)}`)

export const createAdminDispatchApi = (payload: NewDispatchPayload) =>
  api<{ key: string | null }>('/admin/dispatches', 'POST', payload)

export const cancelAdminDispatchApi = (key: string) =>
  api<{ ok: boolean }>(`/admin/dispatches/${encodeURIComponent(key)}`, 'DELETE')

export const cancelAdminUserMessageApi = (uid: number, messageId: number) =>
  api<{ ok: boolean }>(`/admin/users/${uid}/messages/${messageId}`, 'DELETE')
