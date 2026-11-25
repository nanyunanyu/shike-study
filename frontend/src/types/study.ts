import type { Mode, Mood, Times } from './common'

export interface Task extends Times {
  id: string
  title: string
  category: string
  note: string
  estimate: number | null
}

export interface AdhocTaskPayload extends Times {
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
