<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowUpRight, CheckCircle2, Coffee, Hourglass, Link2, Pause, Play, Square, Timer as TimerIcon, Watch, X } from 'lucide-vue-next'
import {
  actTimer,
  finishTimer,
  focusCompletion,
  preferences,
  startTimer,
  timer,
  timerBusy,
  timerModeLabels,
  timerProgress,
  timerReady,
  timerSeconds,
  timerStatus,
  timerText,
} from '../state'
import ProgressRing from './ui/ProgressRing.vue'

type Point = { x: number; y: number }
type Dock = { edge: 'left' | 'right'; height: number }
type Gesture = { id: number; start: Point; origin: Point }

const props = defineProps<{ account: string; bottomNav: HTMLElement | null }>()
const emit = defineEmits<{ openChange: [open: boolean] }>()
const route = useRoute()

const layer = ref<HTMLElement | null>(null)
const trigger = ref<HTMLButtonElement | null>(null)
defineExpose({ trigger })

const open = ref(false)
const settling = ref(false)
const gap = 10
const dragThreshold = 7
const bounds = ref({ width: 0, height: 0, compact: false })
const size = computed(() => (bounds.value.compact ? 42 : 48))
const drag = ref<Point | null>(null)
let gesture: Gesture | null = null
let ignorePointerClick = false

watch(open, value => emit('openChange', value), { flush: 'sync' })

const storageKey = `shike-study:floating-clock:${props.account}`
const clamp = (value: number, max: number) => Math.min(Math.max(value, 0), max)

function loadDock(): Dock {
  try {
    const saved = JSON.parse(window.localStorage.getItem(storageKey) ?? 'null')
    if ((saved?.edge === 'left' || saved?.edge === 'right') && Number.isFinite(saved.height)) {
      return { edge: saved.edge, height: clamp(saved.height, 1) }
    }
  } catch {
    /* ignore */
  }
  return { edge: 'right', height: 1 }
}

const dock = ref(loadDock())
const maxX = computed(() => Math.max(0, bounds.value.width - size.value))
const maxY = computed(() => Math.max(0, bounds.value.height - size.value))
const position = computed(() =>
  drag.value
    ? { x: clamp(drag.value.x, maxX.value), y: clamp(drag.value.y, maxY.value) }
    : { x: dock.value.edge === 'left' ? 0 : maxX.value, y: dock.value.height * maxY.value },
)

const panelPlacement = computed(() => {
  const { width, height, compact } = bounds.value
  const { x, y } = position.value
  const s = size.value
  const w = Math.min(width, compact ? 268 : 304)
  const left = dock.value.edge === 'left'
  const beside = width >= w + s + gap
  const above = beside ? y > maxY.value / 2 : y >= height - y - s
  return {
    width: `${w}px`,
    left: `${beside ? (left ? x + s + gap : x - w - gap) : left ? 0 : width - w}px`,
    top: above ? undefined : `${beside ? y : y + s + gap}px`,
    bottom: above ? `${height - y - (beside ? s : 0) + (beside ? 0 : gap)}px` : undefined,
  }
})

function measure() {
  const frame = layer.value
  if (!frame) return
  const navHeight = props.bottomNav?.offsetHeight ?? 0
  frame.style.setProperty('--clock-nav-height', `${navHeight}px`)
  const width = frame.clientWidth
  const height = frame.clientHeight
  const compact = navHeight > 0
  if (width === bounds.value.width && height === bounds.value.height && compact === bounds.value.compact) return
  settling.value = false
  bounds.value = { width, height, compact }
}

let resize: ResizeObserver | undefined
watch(
  () => props.bottomNav,
  (nav, previous) => {
    if (previous) resize?.unobserve(previous)
    if (nav) resize?.observe(nav)
    measure()
  },
  { flush: 'post' },
)

function beginPointer(event: PointerEvent) {
  if (!event.isPrimary || event.button !== 0 || gesture || !trigger.value || !layer.value) return
  const frame = layer.value.getBoundingClientRect()
  const button = trigger.value.getBoundingClientRect()
  gesture = {
    id: event.pointerId,
    start: { x: event.clientX, y: event.clientY },
    origin: { x: button.left - frame.left, y: button.top - frame.top },
  }
  ignorePointerClick = false
  trigger.value.setPointerCapture(event.pointerId)
}

function movePointer(event: PointerEvent) {
  if (!gesture || event.pointerId !== gesture.id) return
  const dx = event.clientX - gesture.start.x
  const dy = event.clientY - gesture.start.y
  if (!drag.value && Math.hypot(dx, dy) < dragThreshold) return
  settling.value = false
  open.value = false
  drag.value = { x: gesture.origin.x + dx, y: gesture.origin.y + dy }
}

