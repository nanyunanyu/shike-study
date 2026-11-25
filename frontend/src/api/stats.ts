import type {
  Milestone,
  MilestonePayload,
  MilestoneUpdatePayload,
  Mood,
  ReviewTimelinePage,
  Statistics,
} from '@/types'
import { api } from './client'

export interface StatisticsRangeQuery {
  start: string
  end: string
}

export function fetchStatistics(range?: StatisticsRangeQuery) {
  if (!range) return api<Statistics>('/statistics')
  const params = new URLSearchParams({ start: range.start, end: range.end })
  return api<Statistics>(`/statistics?${params}`)
}

export interface ReviewsQuery {
  mood?: Mood | ''
  issue?: string
  q?: string
  before?: string | null
  limit?: number
}

export function fetchReviewsTimeline(query: ReviewsQuery = {}) {
  const params = new URLSearchParams({ limit: String(query.limit ?? 20) })
  if (query.mood) params.set('mood', query.mood)
  if (query.issue) params.set('issue', query.issue)
  if (query.q?.trim()) params.set('q', query.q.trim())
  if (query.before) params.set('before', query.before)
  return api<ReviewTimelinePage>(`/reviews?${params}`)
}

export const fetchMilestones = () => api<Milestone[]>('/milestones')

export const createMilestoneApi = (payload: MilestonePayload) => api<Milestone>('/milestones', 'POST', payload)

export const updateMilestoneApi = (id: string, payload: MilestoneUpdatePayload) =>
  api<Milestone>(`/milestones/${id}`, 'PUT', payload)

export const deleteMilestoneApi = (id: string) => api<{ ok: boolean }>(`/milestones/${id}`, 'DELETE')
