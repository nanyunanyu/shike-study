<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { BookMarked, CalendarDays, ChevronLeft, ChevronRight, NotebookPen } from 'lucide-vue-next'
import ReviewCard from '@/components/reviews/ReviewCard.vue'
import ShareCardModal from '@/components/share/ShareCardModal.vue'
import AdhocTaskModal from '@/components/today/AdhocTaskModal.vue'
import TimeOverrideModal from '@/components/today/TimeOverrideModal.vue'
import TimelineBoard from '@/components/today/TimelineBoard.vue'
import TodayFocusCard from '@/components/today/TodayFocusCard.vue'
import TodayHero from '@/components/today/TodayHero.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PageSkeleton from '@/components/ui/PageSkeleton.vue'
import { useMotionCue } from '@/composables/useMotionCue'
import { useTodayDay } from '@/composables/useTodayDay'
import { preferences, session, today } from '@/stores/session'
import { clearCheckInCelebration, triggerCheckInCelebration, updateCheckInCelebrationStreak } from '@/stores/ui'
import type { AdhocTaskPayload, DayTask, Times } from '@/types'
import { resolveStreakMilestone, type CelebrationOrigin } from '@/utils/celebrationEngine'
import { currentHHMM, greetingForHour, labelDate } from '@/utils/date'
import { buildSharePayloadFromDay } from '@/utils/sharePayload'
import { playCheckInChime } from '@/utils/soundscape'

const router = useRouter()
const taskCue = useMotionCue<string>(320)
const checkInPulse = useMotionCue<boolean>(560)

const {
  selected,
  day,
  error,
  busy,
  review,
  reviewDirty,
  activeCategories,
  pinnedMilestones,
  currentStreak,
  total,
  complete,
  rate,
  percent,
  focusRatio,
  nextTask,
  load,
  toggleTask,
  toggleCheckIn,
  saveTimes,
  saveAdhoc,
  removeAdhoc,
  saveReview,
  moveDate,
} = useTodayDay()

const timeOpen = ref(false)
const timeTask = ref<DayTask | null>(null)
const adhocOpen = ref(false)
const adhocEditingTask = ref<DayTask | null>(null)
const shareOpen = ref(false)

const hourNow = computed(() => Number(currentHHMM(session.value?.timezone).slice(0, 2)))
const greeting = computed(() => (selected.value === today.value ? greetingForHour(hourNow.value) : '历史学习档案'))

const sharePayload = computed(() =>
  day.value && session.value
    ? buildSharePayloadFromDay({
        day: day.value,
        username: session.value.user.username,
        goalMinutes: preferences.value.daily_focus_goal_minutes,
        streak: currentStreak.value,
        review: review.value,
      })
    : null,
)

async function handleCheckIn(origin: CelebrationOrigin) {
  const prevStreak = currentStreak.value
  const outcome = await toggleCheckIn()
  if (outcome === 'undone') {
    checkInPulse.clear()
    clearCheckInCelebration()
  } else if (outcome === 'checked') {
    const nextStreak = Math.max(1, prevStreak + 1)
    checkInPulse.play(true)
    playCheckInChime(!!resolveStreakMilestone(nextStreak))
    triggerCheckInCelebration({ origin, streak: nextStreak })
  }
}

watch(currentStreak, streak => {
  if (streak > 0) updateCheckInCelebrationStreak(streak)
})

function openEditTimes(task: DayTask) {
  timeTask.value = task
  timeOpen.value = true
}

async function handleSaveTimes(taskId: string, times: Times | null) {
  if (await saveTimes(taskId, times)) timeOpen.value = false
}

function openAddAdhoc() {
  adhocEditingTask.value = null
  adhocOpen.value = true
}

function openEditAdhoc(task: DayTask) {
  adhocEditingTask.value = task
  adhocOpen.value = true
}

async function handleSubmitAdhoc(payload: AdhocTaskPayload, editingId: string | null) {
  if (await saveAdhoc(payload, editingId)) adhocOpen.value = false
}

function focusTask(task: DayTask) {
  void router.push({ name: 'timer', query: { task: task.id } })
}
</script>

