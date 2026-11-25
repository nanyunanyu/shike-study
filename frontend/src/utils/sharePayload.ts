import type { Day, Review, ReviewTimelineItem } from '@/types'
import type { ShareCardPayload } from './shareCard'

export type ShareCardBasePayload = Omit<ShareCardPayload, 'palette' | 'dark'>

export function buildSharePayloadFromDay(params: {
  day: Day
  username: string
  goalMinutes: number
  streak: number
  review?: Review | null
}): ShareCardBasePayload {
  const { day, username, goalMinutes, streak, review } = params
  const activeReview = review ?? day.review
  return {
    date: day.date,
    username,
    completed: day.tasks.filter(t => t.done).length,
    total: day.tasks.length,
    focusSeconds: day.focus_seconds,
    goalMinutes,
    streak,
    checked: !!day.checked_at,
    mood: activeReview.mood,
    focusScore: activeReview.focus_score,
    takeaways: activeReview.effective,
    reflection: activeReview.reflection || activeReview.adjustment || day.review.reflection,
  }
}

export function buildSharePayloadFromReview(params: {
  entry: ReviewTimelineItem
  username: string
  goalMinutes: number
  streak: number
}): ShareCardBasePayload {
  const { entry, username, goalMinutes, streak } = params
  return {
    date: entry.date,
    username,
    completed: entry.completed,
    total: entry.total,
    focusSeconds: entry.focus_seconds,
    goalMinutes,
    streak,
    checked: !!entry.checked_at,
    mood: entry.review.mood,
    focusScore: entry.review.focus_score,
    takeaways: entry.review.effective,
    reflection: entry.review.reflection || entry.review.adjustment,
  }
}
