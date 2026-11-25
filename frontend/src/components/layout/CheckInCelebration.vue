<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { Sparkles } from 'lucide-vue-next'
import { checkInCelebration, clearCheckInCelebration } from '@/stores/ui'
import { createCelebrationPlayer, type CelebrationPlayer } from '@/utils/celebrationEngine'

const mounted = ref(false)
const badgeVisible = ref(false)
const canvasRef = ref<HTMLCanvasElement | null>(null)

const reducedMotionQuery =
  typeof window !== 'undefined' ? window.matchMedia('(prefers-reduced-motion: reduce)') : null

let player: CelebrationPlayer | null = null
let badgeTimer = 0
let unmountTimer = 0
let activeRunId = 0
let canvasFinished = false

const isMilestone = computed(() => !!checkInCelebration.milestoneTitle)
const headlineText = computed(() =>
  checkInCelebration.milestoneTitle ? `里程碑 · ${checkInCelebration.milestoneTitle}` : '今日已拾刻',
)
const sublineText = computed(() =>
  checkInCelebration.streak > 1 ? `已连续打卡 ${checkInCelebration.streak} 天` : '开启新的连签节奏',
)

const dialTicks = Array.from({ length: 12 }, (_, idx) => {
  const angle = (idx / 12) * Math.PI * 2 - Math.PI / 2
  const major = idx % 3 === 0
  const r1 = major ? 17.5 : 18.8
  const r2 = 21.2
  return {
    x1: 24 + Math.cos(angle) * r1,
    y1: 24 + Math.sin(angle) * r1,
    x2: 24 + Math.cos(angle) * r2,
    y2: 24 + Math.sin(angle) * r2,
    major,
  }
})

function clearTimers() {
  window.clearTimeout(badgeTimer)
  window.clearTimeout(unmountTimer)
  badgeTimer = 0
  unmountTimer = 0
}

function teardownImmediate() {
  clearTimers()
  player?.destroy()
  player = null
  badgeVisible.value = false
  mounted.value = false
  canvasFinished = true
}

function maybeFinish(runId: number) {
  if (runId !== activeRunId) return
  if (badgeVisible.value || !canvasFinished) return
  window.clearTimeout(unmountTimer)
  unmountTimer = window.setTimeout(() => {
    if (runId !== activeRunId) return
    mounted.value = false
    clearCheckInCelebration(runId)
  }, 460)
}

async function startRun(runId: number) {
  clearTimers()
  player?.destroy()
  player = null
  activeRunId = runId

  if (document.hidden) {
    mounted.value = false
    badgeVisible.value = false
    clearCheckInCelebration(runId)
    return
  }

  const reduced = !!reducedMotionQuery?.matches
  mounted.value = true
  badgeVisible.value = true
  canvasFinished = reduced

  const badgeHoldMs = reduced ? 1750 : isMilestone.value ? 2600 : 2250
  badgeTimer = window.setTimeout(() => {
    if (runId !== activeRunId) return
    badgeVisible.value = false
    maybeFinish(runId)
  }, badgeHoldMs)

  if (reduced) return

  await nextTick()
  if (runId !== activeRunId || !canvasRef.value) return

  player = createCelebrationPlayer(canvasRef.value, {
    scene: checkInCelebration.scene,
    origin: checkInCelebration.origin,
    milestone: isMilestone.value,
    onComplete: () => {
      if (runId !== activeRunId) return
      player = null
      canvasFinished = true
      maybeFinish(runId)
    },
  })
}

watch(
  () => [checkInCelebration.id, checkInCelebration.active] as const,
  ([id, active], prev) => {
    if (!active) {
      if (!mounted.value) return
      clearTimers()
      badgeVisible.value = false
      if (player) {
        player.fadeOut()
      } else {
        unmountTimer = window.setTimeout(() => {
          if (!checkInCelebration.active) mounted.value = false
        }, 320)
      }
      return
    }
    if (!prev || id !== prev[0] || !prev[1]) {
      void startRun(id)
    }
  },
)

function onVisibilityOrMotionChange() {
  if (document.hidden) {
    const id = activeRunId
    teardownImmediate()
    clearCheckInCelebration(id)
  } else if (reducedMotionQuery?.matches && player) {
    player.destroy()
    player = null
    canvasFinished = true
    maybeFinish(activeRunId)
  }
}

onMounted(() => {
  document.addEventListener('visibilitychange', onVisibilityOrMotionChange)
  reducedMotionQuery?.addEventListener('change', onVisibilityOrMotionChange)
})

