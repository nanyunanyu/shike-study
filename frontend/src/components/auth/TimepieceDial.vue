<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, useId } from 'vue'

const props = withDefaults(
  defineProps<{
    size?: 'hero' | 'compact'
  }>(),
  { size: 'hero' },
)

const uid = useId()
const now = ref(new Date())
let timer = 0

onMounted(() => {
  timer = window.setInterval(() => {
    now.value = new Date()
  }, 1000)
})

onUnmounted(() => {
  window.clearInterval(timer)
})

const hours = computed(() => now.value.getHours())
const minutes = computed(() => now.value.getMinutes())
const seconds = computed(() => now.value.getSeconds())

const hourAngle = computed(() => (hours.value % 12) * 30 + minutes.value * 0.5)
const minuteAngle = computed(() => minutes.value * 6 + seconds.value * 0.1)
const secondAngle = computed(() => seconds.value * 6)

const dayProgress = computed(() => Math.max(0.08, (hours.value * 60 + minutes.value) / 1440))
const arcRadius = 96
const arcCircumference = 2 * Math.PI * arcRadius
const arcOffset = computed(() => arcCircumference * (1 - dayProgress.value))
const arcTipAngle = computed(() => dayProgress.value * Math.PI * 2 - Math.PI / 2)
const arcTipX = computed(() => 110 + Math.cos(arcTipAngle.value) * arcRadius)
const arcTipY = computed(() => 110 + Math.sin(arcTipAngle.value) * arcRadius)

const clockText = computed(
  () => `${String(hours.value).padStart(2, '0')}:${String(minutes.value).padStart(2, '0')}`,
)

const ticks = computed(() => {
  const count = props.size === 'hero' ? 60 : 12
  return Array.from({ length: count }, (_, idx) => {
    const angle = (idx / count) * Math.PI * 2 - Math.PI / 2
    const isHour = count === 12 || idx % 5 === 0
    const isCardinal = count === 12 ? idx % 3 === 0 : idx % 15 === 0
    const rOuter = 82
    const rInner = isCardinal ? 71 : isHour ? 74.5 : 78.2
    return {
      x1: 110 + Math.cos(angle) * rInner,
      y1: 110 + Math.sin(angle) * rInner,
      x2: 110 + Math.cos(angle) * rOuter,
      y2: 110 + Math.sin(angle) * rOuter,
      isCardinal,
      isHour,
    }
  })
})
</script>

<template>
  <div class="dial-stage" :class="`is-${size}`" aria-hidden="true">
    <div class="dial-aura"></div>
    <div class="dial-orbit">
      <span class="orbit-spark"></span>
    </div>

    <div class="dial-bezel">
      <svg class="dial-svg" viewBox="0 0 220 220" fill="none">
        <defs>
          <linearGradient :id="`dial-arc-${uid}`" x1="18" y1="18" x2="202" y2="202" gradientUnits="userSpaceOnUse">
            <stop offset="0%" class="grad-a" />
            <stop offset="100%" class="grad-b" />
          </linearGradient>
        </defs>

        <!-- Outer day-progress track & luminous arc -->
        <circle class="arc-track" cx="110" cy="110" :r="arcRadius" stroke-width="2" />
        <circle
          class="arc-fill"
          cx="110"
          cy="110"
          :r="arcRadius"
          stroke-width="2.6"
          stroke-linecap="round"
          :stroke="`url(#dial-arc-${uid})`"
          :stroke-dasharray="arcCircumference"
          :stroke-dashoffset="arcOffset"
        />
        <circle class="arc-tip-glow" :cx="arcTipX" :cy="arcTipY" r="5.5" />
        <circle class="arc-tip" :cx="arcTipX" :cy="arcTipY" r="2.4" />

        <!-- Precision dial ticks -->
        <line
          v-for="(tick, idx) in ticks"
          :key="idx"
          :x1="tick.x1"
          :y1="tick.y1"
          :x2="tick.x2"
          :y2="tick.y2"
          stroke-linecap="round"
          :class="tick.isCardinal ? 'tick-cardinal' : tick.isHour ? 'tick-hour' : 'tick-min'"
        />

        <!-- Live clock hands -->
        <g :transform="`rotate(${hourAngle} 110 110)`">
          <line class="hand-hour" x1="110" y1="117" x2="110" y2="66" stroke-linecap="round" />
        </g>
        <g :transform="`rotate(${minuteAngle} 110 110)`">
          <line class="hand-minute" x1="110" y1="120" x2="110" y2="48" stroke-linecap="round" />
        </g>
        <g v-if="size === 'hero'" :transform="`rotate(${secondAngle} 110 110)`">
          <line class="hand-second" x1="110" y1="126" x2="110" y2="42" stroke-linecap="round" />
        </g>

        <!-- Center pivot jewel -->
        <circle class="pivot-outer" cx="110" cy="110" r="5.4" />
        <circle class="pivot-inner" cx="110" cy="110" r="2.2" />
      </svg>
    </div>

    <span v-if="size === 'hero'" class="dial-readout tabular">{{ clockText }}</span>
  </div>
