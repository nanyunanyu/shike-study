import { duration, labelDate, MOODS } from '../state'
import type { Mood, Palette } from '../types'

export interface ShareCardPayload {
  date: string
  username: string
  completed: number
  total: number
  focusSeconds: number
  goalMinutes: number
  streak: number
  checked: boolean
  mood: Mood | null
  focusScore: number | null
  takeaways: string[]
  reflection: string
  palette: Palette
  dark: boolean
}

const THEME_MAP: Record<Palette, { primary: string; secondary: string; lightA: string; lightB: string; darkA: string; darkB: string }> = {
  blue: { primary: '#2563eb', secondary: '#0ea5e9', lightA: '#eff6ff', lightB: '#e0f2fe', darkA: '#0f172a', darkB: '#172554' },
  mint: { primary: '#0d9488', secondary: '#10b981', lightA: '#f0fdfa', lightB: '#dcfce7', darkA: '#0a1919', darkB: '#11302e' },
  lilac: { primary: '#7c3aed', secondary: '#a855f7', lightA: '#f5f3ff', lightB: '#fae8ff', darkA: '#130e24', darkB: '#271748' },
  amber: { primary: '#c26d18', secondary: '#f59e0b', lightA: '#fffbeb', lightB: '#ffedd5', darkA: '#1c140a', darkB: '#33200a' },
  rose: { primary: '#e11d48', secondary: '#f43f5e', lightA: '#fff1f2', lightB: '#ffe4e6', darkA: '#1e0c14', darkB: '#3b1122' },
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w, y, x + w, y + h, r)
  ctx.arcTo(x + w, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w, y, r)
  ctx.closePath()
}

function wrapLines(ctx: CanvasRenderingContext2D, text: string, maxWidth: number, maxLines: number): string[] {
  const lines: string[] = []
  let current = ''
  for (const char of Array.from(text)) {
    if (char === '\n') {
      lines.push(current)
      current = ''
      if (lines.length >= maxLines) break
      continue
    }
    const test = current + char
    if (ctx.measureText(test).width > maxWidth && current) {
      lines.push(current)
      current = char
      if (lines.length >= maxLines) break
    } else {
      current = test
    }
  }
  if (current && lines.length < maxLines) lines.push(current)
  if (lines.length === maxLines && text.length > lines.join('').length) {
    lines[maxLines - 1] = `${lines[maxLines - 1].slice(0, -1)}…`
  }
  return lines
}

