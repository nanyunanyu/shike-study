import type { Palette } from './common'
import type { Review } from './study'

export interface CalendarDay {
  date: string
  completed: number | null
  total: number | null
  rate: number | null
  seconds: number | null
  checked: boolean
}

export interface CategoryStat {
  id: string
  name: string
  completed: number
  total: number
  rate: number | null
  seconds: number
}

export interface Achievement {
  id: string
  title: string
  description: string
  icon: string
  unlocked: boolean
  progress: number
  target: number
  unit: string
}

export interface MilestonePayload {
  title: string
  target_date: string
  note: string
  color: Palette
  pinned: boolean
}

export interface MilestoneUpdatePayload extends MilestonePayload {
  completed: boolean
}

export interface Milestone extends MilestoneUpdatePayload {
  id: string
  created_at: number
  days_left: number
}

export interface CustomRangeReport {
  start: string
  end: string
  days: CalendarDay[]
  previous_seconds: number
  has_previous: boolean
}

export interface Statistics {
  today: string
  streak: number
  longest_streak: number
  checkins: number
  seconds: number
  today_focus_seconds: number
  daily_focus_goal_minutes: number
  reviews_count: number
  calendar: CalendarDay[]
  categories: CategoryStat[]
  achievements: Achievement[]
  pinned_milestones: Milestone[]
  custom_range?: CustomRangeReport | null
}

export interface ReviewTimelineItem {
  date: string
  checked_at: number | null
  completed: number
  total: number
  rate: number | null
  focus_seconds: number
  review: Review
}

export interface ReviewTimelinePage {
  items: ReviewTimelineItem[]
  next_before: string | null
  summary: {
    total_reviews: number
    avg_focus_score: number | null
    mood_counts: Record<string, number>
  }
}

export interface BackupCounts {
  plans: number
  days: number
  focus: number
  categories: number
  milestones?: number
}
