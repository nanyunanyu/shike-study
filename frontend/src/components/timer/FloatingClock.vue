<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Check,
  CheckCircle2,
  Coffee,
  Hourglass,
  Maximize2,
  Pause,
  Play,
  Square,
  Timer as TimerIcon,
  Watch,
  X,
} from 'lucide-vue-next'
import ProgressRing from '@/components/ui/ProgressRing.vue'
import { useFloatingDock } from '@/composables/useFloatingDock'
import { preferences } from '@/stores/session'
import {
  actTimer,
  draftTask,
  finishTimer,
  floatingClockOpen,
  focusCompletion,
  startTimer,
  timer,
  timerBusy,
  timerProgress,
  timerReady,
  timerSeconds,
  timerStatus,
} from '@/stores/timer'
import { timerText } from '@/utils/date'

const props = defineProps<{
  account: string
  topBar: HTMLElement | null
  bottomNav: HTMLElement | null
}>()

const route = useRoute()

const layer = ref<HTMLElement | null>(null)
const trigger = ref<HTMLButtonElement | null>(null)
const panel = ref<HTMLElement | null>(null)
defineExpose({ trigger })

const { open, settling, bounds, size, drag, position, panelPlacement, beginPointer, movePointer, endPointer, clearPointer, toggle } =
  useFloatingDock({
    storageKey: `shike-study:floating-clock:${props.account}`,
    open: floatingClockOpen,
    layer,
    trigger,
    panel,
    topBar: () => props.topBar,
    bottomNav: () => props.bottomNav,
    routePath: () => route.fullPath,
  })

const displayTime = computed(() =>
  !timerReady.value ? '—:—' : timerText(timer.value ? timerSeconds.value : preferences.value.focus_minutes * 60),
)
const taskTitle = computed(() => timer.value?.task?.title ?? draftTask.value?.title ?? '自由专注')
const dialSize = computed(() => (bounds.value.compact ? 136 : 144))

const clockState = computed(() =>
  !timer.value
    ? 'idle'
    : timer.value.stage === 'offer'
      ? 'complete'
      : timer.value.stage === 'break'
        ? timer.value.running_since === null
          ? 'paused'
          : 'break'
        : timer.value.running_since === null
          ? 'paused'
          : 'running',
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
  if (!timer.value) {
    return {
      label: '开始专注',
      icon: Play,
      isPlay: true,
      run: () => startTimer('pomodoro', draftTask.value?.id ?? null),
    }
  }
  if (timer.value.stage === 'offer') {
    return { label: '开始休息', icon: Coffee, isPlay: false, run: () => actTimer('start_break') }
  }
  if (timer.value.running_since === null) {
    return { label: '继续计时', icon: Play, isPlay: true, run: () => actTimer('resume') }
  }
  return { label: '暂停计时', icon: Pause, isPlay: false, run: () => actTimer('pause') }
})

