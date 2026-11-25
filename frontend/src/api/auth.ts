import type { ChangePasswordPayload, LoginPayload, Session } from '@/types'
import { api } from './client'

export const fetchStatus = () => api<{ initialized: boolean }>('/status')

export const fetchMe = () => api<Session>('/auth/me')

export const loginApi = (payload: LoginPayload) => api<Session>('/auth/login', 'POST', payload)

export const logoutApi = () => api<{ ok: boolean }>('/auth/logout', 'POST')

export const changePasswordApi = (payload: ChangePasswordPayload) => api<Session>('/auth/password', 'POST', payload)
