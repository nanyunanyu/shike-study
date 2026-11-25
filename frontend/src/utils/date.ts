export function duration(seconds: number): string {
  if (!seconds) return '0 分钟'
  if (seconds < 60) return `${seconds} 秒`
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor(seconds / 60) % 60
  return [hours && `${hours} 小时`, minutes && `${minutes} 分钟`].filter(Boolean).join(' ')
}

export function timerText(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor(seconds / 60) % 60
  return [...(hours > 0 ? [hours] : []), minutes, seconds % 60]
    .map(n => String(n).padStart(2, '0'))
    .join(':')
}

export function shiftDate(value: string, offset: number): string {
  const date = new Date(`${value}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + offset)
  return date.toISOString().slice(0, 10)
}

export function addDaysIso(baseIso: string, offset: number): string {
  return shiftDate(baseIso || new Date().toISOString().slice(0, 10), offset)
}

export function labelDate(value: string, style: 'long' | 'short' = 'long'): string {
  return !value
    ? ''
    : new Intl.DateTimeFormat('zh-CN', {
        month: 'long',
        day: 'numeric',
        ...(style === 'long' ? { weekday: 'long' } : {}),
        timeZone: 'UTC',
      }).format(new Date(`${value}T00:00:00Z`))
}

export function greetingForHour(hour: number): string {
  if (hour < 6) return '夜深静学'
  if (hour < 11) return '早安，开启澄澈一日'
  if (hour < 14) return '午安，保持平稳节奏'
  if (hour < 18) return '下午好，沉浸专注此刻'
  return '晚安，收获今日沉淀'
}

export function currentHHMM(timezone?: string): string {
  const now = new Date()
  try {
    const parts = new Intl.DateTimeFormat('en-GB', {
      timeZone: timezone || 'Asia/Shanghai',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).formatToParts(now)
    const h = parts.find(p => p.type === 'hour')?.value ?? '09'
    const m = parts.find(p => p.type === 'minute')?.value ?? '00'
    return `${h === '24' ? '00' : h}:${m}`
  } catch {
    return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  }
}

export function formatMessageTime(timestamp: number, timeZone: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone,
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(timestamp * 1000)
}

export function formatClockTime(timestamp: number, timeZone?: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(timestamp * 1000)
}
