import { ref } from 'vue'
import { BellRing, Sparkles } from 'lucide-vue-next'
import type { MessageKind } from './types'

export const activeDialogs = ref(0)

export const messageKinds: Record<MessageKind, { label: string; icon: typeof BellRing }> = {
  reminder: { label: '提醒', icon: BellRing },
  encouragement: { label: '加油', icon: Sparkles },
}

export function messageTime(timestamp: number, timeZone: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone,
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(timestamp * 1000)
}
