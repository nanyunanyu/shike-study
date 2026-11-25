import type { AdhocTaskPayload, Day, Review, Times } from '@/types'
import { api } from './client'

export const fetchDay = (day: string) => api<Day>(`/days/${day}`)

export const toggleTaskDoneApi = (day: string, taskId: string, done: boolean) =>
  api<Day>(`/days/${day}/tasks/${taskId}/done`, 'PUT', { done })

export const updateTaskTimesApi = (day: string, taskId: string, times: Times | null) =>
  api<Day>(`/days/${day}/tasks/${taskId}/times`, 'PUT', times)

export const addAdhocTaskApi = (day: string, payload: AdhocTaskPayload) => api<Day>(`/days/${day}/tasks`, 'POST', payload)

export const updateAdhocTaskApi = (day: string, taskId: string, payload: AdhocTaskPayload) =>
  api<Day>(`/days/${day}/tasks/${taskId}`, 'PUT', payload)

export const deleteAdhocTaskApi = (day: string, taskId: string) => api<Day>(`/days/${day}/tasks/${taskId}`, 'DELETE')

export const saveDayReviewApi = (day: string, review: Review) => api<Day>(`/days/${day}/review`, 'PUT', review)

export const checkInDayApi = (day: string) => api<Day>(`/days/${day}/check-in`, 'POST')

export const undoCheckInDayApi = (day: string) => api<Day>(`/days/${day}/check-in`, 'DELETE')
