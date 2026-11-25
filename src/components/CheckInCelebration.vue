<script lang="ts">
import confetti from 'canvas-confetti'

type Burst = confetti.Options & { delay?: number }

const effects = {
  starburst: [
    { shapes: ['star'], origin: { x: 0.72, y: 0.52 }, spread: 360, startVelocity: 13, gravity: 0.22, scalar: 0.88, particleCount: 34 },
    { shapes: ['circle'], origin: { x: 0.72, y: 0.52 }, spread: 360, startVelocity: 17, gravity: 0.25, scalar: 0.48, particleCount: 24 },
  ],
  ribbons: [
    { origin: { x: 0.03, y: 0.82 }, angle: 36, spread: 40, startVelocity: 26, gravity: 0.5, particleCount: 32 },
    { origin: { x: 0.97, y: 0.82 }, angle: 144, spread: 40, startVelocity: 26, gravity: 0.5, particleCount: 32 },
  ],
  fireworks: [
    { origin: { x: 0.22, y: 0.36 }, spread: 360, startVelocity: 10, gravity: 0.25, scalar: 0.58, particleCount: 24 },
    { delay: 130, origin: { x: 0.74, y: 0.30 }, spread: 360, startVelocity: 12, gravity: 0.25, scalar: 0.58, particleCount: 28 },
    { delay: 260, origin: { x: 0.50, y: 0.56 }, spread: 360, startVelocity: 13, gravity: 0.25, scalar: 0.62, particleCount: 30 },
  ],
  'paper-rain': Array.from({ length: 9 }, (_, i): Burst => ({
    delay: (i % 3) * 60,
    origin: { x: (i + 0.5) / 9, y: 0.04 },
    angle: 270,
    spread: 68,
    startVelocity: 4,
    gravity: 0.36,
    drift: i % 2 ? 0.42 : -0.42,
    scalar: 0.68,
    particleCount: 8,
  })),
  'star-fountain': [
    { shapes: ['star'], origin: { x: 0.5, y: 1 }, spread: 40, startVelocity: 23, gravity: 0.52, scalar: 0.86, particleCount: 28 },
    { delay: 95, shapes: ['star'], origin: { x: 0.5, y: 1 }, spread: 58, startVelocity: 18, gravity: 0.52, scalar: 0.68, particleCount: 22 },
  ],
  comet: [
    { shapes: ['star'], origin: { x: 0.22, y: 0.76 }, angle: 24, spread: 10, startVelocity: 22, gravity: 0.08, scalar: 1.0, particleCount: 14 },
    { delay: 85, shapes: ['circle'], origin: { x: 0.22, y: 0.76 }, angle: 24, spread: 24, startVelocity: 14, gravity: 0.18, scalar: 0.48, particleCount: 24 },
  ],
  bubbles: Array.from({ length: 5 }, (_, i): Burst => ({
    delay: i * 52,
    shapes: ['circle'],
    origin: { x: 0.16 + 0.17 * i, y: 0.86 },
    angle: 90,
    spread: 26,
    startVelocity: 4 + (i % 2) * 2,
    gravity: -0.48,
    decay: 0.92,
    drift: i % 2 ? -0.44 : 0.44,
    scalar: 1.12,
    particleCount: 6,
  })),
  ripples: Array.from({ length: 3 }, (_, i): Burst => ({
    delay: i * 135,
    shapes: ['circle'],
    origin: { x: 0.56, y: 0.48 },
    spread: 360,
    startVelocity: 7 + i * 2.5,
    gravity: 0.04,
    flat: true,
    scalar: 0.5,
    particleCount: 24,
  })),
  zigzag: Array.from({ length: 5 }, (_, i): Burst => ({
    delay: i * 65,
    shapes: ['star'],
    origin: { x: 0.18 + 0.16 * i, y: i % 2 ? 0.28 : 0.7 },
    angle: i % 2 ? 300 : 60,
    spread: 26,
    startVelocity: 9,
    gravity: 0.22,
    scalar: 0.68,
    particleCount: 10,
  })),
  pinwheel: Array.from({ length: 6 }, (_, i): Burst => ({
    delay: i * 50,
    shapes: ['square'],
    origin: { x: 0.54, y: 0.5 },
    angle: 35 + 60 * i,
    spread: 22,
    startVelocity: 12,
    gravity: 0.14,
    scalar: 0.75,
    particleCount: 10,
  })),
  'cross-sparks': [45, 135, 225, 315].map((angle): Burst => ({
    shapes: ['star'],
    origin: { x: 0.52, y: 0.5 },
    angle,
    spread: 10,
    startVelocity: 13,
    gravity: 0.04,
    scalar: 0.8,
    particleCount: 12,
  })),
  wave: Array.from({ length: 6 }, (_, i): Burst => ({
    delay: i * 54,
    shapes: ['square'],
    origin: { x: 0.1 + 0.16 * i, y: 0.88 },
    angle: 72,
    spread: 22,
    startVelocity: 13 + 4 * Math.sin((i * Math.PI) / 5),
    gravity: 0.68,
    scalar: 0.78,
    particleCount: 10,
  })),
  'twin-bloom': [
    { shapes: ['circle'], origin: { x: 0.3, y: 0.66 }, angle: 112, spread: 145, startVelocity: 12, gravity: 0.3, scalar: 0.9, particleCount: 24 },
    { shapes: ['circle'], origin: { x: 0.7, y: 0.66 }, angle: 68, spread: 145, startVelocity: 12, gravity: 0.3, scalar: 0.9, particleCount: 24 },
  ],
  hourglass: [
    { shapes: ['square', 'circle'], origin: { x: 0.55, y: 0.09 }, angle: 270, spread: 24, startVelocity: 9, gravity: 0.31, scalar: 0.64, particleCount: 24 },
    { shapes: ['square', 'circle'], origin: { x: 0.55, y: 0.91 }, angle: 90, spread: 24, startVelocity: 13, gravity: 0.29, scalar: 0.64, particleCount: 24 },
    { delay: 170, shapes: ['star'], origin: { x: 0.55, y: 0.5 }, spread: 360, startVelocity: 7, gravity: 0.16, scalar: 0.74, particleCount: 16 },
  ],
  'side-sweep': Array.from({ length: 4 }, (_, i): Burst => ({
    delay: i * 55,
    shapes: ['square'],
    origin: { x: 0.96, y: 0.24 + 0.17 * i },
    angle: 180,
    spread: 9,
    startVelocity: 23,
    gravity: 0.08,
    scalar: 0.74,
    particleCount: 12,
  })),
} satisfies Record<string, Burst[]>