function clearPointer() {
  const id = gesture?.id
  gesture = null
  drag.value = null
  if (id != null && trigger.value?.hasPointerCapture(id)) trigger.value.releasePointerCapture(id)
}

function endPointer(event: PointerEvent) {
  if (gesture?.id !== event.pointerId) return
  movePointer(event)
  if (drag.value) {
    const { x, y } = position.value
    dock.value = { edge: x < maxX.value / 2 ? 'left' : 'right', height: maxY.value ? y / maxY.value : dock.value.height }
    settling.value = true
    ignorePointerClick = true
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(dock.value))
    } catch {
      /* ignore */
    }
  }
  clearPointer()
}

function toggle(event: MouseEvent) {
  if (ignorePointerClick && event.detail > 0) return
  open.value = !open.value
}

function onOutside(event: PointerEvent) {
  if (open.value && event.target instanceof Node && !layer.value?.contains(event.target)) open.value = false
}

function onEscape(event: KeyboardEvent) {
  if (open.value && event.key === 'Escape') {
    event.preventDefault()
    open.value = false
    void nextTick(() => trigger.value?.focus({ preventScroll: true }))
  }
}

watch(() => route.fullPath, () => {
  open.value = false
  clearPointer()
})

onMounted(() => {
  measure()
  resize = new ResizeObserver(measure)
  if (layer.value) resize.observe(layer.value)
  if (props.bottomNav) resize.observe(props.bottomNav)
  document.addEventListener('pointerdown', onOutside, true)
  document.addEventListener('keydown', onEscape)
})

onUnmounted(() => {
  if (open.value) emit('openChange', false)
  resize?.disconnect()
  document.removeEventListener('pointerdown', onOutside, true)
  document.removeEventListener('keydown', onEscape)
})

const displayTime = computed(() =>
  !timerReady.value ? '—:—' : timerText(timer.value ? timerSeconds.value : preferences.value.focus_minutes * 60),
)
const clockState = computed(() =>
  !timer.value ? 'idle' : timer.value.stage === 'offer' ? 'complete' : timer.value.running_since === null ? 'paused' : 'running',
)
const dialIcon = computed(() =>
  timer.value?.stage === 'offer'
    ? CheckCircle2
    : timer.value?.stage === 'break'
      ? Coffee
      : timer.value?.mode === 'stopwatch'
        ? Watch
        : timer.value?.mode === 'countdown'
          ? Hourglass
          : TimerIcon,
)
const primary = computed(() => {
  if (!timer.value) return { label: '开始番茄专注', icon: Play, run: () => startTimer('pomodoro', null) }
  if (timer.value.stage === 'offer') return { label: '开始休息', icon: Coffee, run: () => actTimer('start_break') }
  if (timer.value.running_since === null) return { label: '继续专注', icon: Play, run: () => actTimer('resume') }
  return { label: '暂停', icon: Pause, run: () => actTimer('pause') }
})
const secondary = computed(() => {
  if (!timer.value) return null
  if (timer.value.stage === 'offer') return { label: '跳过', icon: CheckCircle2, run: () => actTimer('dismiss') }
  return { label: timer.value.stage === 'break' ? '结束休息' : '结束并记录', icon: Square, run: finishTimer }
})
const finishedRecently = computed(() => !!focusCompletion.value && timer.value?.stage === 'offer')
</script>

