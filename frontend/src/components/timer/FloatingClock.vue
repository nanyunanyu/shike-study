<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowUpRight, CheckCircle2, Coffee, Hourglass, Link2, Pause, Play, Square, Timer as TimerIcon, Watch, X } from 'lucide-vue-next'
import ProgressRing from '@/components/ui/ProgressRing.vue'
import { useFloatingDock } from '@/composables/useFloatingDock'
import { TIMER_MODE_LABELS } from '@/constants/study'
import { preferences } from '@/stores/session'
import {
  actTimer,
  finishTimer,
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

const props = defineProps<{ account: string; bottomNav: HTMLElement | null }>()
const emit = defineEmits<{ openChange: [open: boolean] }>()
const route = useRoute()

const layer = ref<HTMLElement | null>(null)
const trigger = ref<HTMLButtonElement | null>(null)
defineExpose({ trigger })

const { open, settling, bounds, size, drag, position, panelPlacement, beginPointer, movePointer, endPointer, clearPointer, toggle } =
  useFloatingDock({
    storageKey: `shike-study:floating-clock:${props.account}`,
    layer,
    trigger,
    bottomNav: () => props.bottomNav,
    routePath: () => route.fullPath,
    onOpenChange: value => emit('openChange', value),
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
            <span class="tertiary">{{ TIMER_MODE_LABELS[timer?.mode ?? 'pomodoro'] }}</span>
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
