import type { TimerActionPayload, TimerResponse, TimerStartPayload } from '@/types'
import { api } from './client'

export const fetchTimerApi = () => api<TimerResponse>('/timer')

export const postTimerStartApi = (payload: TimerStartPayload) => api<TimerResponse>('/timer/start', 'POST', payload)

export const postTimerActionApi = (payload: TimerActionPayload) => api<TimerResponse>('/timer/action', 'POST', payload)
