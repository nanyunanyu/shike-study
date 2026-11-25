import { Monitor, Moon, Sun } from 'lucide-vue-next'
import type { Appearance, Palette, Preferences } from '@/types'

export const DEFAULT_PREFERENCES: Preferences = {
  focus_minutes: 25,
  break_minutes: 5,
  countdown_minutes: 30,
  auto_break: false,
  daily_focus_goal_minutes: 180,
  appearance: 'light',
  palette: 'blue',
}

export const PALETTES: ReadonlyArray<{ id: Palette; label: string; desc: string; swatch: string; swatch2: string }> = [
  { id: 'blue', label: '晴空蓝', desc: '澄澈克制', swatch: '#2563eb', swatch2: '#0ea5e9' },
  { id: 'mint', label: '青岚翠', desc: '清朗自然', swatch: '#0d9488', swatch2: '#10b981' },
  { id: 'lilac', label: '暮雾紫', desc: '雅致静谧', swatch: '#7c3aed', swatch2: '#a855f7' },
  { id: 'amber', label: '暖砂金', desc: '温润书香', swatch: '#c26d18', swatch2: '#f59e0b' },
  { id: 'rose', label: '晨樱绯', desc: '轻盈柔和', swatch: '#e11d48', swatch2: '#f43f5e' },
]

export const APPEARANCES: ReadonlyArray<{ id: Appearance; label: string; icon: typeof Sun }> = [
  { id: 'light', label: '浅色通透', icon: Sun },
  { id: 'dark', label: '午夜深色', icon: Moon },
  { id: 'system', label: '跟随系统', icon: Monitor },
]

export function paletteSwatch(color: Palette): string {
  return PALETTES.find(item => item.id === color)?.swatch ?? '#2563eb'
}
