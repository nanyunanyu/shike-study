export type Palette = 'blue' | 'mint' | 'lilac' | 'amber' | 'rose'
export type Appearance = 'light' | 'dark' | 'system'
export type Mood = 'great' | 'good' | 'neutral' | 'tired' | 'stressed'
export type Mode = 'pomodoro' | 'stopwatch' | 'countdown'
export type MessageKind = 'reminder' | 'encouragement'

export interface Times {
  start: string
  end: string | null
}