onUnmounted(() => {
  teardownImmediate()
  document.removeEventListener('visibilitychange', onVisibilityOrMotionChange)
  reducedMotionQuery?.removeEventListener('change', onVisibilityOrMotionChange)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="mounted"
      class="checkin-celebration-layer"
      :data-scene="checkInCelebration.scene"
      :data-milestone="isMilestone ? 'true' : 'false'"
      aria-hidden="true"
    >
      <canvas ref="canvasRef" class="celebration-canvas"></canvas>

      <div class="ritual-stage">
        <Transition name="ritual-badge" appear>
          <div
            v-if="badgeVisible"
            :key="checkInCelebration.id"
            class="ritual-badge"
            :class="{ 'is-milestone': isMilestone }"
          >
            <span class="ritual-sheen"></span>

            <span class="ritual-seal">
              <span class="seal-halo"></span>
              <svg class="seal-svg" viewBox="0 0 48 48" width="44" height="44" fill="none">
                <defs>
                  <linearGradient :id="`shike-seal-grad-${checkInCelebration.id}`" x1="6" y1="6" x2="42" y2="42" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" class="seal-stop-a" />
                    <stop offset="100%" class="seal-stop-b" />
                  </linearGradient>
                </defs>
                <g class="seal-ticks">
                  <line
                    v-for="(tick, idx) in dialTicks"
                    :key="idx"
                    :x1="tick.x1"
                    :y1="tick.y1"
                    :x2="tick.x2"
                    :y2="tick.y2"
                    :stroke-width="tick.major ? 1.8 : 1.1"
                    stroke-linecap="round"
                    :class="tick.major ? 'tick-major' : 'tick-minor'"
                  />
                </g>
                <circle class="seal-track" cx="24" cy="24" r="14.5" stroke-width="2.1" />
                <circle
                  class="seal-arc"
                  cx="24"
                  cy="24"
                  r="14.5"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  :stroke="`url(#shike-seal-grad-${checkInCelebration.id})`"
                />
                <path
                  class="seal-check"
                  d="M17.8 24.4 L22.1 28.6 L30.6 19.6"
                  stroke-width="2.7"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  :stroke="`url(#shike-seal-grad-${checkInCelebration.id})`"
                />
              </svg>
            </span>

            <div class="ritual-copy">
              <strong class="ritual-title">{{ headlineText }}</strong>
              <span class="ritual-sub tabular">
                <Sparkles v-if="isMilestone" :size="12" class="milestone-spark" />
                {{ sublineText }}
              </span>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.checkin-celebration-layer {
  position: fixed;
  inset: 0;
  z-index: 165;
  pointer-events: none;
  overflow: hidden;
  user-select: none;
}

.celebration-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
}

.ritual-stage {
  position: absolute;
  left: 0;
  right: 0;
  top: 40%;
  transform: translateY(-50%);
  display: flex;
  justify-content: center;
  padding-inline: 16px;
}

.ritual-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 14px;
  padding: 13px 24px 13px 15px;
  border-radius: var(--radius-pill);
  background:
    radial-gradient(120% 140% at 12% 0%, var(--accent-soft-strong), transparent 60%),
    var(--surface-glass-strong);
  backdrop-filter: blur(26px) saturate(185%);
  -webkit-backdrop-filter: blur(26px) saturate(185%);
  border: 1px solid var(--accent-border);
  box-shadow:
    var(--specular),
    0 20px 52px -14px rgba(15, 23, 42, 0.22),
    0 0 0 1px rgba(255, 255, 255, 0.14),
    0 0 36px -10px var(--accent-ring);
  overflow: hidden;
  animation: ritual-float 2.6s ease-in-out 0.35s infinite;
}

.ritual-badge.is-milestone {
  background:
    radial-gradient(120% 150% at 14% 0%, rgba(245, 158, 11, 0.22), transparent 62%),
    radial-gradient(100% 130% at 90% 100%, var(--accent-soft), transparent 66%),
    var(--surface-glass-strong);
  border-color: rgba(245, 158, 11, 0.48);
  box-shadow:
    var(--specular),
    0 24px 60px -14px rgba(15, 23, 42, 0.28),
    0 0 42px -6px rgba(245, 158, 11, 0.36);
}

