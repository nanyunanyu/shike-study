import type { Mode, Mood } from '@/types'

export const MOODS: ReadonlyArray<{ id: Mood; label: string; short: string; glyph: string; tone: string }> = [
  { id: 'great', label: '状态极佳', short: '极佳', glyph: '✦', tone: '#0ea5e9' },
  { id: 'good', label: '充实顺畅', short: '充实', glyph: '◉', tone: '#10b981' },
  { id: 'neutral', label: '平稳推进', short: '平稳', glyph: '○', tone: '#64748b' },
  { id: 'tired', label: '略感疲惫', short: '疲惫', glyph: '◐', tone: '#f59e0b' },
  { id: 'stressed', label: '有些焦虑', short: '焦虑', glyph: '△', tone: '#f43f5e' },
]

export function moodMeta(id: Mood | null) {
  return MOODS.find(item => item.id === id) ?? null
}

export const REVIEW_ISSUES = ['走神', '网课吸收不足', '错题未消化', '背诵不牢', '拖延', '其他'] as const

export const TIMER_MODE_LABELS: Record<Mode, string> = {
  pomodoro: '番茄钟',
  stopwatch: '正计时',
  countdown: '倒计时',
}

export const TIMER_QUICK_PRESETS: ReadonlyArray<{ minutes: number; label: string }> = [
  { minutes: 15, label: '15m 冲刺' },
  { minutes: 25, label: '25m 经典' },
  { minutes: 45, label: '45m 深度' },
  { minutes: 60, label: '60m 模考' },
]

export const TIMELINE_PERIODS: ReadonlyArray<{ id: string; label: string; range: string; match: (start: string) => boolean }> = [
  { id: 'early', label: '清晨时光', range: '00:00 – 08:30', match: s => s < '08:30' },
  { id: 'morning', label: '上午专注', range: '08:30 – 12:00', match: s => s >= '08:30' && s < '12:00' },
  { id: 'afternoon', label: '午后深耕', range: '12:00 – 18:00', match: s => s >= '12:00' && s < '18:00' },
  { id: 'evening', label: '晚间沉淀', range: '18:00 – 24:00', match: s => s >= '18:00' },
]
