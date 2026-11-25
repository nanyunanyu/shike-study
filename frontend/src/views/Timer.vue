<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  CheckCircle2,
  Coffee,
  Hourglass,
  Link2,
  Maximize2,
  Pause,
  Play,
  Settings2,
  Square,
  Timer as TimerIcon,
  Watch,
} from 'lucide-vue-next'
import { fetchDay } from '@/api/days'
import AmbientMixer from '@/components/timer/AmbientMixer.vue'
import ImmersiveTimer from '@/components/timer/ImmersiveTimer.vue'
import TimerSettings from '@/components/timer/TimerSettings.vue'
import GlassModal from '@/components/ui/GlassModal.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PageSkeleton from '@/components/ui/PageSkeleton.vue'
import ProgressRing from '@/components/ui/ProgressRing.vue'
import { usePreferencesActions } from '@/composables/usePreferencesActions'
import { TIMER_MODE_LABELS, TIMER_QUICK_PRESETS } from '@/constants/study'
import { preferences, today } from '@/stores/session'
import {
  actTimer,
  finishTimer,
  startTimer,
  timer,
  timerBusy,
  timerProgress,
  timerReady,
  timerSeconds,
  timerStatus,
} from '@/stores/timer'
import type { DayTask, Mode, Preferences } from '@/types'
import { timerText } from '@/utils/date'

const route = useRoute()
const { saving: settingsBusy, savePreferences } = usePreferencesActions()

const modes = [
  { value: 'pomodoro', icon: TimerIcon },
  { value: 'stopwatch', icon: Watch },
  { value: 'countdown', icon: Hourglass },
] as const

const mode = ref<Mode>('pomodoro')
const selectedMinutes = ref<number | null>(null)
const countdownMinutes = ref(preferences.value.countdown_minutes)
const tasks = ref<DayTask[]>([])
const taskId = ref('')
const taskError = ref('')
const settingsOpen = ref(false)
const draft = ref<Preferences>({ ...preferences.value })
const immersive = ref(false)

watch(
  [today, () => route.query.task],
  async ([date, selected], _, cleanup) => {
    let valid = true
    cleanup(() => {
      valid = false
    })
    if (!date) return
    try {
      const result = await fetchDay(date)
      if (!valid) return
      tasks.value = result.tasks
      taskError.value = ''
      if (typeof selected === 'string' && tasks.value.some(t => t.id === selected)) taskId.value = selected
      else if (!tasks.value.some(t => t.id === taskId.value)) taskId.value = ''
    } catch (e) {
      if (valid) taskError.value = (e as Error).message
    }
  },
  { immediate: true },
)

watch(
  timer,
  value => {
    if (value) mode.value = value.mode
  },
  { immediate: true },
)

const activeMode = computed(() => timer.value?.mode ?? mode.value)
const effectiveMinutes = computed(() => {
  if (mode.value === 'pomodoro') return selectedMinutes.value ?? preferences.value.focus_minutes
  if (mode.value === 'countdown') return Number(countdownMinutes.value) || preferences.value.countdown_minutes
  return 0
})

const seconds = computed(() =>
  timer.value ? timerSeconds.value : mode.value === 'stopwatch' ? 0 : effectiveMinutes.value * 60,
)
const displayTime = computed(() => (timerReady.value ? timerText(seconds.value) : '—:—'))
const boundTaskTitle = computed(() => {
  if (timer.value) return timer.value.task?.title ?? '自由专注'
  return tasks.value.find(t => t.id === taskId.value)?.title ?? '自由专注'
})

function applyPreset(mins: number) {
  if (timer.value) return
  if (mode.value === 'stopwatch') mode.value = 'pomodoro'
  if (mode.value === 'pomodoro') selectedMinutes.value = mins
  else countdownMinutes.value = mins
}

function handleStart() {
  const mins = mode.value === 'stopwatch' ? undefined : effectiveMinutes.value
  void startTimer(mode.value, taskId.value || null, mins)
}

function openSettings() {
  draft.value = { ...preferences.value }
  settingsOpen.value = true
}

