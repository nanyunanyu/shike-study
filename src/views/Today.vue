<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import {
  ArrowRight,
  BookMarked,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Flag,
  NotebookPen,
  Play,
  RotateCcw,
  Save,
  Share2,
  Sparkles,
  Timer as TimerIcon,
} from 'lucide-vue-next'
import {
  api,
  currentHHMM,
  duration,
  greetingForHour,
  labelDate,
  learningRevision,
  notify,
  preferences,
  session,
  shiftDate,
  today,
  todayFocusSeconds,
} from '../state'
import { useMotionCue } from '../motion'
import type { Category, Day, DayTask, Milestone, Plan, Review, Statistics, Times } from '../types'
import CheckInCelebration, { chooseCheckInEffect, type CheckInEffect } from '../components/CheckInCelebration.vue'
import TimelineBoard from '../components/TimelineBoard.vue'
import ReviewCard from '../components/ReviewCard.vue'
import ShareCardModal from '../components/ShareCardModal.vue'
import GlassModal from '../components/ui/GlassModal.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageSkeleton from '../components/ui/PageSkeleton.vue'
import ProgressRing from '../components/ui/ProgressRing.vue'

const router = useRouter()
const taskCue = useMotionCue<string>(320)
const checkInCue = useMotionCue<CheckInEffect>(1450)

const selected = ref(today.value)
const day = ref<Day | null>(null)
const error = ref('')
const busy = ref(false)
const review = ref<Review | null>(null)
const reviewDirty = ref(false)
const categories = ref<Category[]>([])
const pinnedMilestones = ref<Milestone[]>([])
const currentStreak = ref(0)

// Time override modal
const timeOpen = ref(false)
const timeTask = ref<DayTask | null>(null)
const timeStart = ref('')
const timeEnd = ref('')
const timeError = ref('')

// Ad-hoc task modal
const adhocOpen = ref(false)
const adhocEditingId = ref<string | null>(null)
const adhocForm = ref({
  title: '',
  start: '14:00',
  end: '',
  category: 'practice',
  note: '',
  estimate: 30 as number | null,
})
const adhocError = ref('')

// Share poster modal
const shareOpen = ref(false)

let serial = 0

const total = computed(() => day.value?.tasks.length ?? 0)
const complete = computed(() => day.value?.tasks.filter(t => t.done).length ?? 0)
const rate = computed(() => (total.value ? complete.value / total.value : 0))
const percent = computed(() => Math.round(rate.value * 100))
const goalSeconds = computed(() => Math.max(60, preferences.value.daily_focus_goal_minutes * 60))
const focusRatio = computed(() => Math.min(1, (day.value?.focus_seconds ?? 0) / goalSeconds.value))
const nextTask = computed(() => day.value?.tasks.find(t => !t.done))
const activeCategories = computed(() => categories.value.filter(c => !c.archived))
const hourNow = computed(() => Number(currentHHMM(session.value?.timezone).slice(0, 2)))
const greeting = computed(() => (selected.value === today.value ? greetingForHour(hourNow.value) : '历史学习档案'))

const sharePayload = computed(() =>
  day.value && session.value
    ? {
        date: day.value.date,
        username: session.value.user.username,
        completed: complete.value,
        total: total.value,
        focusSeconds: day.value.focus_seconds,
        goalMinutes: preferences.value.daily_focus_goal_minutes,
        streak: currentStreak.value,
        checked: !!day.value.checked_at,
        mood: review.value?.mood ?? day.value.review.mood,
        focusScore: review.value?.focus_score ?? day.value.review.focus_score,
        takeaways: review.value?.effective ?? day.value.review.effective,
        reflection: review.value?.reflection || review.value?.adjustment || day.value.review.reflection,
      }
    : null,
)

function setDay(value: Day, resetReview = false) {
  day.value = value
  if (value.date === today.value) todayFocusSeconds.value = value.focus_seconds
  if (resetReview || !reviewDirty.value) {
    review.value = structuredClone(value.review)
    reviewDirty.value = false
  }
}