const secondary = computed(() => {
  if (!timer.value) return null
  if (timer.value.stage === 'offer') {
    return { label: '完成本轮', icon: Check, size: 17, run: () => actTimer('dismiss') }
  }
  return {
    label: timer.value.stage === 'break' ? '结束休息' : '结束并记录',
    icon: Square,
    size: 14,
    run: finishTimer,
  }
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
      :class="{ 'is-open': open, 'is-dragging': drag, 'is-settling': settling, 'is-complete': finishedRecently }"
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
      <span v-if="clockState === 'running' || clockState === 'break'" class="orb-pulse" aria-hidden="true"></span>
    </button>

    <Transition name="clock-pop">
      <section
        v-if="open"
        ref="panel"
        class="clock-sheet glass-card-solid"
        :data-state="clockState"
        role="dialog"
        aria-label="悬浮专注时钟"
        :style="panelPlacement"
      >
        <header class="clock-head">
          <div class="clock-task">
            <span class="status-dot" :data-state="clockState" aria-hidden="true"></span>
            <span class="clock-task-name" :title="taskTitle">{{ taskTitle }}</span>
          </div>
          <div class="clock-head-actions">
            <RouterLink :to="{ name: 'timer' }" class="clock-mini-btn" aria-label="打开完整专注页" title="专注页">
              <Maximize2 :size="13" />
            </RouterLink>
            <button type="button" class="clock-mini-btn" aria-label="收起悬浮时钟" title="收起" @click="open = false">
              <X :size="14" />
            </button>
          </div>
        </header>

        <div class="clock-dial">
          <div class="dial-shell" :data-state="clockState">
            <ProgressRing :progress="timerProgress ?? 0" :size="dialSize" :stroke="6" ticks />
            <div class="dial-readout">
              <strong class="dial-time tabular" :class="{ compact: displayTime.length > 5 }">{{ displayTime }}</strong>
              <component
                :is="dialIcon"
                :size="13"
                class="dial-glyph"
                :class="{ active: clockState === 'running' || clockState === 'break' || clockState === 'complete' }"
                aria-hidden="true"
              />
            </div>
          </div>
        </div>

        <div class="clock-controls">
          <button
            type="button"
            class="ctrl-primary"
            :class="{ 'is-play': primary.isPlay }"
            :disabled="!timerReady || timerBusy"
            :aria-label="primary.label"
            :title="primary.label"
            @click="primary.run()"
          >
            <component :is="primary.icon" :size="19" />
          </button>
          <button
            v-if="secondary"
            type="button"
            class="ctrl-secondary"
            :disabled="timerBusy"
            :aria-label="secondary.label"
            :title="secondary.label"
            @click="secondary.run()"
          >
            <component :is="secondary.icon" :size="secondary.size" />
          </button>
        </div>
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
    max(16px, env(safe-area-inset-bottom))
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
  transition:
    border-color 0.2s var(--ease-out),
    box-shadow 0.24s var(--ease-out),
    background 0.2s var(--ease-out);
}

.clock-orb:hover,
.clock-orb.is-open {
  border-color: var(--accent-border);
}

.clock-orb[data-state='running'],
.clock-orb[data-state='break'] {
  border-color: var(--accent-border);
  box-shadow:
    var(--specular),
    0 8px 24px -6px color-mix(in srgb, var(--accent) 42%, transparent),
    0 0 0 3px var(--accent-soft);
}

.clock-orb.is-dragging {
  cursor: grabbing;
  box-shadow:
    var(--specular),
    0 16px 32px -8px rgba(15, 23, 42, 0.28);
}

.clock-orb.is-settling {
  transition:
    transform 0.34s var(--ease-spring),
    border-color 0.2s var(--ease-out),
    box-shadow 0.24s var(--ease-out);
}

.orb-ring {
  position: absolute;
  inset: 0;
}

.orb-icon {
  position: relative;
  z-index: 1;
}

.orb-pulse {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 2.5px var(--surface-solid);
  animation: pulse-soft 1.8s ease-in-out infinite;
}

.clock-sheet {
  position: absolute;
  pointer-events: auto;
  padding: 13px 14px 16px;
  border-radius: 26px;
  display: grid;
  gap: 12px;
  overflow: hidden;
  border-color: var(--border-strong);
  box-shadow: var(--specular), var(--shadow-modal);
  background:
    radial-gradient(75% 60% at 50% 42%, var(--accent-soft), transparent 76%),
    var(--surface-glass-strong);
}

.clock-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
}

.clock-task {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
  flex: 1;
  padding-left: 2px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex: none;
  background: var(--ink-tertiary);
  transition: background 0.2s, box-shadow 0.2s;
}

.status-dot[data-state='running'],
.status-dot[data-state='break'] {
  background: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
  animation: pulse-soft 1.8s ease-in-out infinite;
}

.status-dot[data-state='complete'] {
  background: var(--success);
  box-shadow: 0 0 0 3px var(--success-soft);
}

.clock-task-name {
  font-size: 12.5px;
  font-weight: 590;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clock-head-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: none;
}