.ritual-sheen {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    112deg,
    transparent 24%,
    rgba(255, 255, 255, 0.42) 48%,
    rgba(255, 255, 255, 0.08) 58%,
    transparent 74%
  );
  transform: translateX(-125%);
  animation: ritual-sheen-sweep 0.95s var(--ease-out) 0.16s 1 forwards;
}

.ritual-seal {
  position: relative;
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  flex: none;
}

.seal-halo {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--accent-soft-strong), transparent 70%);
  animation: seal-halo-pop 0.9s var(--ease-out) forwards;
}

.is-milestone .seal-halo {
  background: radial-gradient(circle, rgba(251, 191, 36, 0.36), transparent 70%);
}

.seal-svg {
  position: relative;
  z-index: 1;
}

.seal-stop-a {
  stop-color: var(--accent);
}

.seal-stop-b {
  stop-color: var(--accent-2);
}

.is-milestone .seal-stop-a {
  stop-color: #f59e0b;
}

.is-milestone .seal-stop-b {
  stop-color: var(--accent);
}

.seal-ticks {
  transform-origin: 24px 24px;
  animation: seal-ticks-spin 0.85s var(--ease-spring) forwards;
}

.tick-major {
  stroke: var(--accent);
  opacity: 0.72;
}

.tick-minor {
  stroke: var(--ink-tertiary);
  opacity: 0.38;
}

.is-milestone .tick-major {
  stroke: #f59e0b;
  opacity: 0.9;
}

.seal-track {
  stroke: var(--border-strong);
  opacity: 0.55;
}

.seal-arc {
  transform-origin: 24px 24px;
  transform: rotate(-90deg);
  stroke-dasharray: 92;
  stroke-dashoffset: 92;
  animation: seal-arc-draw 0.54s var(--ease-out) 0.04s forwards;
}

.seal-check {
  stroke-dasharray: 24;
  stroke-dashoffset: 24;
  animation: seal-check-draw 0.34s var(--ease-spring) 0.22s forwards;
}

.ritual-copy {
  display: grid;
  gap: 2px;
  line-height: 1.2;
  min-width: 0;
}

.ritual-title {
  font-size: 16.5px;
  font-weight: 720;
  letter-spacing: -0.02em;
  color: var(--ink);
  white-space: nowrap;
}

.ritual-sub {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12.5px;
  font-weight: 590;
  color: var(--accent);
  white-space: nowrap;
}

.is-milestone .ritual-sub {
  color: var(--warning);
}

.milestone-spark {
  flex: none;
}

/* Badge Enter & Exit Transitions */
.ritual-badge-enter-active {
  transition:
    opacity 0.32s var(--ease-out),
    transform 0.46s var(--ease-spring);
}

.ritual-badge-leave-active {
  transition:
    opacity 0.42s var(--ease-out),
    transform 0.42s var(--ease-out);
}

.ritual-badge-enter-from {
  opacity: 0;
  transform: translateY(18px) scale(0.84);
}

.ritual-badge-leave-to {
  opacity: 0;
  transform: translateY(-14px) scale(0.95);
}

@keyframes ritual-float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

@keyframes ritual-sheen-sweep {
  0% {
    transform: translateX(-125%);
  }
  100% {
    transform: translateX(135%);
  }
}

@keyframes seal-halo-pop {
  0% {
    opacity: 0;
    transform: scale(0.5);
  }
  45% {
    opacity: 1;
    transform: scale(1.22);
  }
  100% {
    opacity: 0.55;
    transform: scale(1);
  }
}

@keyframes seal-ticks-spin {
  0% {
    opacity: 0;
    transform: rotate(-28deg) scale(0.84);
  }
  100% {
    opacity: 1;
    transform: rotate(0deg) scale(1);
  }
}

@keyframes seal-arc-draw {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes seal-check-draw {
  to {
    stroke-dashoffset: 0;
  }
}

@media (max-width: 768px) {
  .ritual-stage {
    top: 36%;
  }
  .ritual-badge {
    gap: 11px;
    padding: 10px 18px 10px 12px;
  }
  .ritual-seal {
    width: 38px;
    height: 38px;
  }
  .seal-svg {
    width: 38px;
    height: 38px;
  }
  .ritual-title {
    font-size: 15px;
  }
  .ritual-sub {
    font-size: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ritual-badge {
    animation: none;
  }
  .ritual-sheen {
    display: none;
  }
  .seal-arc,
  .seal-check {
    stroke-dashoffset: 0;
    animation: none;
  }
  .seal-ticks,
  .seal-halo {
    animation: none;
  }
}
</style>