async function loadMeta() {
  try {
    const [planData, statsData] = await Promise.all([api<Plan>('/plan'), api<Statistics>('/statistics')])
    categories.value = planData.categories
    pinnedMilestones.value = statsData.pinned_milestones ?? []
    currentStreak.value = statsData.streak
  } catch {
    /* non-blocking */
  }
}

async function load(reset = false) {
  if (!selected.value) return
  const sequence = ++serial
  error.value = ''
  if (reset) {
    day.value = null
    reviewDirty.value = false
  }
  try {
    const result = await api<Day>(`/days/${selected.value}`)
    if (sequence === serial) setDay(result, reset)
  } catch (e) {
    if (sequence === serial) error.value = (e as Error).message
  }
}

watch(
  selected,
  () => {
    void load(true)
    void loadMeta()
  },
  { immediate: true },
)

watch(today, (value, old) => {
  if (selected.value === old || !selected.value) selected.value = value
})

watch(learningRevision, () => {
  if (!busy.value) {
    void load()
    void loadMeta()
  }
})

async function mutateDay(suffix: string, payload?: unknown, message?: string, method: 'PUT' | 'POST' | 'DELETE' = 'PUT') {
  if (busy.value || !day.value?.editable) return false
  const dateStr = selected.value
  const sequence = ++serial
  busy.value = true
  try {
    const result = await api<Day>(`/days/${dateStr}${suffix}`, method, payload)
    if (selected.value === dateStr && sequence === serial) setDay(result, suffix === '/review')
    if (message) notify(message)
    return true
  } catch (e) {
    notify((e as Error).message, true)
    return false
  } finally {
    busy.value = false
  }
}

async function toggleTask(task: DayTask) {
  if (busy.value || !day.value?.editable) return
  const prev = task.done
  task.done = !prev
  if (task.done) taskCue.play(task.id)
  const ok = await mutateDay(`/tasks/${task.id}/done`, { done: !prev })
  if (!ok) task.done = prev
}

async function toggleCheckIn() {
  if (busy.value || !day.value?.editable) return
  const undo = !!day.value.checked_at
  const ok = await mutateDay('/check-in', undefined, undo ? '已取消今日打卡' : '今日打卡成功，继续保持节奏！', undo ? 'DELETE' : 'POST')
  if (ok) {
    void loadMeta()
    if (undo) checkInCue.clear()
    else checkInCue.play(chooseCheckInEffect())
  }
}

function openEditTimes(task: DayTask) {
  const active = task.override ?? task
  timeTask.value = task
  timeStart.value = active.start
  timeEnd.value = active.end ?? ''
  timeError.value = ''
  timeOpen.value = true
}

async function saveTimes(reset = false) {
  if (!timeTask.value) return
  const payload: Times = { start: timeStart.value, end: timeEnd.value || null }
  if (!reset && payload.end && payload.end <= payload.start) {
    timeError.value = '结束时间须晚于开始时间'
    return
  }
  if (await mutateDay(`/tasks/${timeTask.value.id}/times`, reset ? null : payload, reset ? '已恢复原时段' : '已调整当天时段')) {
    timeOpen.value = false
  }
}

function openAddAdhoc() {
  adhocEditingId.value = null
  const hhmm = currentHHMM(session.value?.timezone)
  adhocForm.value = {
    title: '',
    start: hhmm,
    end: '',
    category: activeCategories.value[0]?.id ?? 'practice',
    note: '',
    estimate: 30,
  }
  adhocError.value = ''
  adhocOpen.value = true
}

function openEditAdhoc(task: DayTask) {
  adhocEditingId.value = task.id
  adhocForm.value = {
    title: task.title,
    start: (task.override ?? task).start,
    end: (task.override ?? task).end ?? '',
    category: task.category,
    note: task.note,
    estimate: task.estimate,
  }
  adhocError.value = ''
  adhocOpen.value = true
}