<template>
  <div class="page today-page">
    <PageHeader :eyebrow="greeting" title="今日学习" :subtitle="labelDate(selected)">
      <button v-if="selected !== today" type="button" class="btn tinted sm pill" @click="selected = today">返回今天</button>
      <div class="date-capsule glass-card">
        <button type="button" class="icon-btn sm" aria-label="前一天" @click="moveDate(-1)"><ChevronLeft :size="16" /></button>
        <label class="date-input-wrap">
          <CalendarDays :size="14" class="accent-text" />
          <input
            type="date"
            class="bare-input tabular"
            :value="selected"
            :max="today"
            aria-label="选择学习日期"
            @change="e => { const v = (e.target as HTMLInputElement).value; if (v && v <= today) selected = v; else (e.target as HTMLInputElement).value = selected }"
          />
        </label>
        <button type="button" class="icon-btn sm" :disabled="selected >= today" aria-label="后一天" @click="moveDate(1)">
          <ChevronRight :size="16" />
        </button>
      </div>
    </PageHeader>

    <p v-if="error" class="error-text" role="alert" style="margin-bottom: 16px">
      {{ error }} <button type="button" class="btn ghost sm" @click="load()">重试</button>
    </p>

    <PageSkeleton v-if="!day && !error" layout="today" />

    <div v-else-if="day && !day.editable && !day.exists" class="glass-card empty-day">
      <CalendarDays :size="28" class="tertiary" />
      <h3>{{ labelDate(selected) }} 暂无学习记录</h3>
      <p class="muted">可以切换其他日期查看历史档案，或回到今天继续专注。</p>
      <button type="button" class="btn primary" @click="selected = today">返回今天</button>
    </div>

    <template v-else-if="day">
      <TodayHero
        :complete="complete"
        :total="total"
        :percent="percent"
        :rate="rate"
        :focus-ratio="focusRatio"
        :editable="day.editable"
        :checked="!!day.checked_at"
        :busy="busy"
        :current-streak="currentStreak"
        :pinned-milestones="pinnedMilestones"
        :just-checked="!!checkInPulse.cue.value"
        @check-in="handleCheckIn"
        @share="shareOpen = true"
      />

      <div class="today-grid">
        <TimelineBoard
          :tasks="day.tasks"
          :editable="day.editable"
          :is-today="selected === today"
          :busy="busy"
          :just-checked-id="taskCue.cue.value"
          @toggle="task => toggleTask(task, id => taskCue.play(id))"
          @edit-times="openEditTimes"
          @edit-adhoc="openEditAdhoc"
          @delete-adhoc="removeAdhoc"
          @focus="focusTask"
          @add-adhoc="openAddAdhoc"
        />

        <aside class="today-aside">
          <TodayFocusCard
            :focus="day.focus"
            :focus-seconds="day.focus_seconds"
            :goal-minutes="preferences.daily_focus_goal_minutes"
            :focus-ratio="focusRatio"
            :editable="day.editable"
            :next-task="nextTask"
          />

          <section class="aside-card glass-card" @input="reviewDirty = true" @change="reviewDirty = true">
            <header class="section-head">
              <div class="section-title"><NotebookPen :size="18" /><h2>每日复盘</h2></div>
              <RouterLink :to="{ name: 'reviews' }" class="btn ghost sm">
                <BookMarked :size="14" />手账档案
              </RouterLink>
            </header>
            <ReviewCard
              v-if="review"
              v-model="review"
              :readonly="!day.editable"
              :busy="busy"
              @update:model-value="reviewDirty = true"
              @save="saveReview"
            />
          </section>
        </aside>
      </div>
    </template>

    <TimeOverrideModal v-model="timeOpen" :task="timeTask" :busy="busy" @save="handleSaveTimes" />
    <AdhocTaskModal
      v-model="adhocOpen"
      :editing-task="adhocEditingTask"
      :categories="activeCategories"
      :busy="busy"
      @submit="handleSubmitAdhoc"
    />
    <ShareCardModal v-model="shareOpen" :payload="sharePayload" />
  </div>
</template>

<style scoped>
.date-capsule {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 4px;
  border-radius: var(--radius-pill);
}
.date-input-wrap {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 8px;
}
.date-input-wrap input {
  border: 0;
  background: transparent;
  font-size: 13px;
  font-weight: 590;
  color: var(--ink);
  outline: none;
  cursor: pointer;
}
.empty-day {
  padding: 56px 24px;
  display: grid;
  justify-items: center;
  gap: 12px;
  text-align: center;
}
.today-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.48fr) minmax(300px, 370px);
  align-items: start;
  gap: 20px;
}
.today-aside {
  display: grid;
  gap: 18px;
  min-width: 0;
}
.aside-card {
  padding: 20px;
  display: grid;
  gap: 16px;
}
@media (max-width: 980px) {
  .today-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 768px) {
  .date-capsule {
    flex: 1;
    justify-content: space-between;
    padding: 3px 4px;
  }
  .today-grid {
    gap: 14px;
  }
  .today-aside {
    gap: 14px;
  }
  .aside-card {
    padding: 15px 14px;
    gap: 12px;
  }
}
</style>