export function renderShareCard(payload: ShareCardPayload): HTMLCanvasElement {
  const W = 1080
  const H = 1440
  const canvas = document.createElement('canvas')
  canvas.width = W
  canvas.height = H
  const ctx = canvas.getContext('2d')!
  const theme = THEME_MAP[payload.palette] ?? THEME_MAP.blue
  const isDark = payload.dark
  const font = '-apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", "Hiragino Sans GB", sans-serif'

  // Background gradient
  const bgGrad = ctx.createLinearGradient(0, 0, W, H)
  if (isDark) {
    bgGrad.addColorStop(0, '#090c12')
    bgGrad.addColorStop(0.5, theme.darkA)
    bgGrad.addColorStop(1, theme.darkB)
  } else {
    bgGrad.addColorStop(0, '#f8fafc')
    bgGrad.addColorStop(0.5, theme.lightA)
    bgGrad.addColorStop(1, theme.lightB)
  }
  ctx.fillStyle = bgGrad
  ctx.fillRect(0, 0, W, H)

  // Soft ambient orbs
  const orb1 = ctx.createRadialGradient(210, 220, 40, 210, 220, 480)
  orb1.addColorStop(0, isDark ? `${theme.primary}44` : `${theme.primary}28`)
  orb1.addColorStop(1, 'transparent')
  ctx.fillStyle = orb1
  ctx.fillRect(0, 0, W, H)

  const orb2 = ctx.createRadialGradient(880, 1180, 40, 880, 1180, 520)
  orb2.addColorStop(0, isDark ? `${theme.secondary}38` : `${theme.secondary}26`)
  orb2.addColorStop(1, 'transparent')
  ctx.fillStyle = orb2
  ctx.fillRect(0, 0, W, H)

  // Outer Frosted Glass Card
  ctx.save()
  ctx.shadowColor = isDark ? 'rgba(0,0,0,0.55)' : 'rgba(15,23,42,0.12)'
  ctx.shadowBlur = 60
  ctx.shadowOffsetY = 24
  roundRect(ctx, 76, 86, W - 152, H - 172, 46)
  ctx.fillStyle = isDark ? 'rgba(20, 25, 36, 0.84)' : 'rgba(255, 255, 255, 0.82)'
  ctx.fill()
  ctx.restore()

  roundRect(ctx, 76, 86, W - 152, H - 172, 46)
  ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.92)'
  ctx.lineWidth = 2.5
  ctx.stroke()

  const ink = isDark ? '#f8fafc' : '#0f172a'
  const muted = isDark ? '#94a3b8' : '#64748b'
  const cardInsetBg = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(15,23,42,0.035)'
  const cardInsetStroke = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(15,23,42,0.06)'

  // Brand Badge
  const brandGrad = ctx.createLinearGradient(136, 146, 200, 210)
  brandGrad.addColorStop(0, theme.primary)
  brandGrad.addColorStop(1, theme.secondary)
  roundRect(ctx, 136, 146, 62, 62, 18)
  ctx.fillStyle = brandGrad
  ctx.fill()

  ctx.strokeStyle = '#ffffff'
  ctx.lineWidth = 4
  ctx.lineCap = 'round'
  ctx.beginPath()
  ctx.arc(167, 177, 15, -Math.PI / 2, Math.PI * 1.15)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(167, 169)
  ctx.lineTo(167, 177)
  ctx.lineTo(174, 181)
  ctx.stroke()

  ctx.fillStyle = ink
  ctx.font = `700 32px ${font}`
  ctx.fillText('拾刻学习', 218, 178)
  ctx.fillStyle = muted
  ctx.font = `500 21px ${font}`
  ctx.fillText('SHIKE STUDIO · 每日学习手账', 218, 206)

  // Check-in status pill on top right
  const statusLabel = payload.checked ? '✓ 今日已打卡' : '学习记录'
  ctx.font = `600 22px ${font}`
  const pillW = ctx.measureText(statusLabel).width + 44
  roundRect(ctx, W - 136 - pillW, 152, pillW, 50, 25)
  ctx.fillStyle = payload.checked ? `${theme.primary}20` : cardInsetBg
  ctx.fill()
  ctx.strokeStyle = payload.checked ? `${theme.primary}55` : cardInsetStroke
  ctx.lineWidth = 1.5
  ctx.stroke()
  ctx.fillStyle = payload.checked ? theme.primary : muted
  ctx.fillText(statusLabel, W - 136 - pillW + 22, 185)

  // Date title
  ctx.fillStyle = ink
  ctx.font = `700 54px ${font}`
  ctx.fillText(labelDate(payload.date, 'long'), 136, 304)
  ctx.fillStyle = muted
  ctx.font = `500 25px ${font}`
  ctx.fillText(`${payload.date} · @${payload.username}`, 136, 344)

  // Hero Ring + Stats Section
  const heroY = 396
  const heroH = 310
  roundRect(ctx, 136, heroY, W - 272, heroH, 32)
  ctx.fillStyle = cardInsetBg
  ctx.fill()
  ctx.strokeStyle = cardInsetStroke
  ctx.lineWidth = 1.5
  ctx.stroke()

  const percent = payload.total ? Math.round((payload.completed / payload.total) * 100) : 0
  const cx = 286
  const cy = heroY + heroH / 2
  const r = 98

  ctx.beginPath()
  ctx.arc(cx, cy, r, 0, Math.PI * 2)
  ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.09)' : 'rgba(15,23,42,0.08)'
  ctx.lineWidth = 16
  ctx.stroke()

  const ringGrad = ctx.createLinearGradient(cx - r, cy - r, cx + r, cy + r)
  ringGrad.addColorStop(0, theme.primary)
  ringGrad.addColorStop(1, theme.secondary)
  ctx.beginPath()
  ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + (Math.PI * 2 * percent) / 100)
  ctx.strokeStyle = ringGrad
  ctx.lineWidth = 16
  ctx.lineCap = 'round'
  ctx.stroke()

  ctx.textAlign = 'center'
  ctx.fillStyle = ink
  ctx.font = `700 56px ${font}`
  ctx.fillText(`${percent}%`, cx, cy + 12)
  ctx.fillStyle = muted
  ctx.font = `500 21px ${font}`
  ctx.fillText(`${payload.completed} / ${payload.total} 任务`, cx, cy + 48)
  ctx.textAlign = 'left'

  // Right metrics inside hero
  const mx = 446
  ctx.fillStyle = muted
  ctx.font = `500 22px ${font}`
  ctx.fillText('今日深度专注', mx, heroY + 76)
  ctx.fillStyle = ink
  ctx.font = `700 48px ${font}`
  ctx.fillText(duration(payload.focusSeconds), mx, heroY + 134)

  // Focus goal bar
  const goalPct = Math.min(1, payload.focusSeconds / Math.max(60, payload.goalMinutes * 60))
  roundRect(ctx, mx, heroY + 160, 420, 12, 6)
  ctx.fillStyle = isDark ? 'rgba(255,255,255,0.09)' : 'rgba(15,23,42,0.08)'
  ctx.fill()
  if (goalPct > 0) {
    roundRect(ctx, mx, heroY + 160, Math.max(18, 420 * goalPct), 12, 6)
    ctx.fillStyle = ringGrad
    ctx.fill()
  }
  ctx.fillStyle = muted
  ctx.font = `500 20px ${font}`
  ctx.fillText(`目标 ${Math.round(payload.goalMinutes / 60 * 10) / 10} 小时 · 已达成 ${Math.round(goalPct * 100)}%`, mx, heroY + 206)

  // Streak badge
  roundRect(ctx, mx, heroY + 228, 224, 48, 24)
  ctx.fillStyle = `${theme.primary}1a`
  ctx.fill()
  ctx.fillStyle = theme.primary
  ctx.font = `650 22px ${font}`
  ctx.fillText(`连续打卡 ${payload.streak} 天`, mx + 24, heroY + 260)

  // Mood & Focus Score strip
  let cursorY = heroY + heroH + 46
  const moodObj = MOODS.find(m => m.id === payload.mood)
  if (moodObj || payload.focusScore) {
    let px = 136
    if (moodObj) {
      const label = `${moodObj.glyph}  今日状态 · ${moodObj.label}`
      ctx.font = `600 23px ${font}`
      const w = ctx.measureText(label).width + 44
      roundRect(ctx, px, cursorY, w, 52, 26)
      ctx.fillStyle = cardInsetBg
      ctx.fill()
      ctx.strokeStyle = cardInsetStroke
      ctx.stroke()
      ctx.fillStyle = ink
      ctx.fillText(label, px + 22, cursorY + 34)
      px += w + 16
    }
    if (payload.focusScore) {
      const stars = '★'.repeat(payload.focusScore) + '☆'.repeat(5 - payload.focusScore)
      const label = `专注度 ${stars}`
      ctx.font = `600 23px ${font}`
      const w = ctx.measureText(label).width + 44
      roundRect(ctx, px, cursorY, w, 52, 26)
      ctx.fillStyle = cardInsetBg
      ctx.fill()
      ctx.strokeStyle = cardInsetStroke
      ctx.stroke()
      ctx.fillStyle = theme.primary
      ctx.fillText(label, px + 22, cursorY + 34)
    }
    cursorY += 86
  }

  // Takeaways / Reflection box
  const cleanTakeaways = payload.takeaways.map(t => t.trim()).filter(Boolean).slice(0, 3)
  const noteText = payload.reflection.trim()
  const boxH = Math.max(260, H - 180 - cursorY)
  roundRect(ctx, 136, cursorY, W - 272, boxH, 32)
  ctx.fillStyle = cardInsetBg
  ctx.fill()
  ctx.strokeStyle = cardInsetStroke
  ctx.lineWidth = 1.5
  ctx.stroke()

  let ty = cursorY + 56
  ctx.fillStyle = theme.primary
  ctx.font = `700 24px ${font}`
  ctx.fillText('今日复盘与收获', 176, ty)
  ty += 46

  if (cleanTakeaways.length) {
    ctx.font = `500 27px ${font}`
    for (const item of cleanTakeaways) {
      ctx.fillStyle = theme.primary
      ctx.beginPath()
      ctx.arc(186, ty - 9, 5, 0, Math.PI * 2)
      ctx.fill()
      ctx.fillStyle = ink
      const lines = wrapLines(ctx, item, W - 400, 2)
      for (const line of lines) {
        ctx.fillText(line, 208, ty)
        ty += 40
      }
      ty += 8
    }
  }

  if (noteText) {
    ty += cleanTakeaways.length ? 12 : 0
    ctx.fillStyle = muted
    ctx.font = `500 25px ${font}`
    const lines = wrapLines(ctx, `“${noteText}”`, W - 360, 4)
    for (const line of lines) {
      if (ty > cursorY + boxH - 36) break
      ctx.fillText(line, 176, ty)
      ty += 38
    }
  }

  if (!cleanTakeaways.length && !noteText) {
    ctx.fillStyle = muted
    ctx.font = `500 26px ${font}`
    ctx.fillText('每一次克制而专注的积累，都在悄悄塑造更好的自己。', 176, ty + 14)
  }

  // Footer
  ctx.fillStyle = muted
  ctx.font = `500 21px ${font}`
  ctx.fillText('拾起每一刻专注 · Keep your quiet rhythm', 136, H - 122)

  return canvas
}