.clock-mini-btn {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--ink-secondary);
  transition: background 0.16s var(--ease-out), color 0.16s var(--ease-out), transform 0.16s var(--ease-spring);
}

.clock-mini-btn:hover {
  background: var(--surface-hover);
  color: var(--ink);
}

.clock-mini-btn:active {
  transform: scale(0.92);
}

.clock-dial {
  display: grid;
  place-items: center;
  padding: 2px 0;
}

.dial-shell {
  position: relative;
  display: grid;
  place-items: center;
  border-radius: 50%;
}

.dial-shell[data-state='running']::before,
.dial-shell[data-state='break']::before {
  content: '';
  position: absolute;
  inset: 14px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--accent-soft-strong), transparent 72%);
  opacity: 0.7;
  pointer-events: none;
}

.dial-readout {
  position: absolute;
  display: grid;
  justify-items: center;
  gap: 5px;
  pointer-events: none;
}

.dial-time {
  font-size: 32px;
  font-weight: 730;
  line-height: 1;
  letter-spacing: -0.04em;
  color: var(--ink);
}

.dial-time.compact {
  font-size: 24px;
}

.dial-glyph {
  color: var(--ink-tertiary);
  transition: color 0.2s;
}

.dial-glyph.active {
  color: var(--accent);
}

.clock-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding-top: 2px;
}

.ctrl-primary,
.ctrl-secondary {
  border-radius: 50%;
  display: grid;
  place-items: center;
  transition:
    transform 0.18s var(--ease-spring),
    filter 0.18s var(--ease-out),
    background 0.18s var(--ease-out),
    border-color 0.18s var(--ease-out),
    box-shadow 0.22s var(--ease-out),
    opacity 0.18s;
}

.ctrl-primary {
  width: 46px;
  height: 46px;
  border: 1px solid transparent;
  background: linear-gradient(145deg, var(--accent), var(--accent-hover));
  color: var(--on-accent);
  box-shadow:
    0 2px 6px rgba(0, 0, 0, 0.10),
    0 10px 22px -8px var(--accent);
}

.ctrl-primary.is-play :deep(svg) {
  transform: translateX(1px);
}

.ctrl-primary:hover:not(:disabled) {
  filter: brightness(1.06);
  transform: translateY(-1px);
  box-shadow:
    0 4px 8px rgba(0, 0, 0, 0.12),
    0 14px 26px -8px var(--accent);
}

.ctrl-secondary {
  width: 38px;
  height: 38px;
  background: var(--surface-subtle);
  border: 1px solid var(--border-strong);
  color: var(--ink-secondary);
  box-shadow: var(--specular);
}

.ctrl-secondary:hover:not(:disabled) {
  background: var(--surface-solid);
  color: var(--ink);
  border-color: var(--accent-border);
}

.ctrl-primary:active:not(:disabled),
.ctrl-secondary:active:not(:disabled) {
  transform: scale(0.93);
}

.ctrl-primary:disabled,
.ctrl-secondary:disabled {
  opacity: 0.44;
}

@media (max-width: 768px) {
  .clock-layer {
    inset: calc(max(var(--clock-top-offset, 0px), env(safe-area-inset-top)) + 10px)
      max(8px, env(safe-area-inset-right))
      calc(max(var(--clock-bottom-offset, 0px), env(safe-area-inset-bottom)) + 10px)
      max(8px, env(safe-area-inset-left));
  }
  .clock-sheet {
    padding: 12px 13px 15px;
    border-radius: 24px;
    gap: 10px;
  }
  .dial-time {
    font-size: 30px;
  }
  .dial-time.compact {
    font-size: 23px;
  }
  .ctrl-primary {
    width: 44px;
    height: 44px;
  }
  .ctrl-secondary {
    width: 36px;
    height: 36px;
  }
}

.clock-pop-enter-active,
.clock-pop-leave-active {
  transition: opacity 0.18s var(--ease-out), transform 0.26s var(--ease-spring);
}

.clock-pop-enter-from,
.clock-pop-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
</style>