<template>
  <div ref="layer" class="clock-layer" :style="{ '--clock-size': `${size}px` }">
    <button
      v-show="bounds.width"
      ref="trigger"
      type="button"
      class="clock-orb glass-card-solid"
      :data-state="clockState"
      :class="{ 'is-dragging': drag, 'is-settling': settling, 'is-complete': finishedRecently }"
      :style="{ transform: `translate3d(${position.x}px, ${position.y}px, 0)` }"
      aria-label="悬浮番茄时钟"
      :title="`番茄时钟 · ${timerStatus}`"
      :aria-expanded="open"
      @pointerdown="beginPointer"
      @pointermove="movePointer"
      @pointerup="endPointer"
      @pointercancel="clearPointer"
      @click="toggle"
    >
      <ProgressRing class="orb-ring" :progress="timerProgress" :size="size" :stroke="3" />
      <component :is="dialIcon" :size="bounds.compact ? 17 : 19" class="orb-icon" />
      <span v-if="clockState === 'running'" class="orb-pulse" aria-hidden="true"></span>
    </button>

    <Transition name="clock-pop">
      <section v-if="open" class="clock-sheet glass-card-solid" role="dialog" aria-label="快速专注控制" :style="panelPlacement">
        <header class="clock-sheet-head">
          <div class="clock-sheet-title">
            <span class="status-dot" :data-state="clockState"></span>
            <strong>{{ timerStatus }}</strong>
            <span class="tertiary">{{ timerModeLabels[timer?.mode ?? 'pomodoro'] }}</span>
          </div>
          <button type="button" class="icon-btn sm" aria-label="关闭" @click="open = false"><X :size="16" /></button>
        </header>

        <div class="clock-sheet-main">
          <div class="mini-ring-wrap">
            <ProgressRing :progress="timerProgress ?? 0" :size="56" :stroke="4.5" />
            <component :is="dialIcon" :size="18" class="accent-text mini-ring-icon" />
          </div>
          <div class="clock-sheet-digits">
            <strong class="tabular" :class="{ compact: displayTime.length > 5 }">{{ displayTime }}</strong>
            <span class="clock-task-line muted">
              <Link2 :size="13" />
              <span>{{ timer?.task?.title ?? '自由专注' }}</span>
            </span>
          </div>
        </div>

        <div class="clock-sheet-actions">
          <button type="button" class="btn primary full" :disabled="!timerReady || timerBusy" @click="primary.run()">
            <component :is="primary.icon" :size="15" />{{ primary.label }}
          </button>
          <button v-if="secondary" type="button" class="btn secondary" :disabled="timerBusy" @click="secondary.run()">
            <component :is="secondary.icon" :size="14" />{{ secondary.label }}
          </button>
        </div>

        <RouterLink :to="{ name: 'timer' }" class="clock-sheet-link">
          <span>进入沉浸专注工作台</span>
          <ArrowUpRight :size="15" />
        </RouterLink>
      </section>
    </Transition>
  </div>
</template>

<style scoped>
.clock-layer {
  position: fixed;
  z-index: 60;
  pointer-events: none;
  inset: max(12px, env(safe-area-inset-top)) max(12px, env(safe-area-inset-right))
    max(calc(var(--clock-nav-height, 0px) + 16px), env(safe-area-inset-bottom))
    calc(max(var(--sidebar-offset, 0px), env(safe-area-inset-left)) + 12px);
}
.clock-orb {
  position: absolute;
  top: 0;
  left: 0;
  width: var(--clock-size);
  height: var(--clock-size);
  border-radius: 50%;
  display: grid;
  place-items: center;
  pointer-events: auto;
  touch-action: none;
  user-select: none;
  cursor: grab;
  color: var(--accent);
}
.clock-orb:hover {
  border-color: var(--accent-border);
}
.clock-orb.is-dragging {
  cursor: grabbing;
}
.clock-orb.is-settling {
  transition: transform 0.28s var(--ease-spring);
}
.orb-ring {
  position: absolute;
  inset: 0;
}
.orb-pulse {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 3px var(--surface-solid);
  animation: pulse-soft 1.8s ease-in-out infinite;
}
.clock-sheet {
  position: absolute;
  pointer-events: auto;
  padding: 16px;
  border-radius: var(--radius-lg);
  display: grid;
  gap: 14px;
}
.clock-sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.clock-sheet-title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ink-tertiary);
}
.status-dot[data-state='running'],
.status-dot[data-state='complete'] {
  background: var(--accent);
}
.clock-sheet-main {
  display: flex;
  align-items: center;
  gap: 14px;
}
.mini-ring-wrap {
  position: relative;
  display: grid;
  place-items: center;
  flex: none;
}
.mini-ring-icon {
  position: absolute;
}
.clock-sheet-digits {
  min-width: 0;
  display: grid;
  gap: 4px;
}
.clock-sheet-digits strong {
  font-size: 34px;
  font-weight: 720;
  line-height: 1;
  letter-spacing: -0.03em;
}
.clock-sheet-digits strong.compact {
  font-size: 26px;
}
.clock-task-line {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  min-width: 0;
}
.clock-task-line span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.clock-sheet-actions {
  display: flex;
  gap: 8px;
}
.clock-sheet-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  border-top: 1px solid var(--border);
  font-size: 12.5px;
  font-weight: 590;
  color: var(--accent);
}
.clock-sheet-link:hover {
  opacity: 0.8;
}

@media (max-width: 768px) {
  .clock-layer {
    display: none;
  }
}
.clock-pop-enter-active,
.clock-pop-leave-active {
  transition: opacity 0.18s var(--ease-out), transform 0.24s var(--ease-spring);
}
.clock-pop-enter-from,
.clock-pop-leave-to {
  opacity: 0;
  transform: scale(0.94);
}
</style>