async function submitAdhoc() {
  const title = adhocForm.value.title.trim()
  if (!title) {
    adhocError.value = '请输入临时任务名称'
    return
  }
  const end = adhocForm.value.end || null
  if (end && end <= adhocForm.value.start) {
    adhocError.value = '结束时间须晚于开始时间'
    return
  }
  const payload = {
    title,
    start: adhocForm.value.start,
    end,
    category: adhocForm.value.category,
    note: adhocForm.value.note.trim(),
    estimate: adhocForm.value.estimate ? Number(adhocForm.value.estimate) : null,
  }
  const ok = adhocEditingId.value
    ? await mutateDay(`/tasks/${adhocEditingId.value}`, payload, '临时任务已更新', 'PUT')
    : await mutateDay('/tasks', payload, '已添加今日临时任务', 'POST')
  if (ok) adhocOpen.value = false
}

async function removeAdhoc(task: DayTask) {
  await mutateDay(`/tasks/${task.id}`, undefined, '已移除临时任务', 'DELETE')
}

function moveDate(offset: number) {
  selected.value = shiftDate(selected.value, offset)
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
      <!-- Bento Hero Glass Card -->
      <section class="hero-card glass-card">
        <div class="hero-left">
          <div class="hero-badges">
            <span class="pill accent"><Sparkles :size="12" />连续打卡 {{ currentStreak }} 天</span>
            <RouterLink
              v-for="ms in pinnedMilestones"
              :key="ms.id"
              :to="{ name: 'stats' }"
              class="pill milestone-pill"
              :title="ms.note || ms.target_date"
            >
              <Flag :size="12" class="accent-text" />
              <span>{{ ms.title }}</span>
              <strong class="tabular">{{ ms.days_left >= 0 ? `还剩 ${ms.days_left} 天` : `已过 ${-ms.days_left} 天` }}</strong>
            </RouterLink>
          </div>

          <div class="hero-headline">
            <strong class="hero-big tabular">{{ complete }}<span> / {{ total }}</span></strong>
            <span class="muted">项日程任务已完成</span>
          </div>

          <div class="hero-actions">
            <button
              v-if="day.editable"
              type="button"
              class="btn lg pill checkin-btn"
              :class="day.checked_at ? 'tinted' : 'primary'"
              :disabled="busy"
              :title="day.checked_at ? '点击可取消今日打卡' : '完成今日打卡'"
              @click="toggleCheckIn"
            >
              <CheckCircle2 :size="17" />
              <span>{{ day.checked_at ? '今日已打卡' : '完成今日打卡' }}</span>
            </button>
            <span v-else-if="day.checked_at" class="pill success" style="padding: 7px 12px; font-size: 12.5px">
              <CheckCircle2 :size="14" />当日已打卡
            </span>
            <button type="button" class="btn secondary lg pill share-btn" @click="shareOpen = true">
              <Share2 :size="15" />分享海报
            </button>
          </div>
        </div>

        <div class="hero-rings">
          <div class="ring-card glass-inset">
            <div class="ring-visual">
              <ProgressRing :progress="rate" :size="96" :stroke="8" />
              <div class="ring-center">
                <strong class="tabular">{{ total ? `${percent}%` : '—' }}</strong>
                <small class="tertiary">任务率</small>
              </div>
            </div>
          </div>

          <div class="ring-card glass-inset">
            <div class="ring-visual">
              <ProgressRing :progress="focusRatio" :size="96" :stroke="8" tone="secondary" />
              <div class="ring-center">
                <strong class="tabular">{{ Math.round(focusRatio * 100) }}%</strong>
                <small class="tertiary">专注目标</small>
              </div>
            </div>
          </div>
        </div>
        <CheckInCelebration v-if="checkInCue.cue.value" :key="checkInCue.cue.value" :effect="checkInCue.cue.value" />
      </section>

      <!-- Main Split Layout -->
      <div class="today-grid">
        <TimelineBoard
          :tasks="day.tasks"
          :editable="day.editable"
          :is-today="selected === today"
          :busy="busy"
          :just-checked-id="taskCue.cue.value"
          @toggle="toggleTask"
          @edit-times="openEditTimes"
          @edit-adhoc="openEditAdhoc"
          @delete-adhoc="removeAdhoc"
          @focus="focusTask"
          @add-adhoc="openAddAdhoc"
        />

        <aside class="today-aside">
          <!-- Focus Summary Glass Card -->
          <section class="aside-card glass-card">
            <header class="section-head">
              <div class="section-title"><TimerIcon :size="18" /><h2>专注记录</h2></div>
              <span class="pill tabular">{{ day.focus.length }} 次</span>
            </header>

            <div class="focus-metric">
              <strong class="tabular">{{ duration(day.focus_seconds) }}</strong>
              <small class="muted tabular">目标 {{ Math.round(preferences.daily_focus_goal_minutes / 60 * 10) / 10 }} 小时</small>
            </div>

            <div class="goal-bar">
              <span :style="{ width: `${Math.round(focusRatio * 100)}%` }"></span>
            </div>

            <ul v-if="day.focus.length" class="focus-sessions">
              <li v-for="entry in day.focus.slice(0, 6)" :key="entry.id">
                <span class="session-name">{{ entry.task?.title ?? '自由专注' }}</span>
                <strong class="tabular">{{ duration(entry.seconds) }}</strong>
              </li>
            </ul>

            <RouterLink
              v-if="day.editable"
              class="btn tinted full"
              :to="{ name: 'timer', query: nextTask ? { task: nextTask.id } : {} }"
            >
              <Play :size="15" />进入沉浸专注
              <ArrowRight :size="15" style="margin-left: auto" />
            </RouterLink>
          </section>

          <!-- Upgraded Daily Review Glass Card -->
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
              @save="mutateDay('/review', review, '复盘已保存，已收录至复盘手账')"
            />
          </section>
        </aside>
      </div>
    </template>

    <!-- Adjust Time Modal -->
    <GlassModal v-model="timeOpen" title="调整当天时段" :subtitle="timeTask?.title" :busy="busy">
      <form class="form-stack" @submit.prevent="saveTimes()">
        <div class="field-grid">
          <label class="field"><span class="field-label">开始时间</span><input v-model="timeStart" type="time" required /></label>
          <label class="field"><span class="field-label">结束时间</span><input v-model="timeEnd" type="time" /></label>
        </div>
        <p v-if="timeError" class="error-text" role="alert">{{ timeError }}</p>
        <div class="dialog-actions">
          <button v-if="timeTask?.override" type="button" class="btn ghost push-left" :disabled="busy" @click="saveTimes(true)">
            <RotateCcw :size="15" />恢复计划时段
          </button>
          <button type="submit" class="btn primary" :disabled="busy"><Clock3 :size="15" />保存时段</button>
        </div>
      </form>
    </GlassModal>

    <!-- Ad-hoc Task Modal -->
    <GlassModal
      v-model="adhocOpen"
      :title="adhocEditingId ? '编辑今日临时任务' : '添加今日临时任务'"
      subtitle="仅作用于今天，不会改动你的主学习计划模板"
      :busy="busy"
    >
      <form class="form-stack" @submit.prevent="submitAdhoc">
        <label class="field">
          <span class="field-label">任务名称</span>
          <input v-model="adhocForm.title" required maxlength="100" placeholder="例如：整理今天错题本、刷一套真题…" />
        </label>
        <div class="field-grid">
          <label class="field"><span class="field-label">开始时间</span><input v-model="adhocForm.start" type="time" required /></label>
          <label class="field"><span class="field-label">结束时间（选填）</span><input v-model="adhocForm.end" type="time" /></label>
          <label class="field">
            <span class="field-label">分类</span>
            <select v-model="adhocForm.category" required>
              <option v-for="cat in activeCategories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">预计专注（分钟）</span>
            <input v-model.number="adhocForm.estimate" type="number" min="1" max="1440" />
          </label>
        </div>
        <label class="field">
          <span class="field-label">备注</span>
          <textarea v-model="adhocForm.note" rows="2" maxlength="2000" placeholder="可选：补充目标或资料页码" />
        </label>
        <p v-if="adhocError" class="error-text" role="alert">{{ adhocError }}</p>
        <div class="dialog-actions">
          <button type="button" class="btn ghost" :disabled="busy" @click="adhocOpen = false">取消</button>
          <button type="submit" class="btn primary" :disabled="busy"><Save :size="15" />{{ adhocEditingId ? '保存修改' : '添加到今日时间轴' }}</button>
        </div>
      </form>
    </GlassModal>

    <!-- Share Card Modal -->
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

.hero-card {
  position: relative;
  overflow: hidden;
  padding: 26px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 22px;
  background:
    radial-gradient(60% 120% at 100% 0%, var(--accent-soft), transparent 68%),
    var(--surface-glass);
}
.hero-left {
  display: grid;
  gap: 14px;
  min-width: 0;
}
.hero-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.milestone-pill {
  transition: background 0.16s, border-color 0.16s;
}
.milestone-pill:hover {
  background: var(--surface-solid);
  border-color: var(--accent-border);
}
.milestone-pill strong {
  color: var(--accent);
}
.hero-headline {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}
.hero-big {
  font-size: 40px;
  font-weight: 760;
  line-height: 1;
  letter-spacing: -0.04em;
}
.hero-big span {
  font-size: 22px;
  font-weight: 560;
  color: var(--ink-tertiary);
}
.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.hero-rings {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: none;
}
.ring-card {
  padding: 14px;
  border-radius: 20px;
}
.ring-visual {
  position: relative;
  display: grid;
  place-items: center;
}
.ring-center {
  position: absolute;
  text-align: center;
  line-height: 1.15;
}
.ring-center strong {
  display: block;
  font-size: 20px;
  font-weight: 740;
  letter-spacing: -0.03em;
}
.ring-center small {
  display: block;
  margin-top: 2px;
  font-size: 10.5px;
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
.focus-metric {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}
.focus-metric strong {
  font-size: 26px;
  font-weight: 740;
  letter-spacing: -0.03em;
}
.goal-bar {
  height: 7px;
  border-radius: var(--radius-pill);
  background: var(--surface-hover);
  overflow: hidden;
}
.goal-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  transition: width 0.5s var(--ease-spring);
}
.focus-sessions {
  display: grid;
  gap: 6px;
  max-height: 220px;
  overflow-y: auto;
}
.focus-sessions li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 11px;
  border-radius: 11px;
  background: var(--surface-subtle);
  font-size: 12.5px;
}
.session-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--ink-secondary);
}

@media (max-width: 980px) {
  .hero-card {
    flex-direction: column;
    align-items: stretch;
    padding: 20px;
  }
  .hero-rings {
    justify-content: flex-start;
  }
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
  .hero-card {
    padding: 15px 14px;
    gap: 14px;
    margin-bottom: 14px;
  }
  .hero-left {
    gap: 11px;
  }
  .hero-badges {
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: 2px;
  }
  .hero-badges::-webkit-scrollbar {
    display: none;
  }
  .hero-big {
    font-size: 30px;
  }
  .hero-big span {
    font-size: 17px;
  }
  .hero-headline {
    gap: 7px;
    font-size: 12.5px;
  }
  .hero-actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 8px;
  }
  .hero-rings {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .ring-card {
    padding: 10px;
    border-radius: 14px;
    display: grid;
    place-items: center;
  }
  .ring-visual :deep(.progress-ring) {
    width: 68px;
    height: 68px;
  }
  .ring-center strong {
    font-size: 15px;
  }
  .ring-center small {
    font-size: 9.5px;
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
  .focus-metric strong {
    font-size: 21px;
  }
}
</style>