async function handleSaveSettings() {
  const updated = await savePreferences(draft.value, '计时设置已更新')
  if (updated) {
    countdownMinutes.value = updated.countdown_minutes
    selectedMinutes.value = null
    settingsOpen.value = false
  }
}
</script>

<template>
  <div class="page timer-page">
    <PageHeader eyebrow="FOCUS STUDIO" title="专注时钟" subtitle="静谧计时、实时环境音与全屏沉浸剧场">
      <button type="button" class="btn tinted pill" @click="immersive = true">
        <Maximize2 :size="15" />沉浸剧场
      </button>
      <button type="button" class="btn secondary pill" @click="openSettings">
        <Settings2 :size="15" />计时偏好
      </button>
    </PageHeader>

    <PageSkeleton v-if="!timerReady" layout="timer" />

    <div v-else class="timer-bento">
      <section class="dial-card glass-card">
        <div class="dial-top">
          <div class="segmented" role="group" aria-label="计时模式">
            <button
              v-for="item in modes"
              :key="item.value"
              type="button"
              :disabled="!!timer || timerBusy"
              :aria-pressed="activeMode === item.value"
              @click="mode = item.value"
            >
              <component :is="item.icon" :size="14" />{{ TIMER_MODE_LABELS[item.value] }}
            </button>
          </div>
          <span class="pill accent">{{ timerStatus }}</span>
        </div>

        <div class="dial-stage">
          <div class="dial-orb">
            <ProgressRing :progress="timerProgress ?? 0" :size="278" :stroke="8.5" ticks />
            <div class="dial-face">
              <strong class="dial-digits tabular" :class="{ long: displayTime.length > 5 }">{{ displayTime }}</strong>
              <span class="dial-sub muted">
                {{
                  timer?.stage === 'offer'
                    ? '本轮已计入专注统计'
                    : timer?.stage === 'break'
                      ? '休息片刻，放松双眼'
                      : boundTaskTitle
                }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="!timer && mode !== 'stopwatch'" class="presets-bar">
          <button
            v-for="preset in TIMER_QUICK_PRESETS"
            :key="preset.minutes"
            type="button"
            class="preset-chip"
            :class="{ active: effectiveMinutes === preset.minutes }"
            @click="applyPreset(preset.minutes)"
          >
            {{ preset.label }}
          </button>
        </div>

        <div class="dial-actions">
          <template v-if="timer?.stage === 'offer'">
            <button type="button" class="btn primary lg pill" :disabled="timerBusy" @click="actTimer('start_break')">
              <Coffee :size="17" />开始休息
            </button>
            <button type="button" class="btn secondary lg pill" :disabled="timerBusy" @click="actTimer('dismiss')">
              <CheckCircle2 :size="16" />跳过休息
            </button>
          </template>
          <template v-else-if="timer">
            <button
              type="button"
              class="btn primary lg pill"
              :disabled="timerBusy"
              @click="actTimer(timer.running_since === null ? 'resume' : 'pause')"
            >
              <Play v-if="timer.running_since === null" :size="17" />
              <Pause v-else :size="17" />
              {{ timer.running_since === null ? '继续计时' : '暂停计时' }}
            </button>
            <button type="button" class="btn secondary lg pill" :disabled="timerBusy" @click="finishTimer">
              <Square :size="15" />{{ timer.stage === 'break' ? '结束休息' : '结束并记录' }}
            </button>
          </template>
          <template v-else>
            <label v-if="mode === 'countdown'" class="countdown-box glass-inset">
              <input v-model.number="countdownMinutes" type="number" min="1" max="720" class="bare-input tabular" />
              <span class="muted">分钟</span>
            </label>
            <button type="button" class="btn primary lg pill start-cta" :disabled="!timerReady || timerBusy" @click="handleStart">
              <Play :size="17" />开始专注
            </button>
          </template>
        </div>
      </section>

      <aside class="timer-side">
        <section class="side-card glass-card">
          <header class="section-title"><Link2 :size="17" /><h2>关联今日任务</h2></header>
          <p class="muted" style="font-size: 12.5px">绑定后，本轮专注时长将自动归类到对应学习分类统计中。</p>
          <select v-if="!timer" v-model="taskId" aria-label="选择要关联的今日任务">
            <option value="">自由专注（不绑定具体任务）</option>
            <option v-for="task in tasks" :key="task.id" :value="task.id">
              {{ (task.override ?? task).start }} · {{ task.title }}
            </option>
          </select>
          <div v-else class="bound-box glass-inset">
            <strong>{{ timer.task?.title ?? '自由专注' }}</strong>
            <small class="tertiary">{{ timer.date }} · 计时进行中已锁定关联</small>
          </div>
          <p v-if="taskError" class="error-text" role="alert">{{ taskError }}</p>
        </section>

        <section class="side-card glass-card">
          <AmbientMixer />
        </section>
      </aside>
    </div>

    <GlassModal v-model="settingsOpen" title="计时偏好设置" :busy="settingsBusy">
      <TimerSettings v-model="draft" :busy="settingsBusy" @save="handleSaveSettings" />
    </GlassModal>

    <ImmersiveTimer
      v-if="immersive"
      :display-time="displayTime"
      :task-title="boundTaskTitle"
      :can-start="timerReady"
      @close="immersive = false"
      @start="handleStart"
    />
  </div>
</template>

<style scoped>
.timer-page {
  max-width: 1120px;
}
.timer-bento {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(300px, 0.9fr);
  gap: 20px;
  align-items: start;
}
.dial-card {
  padding: 24px 26px 28px;
  display: grid;
  gap: 22px;
  background:
    radial-gradient(65% 65% at 50% 42%, var(--accent-soft), transparent 72%),
    var(--surface-glass);
}
.dial-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.dial-stage {
  display: grid;
  place-items: center;
  padding: 12px 0;
}
.dial-orb {
  position: relative;
  display: grid;
  place-items: center;
}
.dial-face {
  position: absolute;
  display: grid;
  justify-items: center;
  gap: 6px;
  text-align: center;
  padding: 0 24px;
  max-width: 230px;
}
.dial-digits {
  font-size: 62px;
  font-weight: 740;
  line-height: 1;
  letter-spacing: -0.04em;
}
.dial-digits.long {
  font-size: 46px;
}
.dial-sub {
  font-size: 12.5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}
.presets-bar {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
}
.preset-chip {
  padding: 6px 13px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border);
  background: var(--surface-subtle);
  color: var(--ink-secondary);
  font-size: 12.5px;
  font-weight: 560;
  transition: background 0.16s, color 0.16s, border-color 0.16s;
}
.preset-chip:hover {
  background: var(--surface-hover);
  color: var(--ink);
}
.preset-chip.active {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent);
  font-weight: 650;
}
.dial-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}
.start-cta {
  min-width: 184px;
}
.countdown-box {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  min-height: 44px;
  border-radius: 14px;
}
.countdown-box input {
  width: 56px;
  border: 0;
  background: transparent;
  font-size: 16px;
  font-weight: 680;
  text-align: center;
  outline: none;
}
.timer-side {
  display: grid;
  gap: 18px;
}
.side-card {
  padding: 20px 22px;
  display: grid;
  gap: 12px;
}
.bound-box {
  padding: 13px 14px;
  display: grid;
  gap: 4px;
}
@media (max-width: 900px) {
  .timer-bento {
    grid-template-columns: 1fr;
    gap: 14px;
  }
}
@media (max-width: 768px) {
  .dial-card {
    padding: 16px 14px 20px;
    gap: 15px;
  }
  .dial-top {
    gap: 8px;
  }
  .dial-top .segmented {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .dial-top .segmented button {
    padding: 0 4px;
  }
  .dial-stage {
    padding: 4px 0;
  }
  .dial-orb :deep(.progress-ring) {
    width: min(210px, 60vw);
    height: min(210px, 60vw);
  }
  .dial-digits {
    font-size: 46px;
  }
  .dial-digits.long {
    font-size: 35px;
  }
  .presets-bar {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 7px;
  }
  .preset-chip {
    padding: 6px 11px;
    font-size: 12px;
    text-align: center;
  }
  .dial-actions {
    width: 100%;
  }
  .start-cta {
    width: auto;
    min-width: 164px;
  }
  .timer-side {
    gap: 14px;
  }
  .side-card {
    padding: 15px 14px;
    gap: 10px;
  }
}
</style>
