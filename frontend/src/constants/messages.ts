import { BellRing, Sparkles } from 'lucide-vue-next'
import type { DispatchStatus, MessageKind } from '@/types'

export const MESSAGE_KINDS: Record<MessageKind, { label: string; icon: typeof BellRing }> = {
  reminder: { label: '提醒', icon: BellRing },
  encouragement: { label: '加油', icon: Sparkles },
}

export const DISPATCH_TABS: ReadonlyArray<{ id: DispatchStatus; label: string }> = [
  { id: 'pending', label: '待发送' },
  { id: 'sent', label: '已发送' },
  { id: 'canceled', label: '已取消' },
]
