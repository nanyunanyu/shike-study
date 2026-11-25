import { computed, ref, watch } from 'vue'
import {
  addAdhocTaskApi,
  checkInDayApi,
  deleteAdhocTaskApi,
  fetchDay,
  saveDayReviewApi,
  toggleTaskDoneApi,
  undoCheckInDayApi,
  updateAdhocTaskApi,
  updateTaskTimesApi,
} from '@/api/days'
import { fetchPlan } from '@/api/plan'
import { fetchStatistics } from '@/api/stats'
import { learningRevision, preferences, today, todayFocusSeconds } from '@/stores/session'
import { notify } from '@/stores/ui'
import type { AdhocTaskPayload, Category, Day, DayTask, Milestone, Review, Times } from '@/types'
import { shiftDate } from '@/utils/date'

export function useTodayDay() {
  const selected = ref(today.value)
  const day = ref<Day | null>(null)
  const error = ref('')
  const busy = ref(false)
  const review = ref<Review | null>(null)
  const reviewDirty = ref(false)
  const categories = ref<Category[]>([])
  const pinnedMilestones = ref<Milestone[]>([])
  const currentStreak = ref(0)

  let serial = 0

  const total = computed(() => day.value?.tasks.length ?? 0)
  const complete = computed(() => day.value?.tasks.filter(t => t.done).length ?? 0)
  const rate = computed(() => (total.value ? complete.value / total.value : 0))
  const percent = computed(() => Math.round(rate.value * 100))
  const goalSeconds = computed(() => Math.max(60, preferences.value.daily_focus_goal_minutes * 60))
  const focusRatio = computed(() => Math.min(1, (day.value?.focus_seconds ?? 0) / goalSeconds.value))
  const nextTask = computed(() => day.value?.tasks.find(t => !t.done))
  const activeCategories = computed(() => categories.value.filter(c => !c.archived))

  function applyDay(value: Day, resetReview = false) {
    day.value = value
    if (value.date === today.value) todayFocusSeconds.value = value.focus_seconds
    if (resetReview || !reviewDirty.value) {
      review.value = structuredClone(value.review)
      reviewDirty.value = false
    }
  }

  async function loadMeta() {
    try {
      const [planData, statsData] = await Promise.all([fetchPlan(), fetchStatistics()])
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
      const result = await fetchDay(selected.value)
      if (sequence === serial) applyDay(result, reset)
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

  async function runDayMutation(action: (dateStr: string) => Promise<Day>, message?: string, resetReview = false) {
    if (busy.value || !day.value?.editable) return false
    const dateStr = selected.value
    const sequence = ++serial
    busy.value = true
    try {
      const result = await action(dateStr)
      if (selected.value === dateStr && sequence === serial) applyDay(result, resetReview)
      if (message) notify(message)
      return true
    } catch (e) {
      notify((e as Error).message, true)
      return false
    } finally {
      busy.value = false
    }
  }

  async function toggleTask(task: DayTask, onChecked?: (id: string) => void) {
    if (busy.value || !day.value?.editable) return
    const prev = task.done
    task.done = !prev
    if (task.done) onChecked?.(task.id)
    const ok = await runDayMutation(dateStr => toggleTaskDoneApi(dateStr, task.id, !prev))
    if (!ok) task.done = prev
  }

  async function toggleCheckIn() {
    if (busy.value || !day.value?.editable) return null
    const undo = !!day.value.checked_at
    const ok = await runDayMutation(
      dateStr => (undo ? undoCheckInDayApi(dateStr) : checkInDayApi(dateStr)),
      undo ? '已取消今日打卡' : '今日打卡成功，继续保持节奏！',
    )
    if (!ok) return null
    void loadMeta()
    return undo ? 'undone' : 'checked'
  }

  function saveTimes(taskId: string, times: Times | null) {
    return runDayMutation(
      dateStr => updateTaskTimesApi(dateStr, taskId, times),
      times === null ? '已恢复原时段' : '已调整当天时段',
    )
  }

  function saveAdhoc(payload: AdhocTaskPayload, editingId: string | null) {
    return runDayMutation(
      dateStr => (editingId ? updateAdhocTaskApi(dateStr, editingId, payload) : addAdhocTaskApi(dateStr, payload)),
      editingId ? '临时任务已更新' : '已添加今日临时任务',
    )
  }

  function removeAdhoc(task: DayTask) {
    return runDayMutation(dateStr => deleteAdhocTaskApi(dateStr, task.id), '已移除临时任务')
  }

  function saveReview() {
    if (!review.value) return Promise.resolve(false)
    const currentReview = review.value
    return runDayMutation(dateStr => saveDayReviewApi(dateStr, currentReview), '复盘已保存，已收录至复盘手账', true)
  }

  function moveDate(offset: number) {
    selected.value = shiftDate(selected.value, offset)
  }

  return {
    selected,
    day,
    error,
    busy,
    review,
    reviewDirty,
    categories,
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
  }
}
