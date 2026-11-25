export type Palette = 'blue' | 'mint' | 'lilac' | 'amber' | 'rose'
export type Appearance = 'light' | 'dark' | 'system'
export type Mood = 'great' | 'good' | 'neutral' | 'tired' | 'stressed'
export type Mode = 'pomodoro' | 'stopwatch' | 'countdown'
export type MessageKind = 'reminder' | 'encouragement'

export interface User {
  id: number
  username: string
  role: 'admin' | 'user'
  active: boolean
  must_change: boolean
}

export interface Preferences {
  focus_minutes: number
  break_minutes: number
  countdown_minutes: number
  auto_break: boolean
  daily_focus_goal_minutes: number
  appearance: Appearance
  palette: Palette
}

export interface Session {
  user: User
  csrf: string
  today: string
  timezone: string
  preferences: Preferences
}

export interface Times {
  start: string
  end: string | null
}

export interface Task extends Times {
  id: string
  title: string
  category: string
  note: string
  estimate: number | null
}

export interface Snapshot extends Task {
  category_name: string
}

export interface DayTask extends Snapshot {
  done: boolean
  override: Times | null
  adhoc?: boolean
}

export interface Review {
  effective: string[]
  issues: string[]
  other: string
  priorities: string[]
  adjustment: string
  mood: Mood | null
  focus_score: number | null
  reflection: string
}

export interface FocusTask {
  id: string
  title: string
  category: string
  category_name: string
}

export interface Focus {
  id: string
  date: string
  started_at: number
  ended_at: number
  seconds: number
  mode: Mode
  task: FocusTask | null
}

export interface Day {
  date: string
  today: string
  exists: boolean
  editable: boolean
  tasks: DayTask[]
  review: Review
  checked_at: number | null
  focus: Focus[]
  focus_seconds: number
}

export interface Category {
  id: string
  name: string
  archived: boolean
  builtin: boolean
}

export interface PlanVersion {
  id: string
  date: string
  created_at: number
}

export interface Plan {
  current: PlanVersion & { tasks: Snapshot[] }
  categories: Category[]
  defaults: Snapshot[]
  history: PlanVersion[]
}

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

export interface Milestone {
  id: string
  title: string
  target_date: string
  note: string
  color: Palette
  pinned: boolean
  completed: boolean
  created_at: number
  days_left: number
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

export interface Timer {
  id: string
  date: string
  revision: number
  mode: Mode
  stage: 'focus' | 'break' | 'offer'
  task: FocusTask | null
  elapsed: number
  running_since: number | null
  started_at: number
  duration: number | null
  auto_break: boolean
  break_seconds: number
}

export interface TimerResponse {
  timer: Timer | null
  now: number
  today: string
}

export type TimerAction = 'pause' | 'resume' | 'finish' | 'start_break' | 'dismiss'

export interface BackupCounts {
  plans: number
  days: number
  focus: number
  categories: number
  milestones?: number
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