export type CheckInEffect = keyof typeof effects
export const CHECKIN_EFFECT_NAMES = Object.keys(effects) as CheckInEffect[]

let lastEffect: CheckInEffect | null = null
export function chooseCheckInEffect(): CheckInEffect {
  const pool = CHECKIN_EFFECT_NAMES.filter(name => name !== lastEffect)
  const picked = pool[Math.floor(Math.random() * pool.length)] ?? CHECKIN_EFFECT_NAMES[0]!
  lastEffect = picked
  return picked
}
</script>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const props = defineProps<{ effect: CheckInEffect }>()
const canvas = ref<HTMLCanvasElement | null>(null)
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
const pending: number[] = []
let cannon: confetti.CreateTypes | undefined

function stop() {
  pending.splice(0).forEach(id => window.clearTimeout(id))
  cannon?.reset()
}

function stopIfDisabled() {
  if (document.hidden || reducedMotion.matches) stop()
}

onMounted(() => {
  if (!canvas.value || reducedMotion.matches || document.hidden) return
  const fire = confetti.create(canvas.value, { resize: true, disableForReducedMotion: true })
  cannon = fire
  const theme = getComputedStyle(document.documentElement)
  const colors = ['--accent', '--accent-2', '--warning', '--success']
    .map(name => theme.getPropertyValue(name).trim())
    .filter(Boolean)
  const palette = colors.length ? colors : ['#2563eb', '#0ea5e9', '#f59e0b', '#10b981']
  const bursts: Burst[] = effects[props.effect]
  for (const { delay = 0, ...options } of bursts) {
    const shoot = () => {
      void fire({ colors: palette, ticks: 56, ...options })
    }
    if (delay) pending.push(window.setTimeout(shoot, delay))
    else shoot()
  }
  document.addEventListener('visibilitychange', stopIfDisabled)
  reducedMotion.addEventListener('change', stopIfDisabled)
})

onUnmounted(() => {
  stop()
  document.removeEventListener('visibilitychange', stopIfDisabled)
  reducedMotion.removeEventListener('change', stopIfDisabled)
})
</script>

<template>
  <canvas ref="canvas" class="check-in-celebration" :data-effect="effect" aria-hidden="true"></canvas>
</template>

<style scoped>
.check-in-celebration {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 4;
  pointer-events: none;
  border-radius: inherit;
}
</style>