</template>

<style scoped>
.dial-stage {
  position: relative;
  display: grid;
  place-items: center;
  justify-items: center;
  gap: 16px;
}

.dial-aura {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  background:
    radial-gradient(circle at 35% 30%, var(--accent-soft-strong), transparent 60%),
    radial-gradient(circle at 70% 72%, var(--ambient-2), transparent 65%);
  filter: blur(24px);
  animation: dial-breathe 8s ease-in-out infinite;
}

.is-hero .dial-aura {
  width: 310px;
  height: 310px;
  top: -31px;
}

.is-compact .dial-aura {
  width: 152px;
  height: 152px;
  top: -32px;
  filter: blur(18px);
}

.dial-orbit {
  position: absolute;
  border-radius: 50%;
  border: 1px dashed color-mix(in srgb, var(--accent-border) 55%, transparent);
  pointer-events: none;
  animation: dial-orbit-spin 42s linear infinite;
}

.is-hero .dial-orbit {
  width: 282px;
  height: 282px;
  top: -17px;
}

.is-compact .dial-orbit {
  width: 108px;
  height: 108px;
  top: -10px;
}

.orbit-spark {
  position: absolute;
  top: -3px;
  left: 50%;
  width: 6px;
  height: 6px;
  margin-left: -3px;
  border-radius: 50%;
  background: var(--accent-2);
  box-shadow: 0 0 10px 2px var(--accent-ring);
}

.is-compact .orbit-spark {
  width: 4.5px;
  height: 4.5px;
  top: -2.25px;
  margin-left: -2.25px;
}

.dial-bezel {
  position: relative;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background:
    radial-gradient(120% 120% at 24% 16%, rgba(255, 255, 255, 0.42), transparent 52%),
    var(--surface-glass-strong);
  backdrop-filter: blur(26px) saturate(180%);
  -webkit-backdrop-filter: blur(26px) saturate(180%);
  border: 1px solid var(--border-strong);
  box-shadow:
    var(--specular),
    0 24px 56px -22px rgba(15, 23, 42, 0.22),
    0 0 0 1px color-mix(in srgb, var(--accent-border) 42%, transparent);
}

.is-hero .dial-bezel {
  width: 248px;
  height: 248px;
  padding: 12px;
}

.is-compact .dial-bezel {
  width: 88px;
  height: 88px;
  padding: 5px;
  box-shadow:
    var(--specular),
    0 14px 34px -12px rgba(15, 23, 42, 0.24),
    0 0 28px -8px var(--accent-ring);
}

.dial-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.grad-a {
  stop-color: var(--accent);
}

.grad-b {
  stop-color: var(--accent-2);
}

.arc-track {
  stroke: var(--border);
}

.arc-fill {
  transform-origin: 110px 110px;
  transform: rotate(-90deg);
  transition: stroke-dashoffset 0.8s var(--ease-out);
}

.arc-tip-glow {
  fill: var(--accent-soft-strong);
}

.arc-tip {
  fill: var(--accent);
}

.tick-cardinal {
  stroke: var(--ink);
  stroke-width: 2.3;
  opacity: 0.78;
}

.tick-hour {
  stroke: var(--ink-secondary);
  stroke-width: 1.5;
  opacity: 0.56;
}

.tick-min {
  stroke: var(--ink-tertiary);
  stroke-width: 1;
  opacity: 0.34;
}

.is-compact .tick-cardinal {
  stroke-width: 3.4;
}

.is-compact .tick-hour {
  stroke-width: 2.4;
}

.hand-hour {
  stroke: var(--ink);
  stroke-width: 4.4;
}

.hand-minute {
  stroke: var(--ink);
  stroke-width: 3;
  opacity: 0.88;
}

.is-compact .hand-hour {
  stroke-width: 7;
}

.is-compact .hand-minute {
  stroke-width: 5;
}

.hand-second {
  stroke: var(--accent);
  stroke-width: 1.5;
}

.pivot-outer {
  fill: var(--accent);
}

.pivot-inner {
  fill: var(--surface-solid);
}

.dial-readout {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.14em;
  color: var(--ink-tertiary);
}

@keyframes dial-breathe {
  0%, 100% {
    opacity: 0.78;
    transform: scale(0.97);
  }
  50% {
    opacity: 1;
    transform: scale(1.04);
  }
}

@keyframes dial-orbit-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .dial-aura,
  .dial-orbit {
    animation: none;
  }
}
</style>
