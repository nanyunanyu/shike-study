<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowDownRight, ArrowUpRight, BookMarked, CalendarCheck, CalendarRange, Flame, ListChecks, Timer, Trophy } from 'lucide-vue-next'
import CategoryBadge from '@/components/ui/CategoryBadge.vue'
import type { CalendarDay, Statistics } from '@/types'
import { duration, shiftDate } from '@/utils/date'
import AchievementGrid from './AchievementGrid.vue'
import StudyHeatmap from './StudyHeatmap.vue'
import StudyTrend from './StudyTrend.vue'

type ReportMode = '7d' | '30d' | 'custom'

const props = defineProps<{
  data: Statistics
  compact?: boolean
  loadRange?: (start: string, end: string) => Promise<Statistics>
}>()

const mode = ref<ReportMode>('7d')
const draftStart = ref('')
const draftEnd = ref('')
const appliedRange = ref<{ start: string; end: string } | null>(null)
const customReport = ref<Statistics | null>(null)
const rangeLoading = ref(false)
const rangeError = ref('')
let rangeSerial = 0

function defaultCustomBounds() {
  const end = props.data.today
  const start = shiftDate(end, -13)
  return { start, end }
}

async function fetchCustomRange(start: string, end: string) {
  rangeError.value = ''
  if (!start || !end) {
    rangeError.value = '请选择完整的开始和结束日期'
    return
  }
  if (start > end) {
    rangeError.value = '结束日期不能早于开始日期'
    return
  }
  if (end > props.data.today) {
    rangeError.value = '结束日期不能晚于今天'
    return
  }
  appliedRange.value = { start, end }
  if (!props.loadRange) return
  const token = ++rangeSerial
  rangeLoading.value = true
  try {
    const result = await props.loadRange(start, end)
    if (token === rangeSerial) customReport.value = result
  } catch (e) {
    if (token === rangeSerial) rangeError.value = (e as Error).message
  } finally {
    if (token === rangeSerial) rangeLoading.value = false
  }
}

function selectMode(next: ReportMode) {
  mode.value = next
  rangeError.value = ''
  if (next === 'custom' && !appliedRange.value) {
    const bounds = defaultCustomBounds()
    draftStart.value = bounds.start
    draftEnd.value = bounds.end
    void fetchCustomRange(bounds.start, bounds.end)
  }
}

function applyCustomRange() {
  void fetchCustomRange(draftStart.value, draftEnd.value)
}

function pickQuickRange(preset: 'week' | 'month' | '90d') {
  const end = props.data.today
  let start = end
  if (preset === 'week') {
    const dayOfWeek = (new Date(`${end}T00:00:00Z`).getUTCDay() + 6) % 7
    start = shiftDate(end, -dayOfWeek)
  } else if (preset === 'month') {
    start = `${end.slice(0, 8)}01`
  } else {
    start = shiftDate(end, -89)
  }
  draftStart.value = start
  draftEnd.value = end
  void fetchCustomRange(start, end)
}

watch(
  () => props.data,
  () => {
    if (mode.value === 'custom' && appliedRange.value && props.loadRange) {
      void fetchCustomRange(appliedRange.value.start, appliedRange.value.end)
    }
  },
)

const customFallback = computed(() => {
  if (!appliedRange.value) return null
  const { start, end } = appliedRange.value
  const slice = props.data.calendar.filter(day => day.date >= start && day.date <= end)
  return { days: slice, previous_seconds: 0, has_previous: false }
})

const periodDays = computed(() => (mode.value === '7d' ? 7 : 30))

const days = computed<CalendarDay[]>(() => {
  if (mode.value === 'custom') {
    return customReport.value?.custom_range?.days ?? customFallback.value?.days ?? []
  }
  return props.data.calendar.slice(-periodDays.value)
})

const previous = computed(() => props.data.calendar.slice(-2 * periodDays.value, -periodDays.value))
const sumSeconds = (rows: CalendarDay[]) => rows.reduce((sum, day) => sum + (day.seconds ?? 0), 0)
const focus = computed(() => sumSeconds(days.value))

const delta = computed(() => {
  if (mode.value === 'custom') {
    const cr = customReport.value?.custom_range
    return cr ? focus.value - cr.previous_seconds : 0
  }
  return focus.value - sumSeconds(previous.value)
})

const comparison = computed(() => {
  if (mode.value === 'custom') {
    const cr = customReport.value?.custom_range
    if (!cr || !cr.has_previous) return '上期无记录'
    if (delta.value === 0) return '与上期持平'
    return `较上期${delta.value > 0 ? '增加' : '减少'} ${duration(Math.abs(delta.value))}`
  }
  if (!previous.value.some(day => day.total !== null)) return '上期无记录'
  if (delta.value === 0) return '与上期持平'
  return `较上期${delta.value > 0 ? '增加' : '减少'} ${duration(Math.abs(delta.value))}`
})

const completed = computed(() => days.value.reduce((sum, day) => sum + (day.completed ?? 0), 0))
const planned = computed(() => days.value.reduce((sum, day) => sum + (day.total ?? 0), 0))
const checked = computed(() => days.value.filter(day => day.checked).length)

const rangeText = computed(() =>
  days.value.length ? `${days.value[0]!.date} 至 ${days.value[days.value.length - 1]!.date}` : '',
)

const activeCategories = computed(() =>
  mode.value === 'custom' && customReport.value ? customReport.value.categories : props.data.categories,
)

const categories = computed(() =>
  [...activeCategories.value].sort((a, b) => b.seconds - a.seconds || b.total - a.total || a.name.localeCompare(b.name, 'zh-CN')),
)
const totalCatSeconds = computed(() => categories.value.reduce((sum, item) => sum + item.seconds, 0))
const categoryRangeLabel = computed(() =>
  mode.value === 'custom' && appliedRange.value ? `${appliedRange.value.start} ~ ${appliedRange.value.end}` : '近 30 天',
)
</script>

<template>
  <div class="report-stack">
    <!-- Period Overview Bento Hero -->
    <section class="overview-card glass-card">
      <header class="section-head overview-head">
        <div>
          <h2>周期学习概览</h2>
          <p v-if="days.length" class="tertiary tabular" style="font-size: 12px; margin-top: 2px">
            {{ rangeText }} · 共 {{ days.length }} 天
          </p>
        </div>
        <div class="segmented" role="group" aria-label="统计周期">
          <button type="button" :aria-pressed="mode === '7d'" @click="selectMode('7d')">最近 7 天</button>
          <button type="button" :aria-pressed="mode === '30d'" @click="selectMode('30d')">最近 30 天</button>
          <button type="button" :aria-pressed="mode === 'custom'" @click="selectMode('custom')">
            <CalendarRange :size="13" />自定义
          </button>
        </div>
      </header>

      <form v-if="mode === 'custom'" class="custom-range-bar glass-inset" @submit.prevent="applyCustomRange">
        <div class="range-inputs">
          <label class="range-field">
            <span class="tertiary">开始</span>
            <input v-model="draftStart" type="date" :max="draftEnd || data.today" required aria-label="开始日期" />
          </label>
          <span class="range-sep tertiary">至</span>
          <label class="range-field">
            <span class="tertiary">结束</span>
            <input v-model="draftEnd" type="date" :min="draftStart" :max="data.today" required aria-label="结束日期" />
          </label>
        </div>
        <div class="range-actions">
          <div class="range-presets">
            <button type="button" class="btn ghost sm" :disabled="rangeLoading" @click="pickQuickRange('week')">本周</button>
            <button type="button" class="btn ghost sm" :disabled="rangeLoading" @click="pickQuickRange('month')">本月</button>
            <button type="button" class="btn ghost sm" :disabled="rangeLoading" @click="pickQuickRange('90d')">近 90 天</button>
          </div>
          <button type="submit" class="btn tinted sm pill" :disabled="rangeLoading">
            {{ rangeLoading ? '查询中…' : '应用' }}
          </button>
        </div>
        <p v-if="rangeError" class="error-text range-err" role="alert">{{ rangeError }}</p>
      </form>

      <div class="kpi-grid" :class="{ 'is-loading': rangeLoading }">
        <div class="kpi-tile glass-inset primary-kpi">
          <span class="kpi-label"><Timer :size="15" class="accent-text" />周期专注总时长</span>
          <strong class="kpi-val tabular">{{ duration(focus) }}</strong>
          <span class="kpi-delta" :class="{ up: delta > 0, down: delta < 0 }">
            <ArrowUpRight v-if="delta > 0 && comparison !== '上期无记录'" :size="14" />
            <ArrowDownRight v-else-if="delta < 0 && comparison !== '上期无记录'" :size="14" />
            {{ comparison }}
          </span>
        </div>

        <div class="kpi-tile glass-inset">
          <span class="kpi-label"><ListChecks :size="15" class="accent-text" />任务完成</span>
          <strong class="kpi-val tabular">{{ completed }}<small class="tertiary"> / {{ planned }}</small></strong>
          <span class="tertiary" style="font-size: 12px">
            完成率 {{ planned ? `${Math.round((completed / planned) * 100)}%` : '—' }}
          </span>
        </div>

        <div class="kpi-tile glass-inset">
          <span class="kpi-label"><CalendarCheck :size="15" class="accent-text" />周期打卡</span>
          <strong class="kpi-val tabular">{{ checked }}<small class="tertiary"> / {{ days.length }} 天</small></strong>
          <span class="tertiary" style="font-size: 12px">当前连续 {{ data.streak }} 天</span>
        </div>
      </div>
    </section>

    <!-- Trend + Categories Split -->
    <div class="report-split">
      <StudyTrend :days="days" :today="data.today" />

      <section class="cat-card glass-card">
        <header class="section-head">
          <h2>分类专注分布</h2>
          <span class="tertiary tabular" style="font-size: 12px">{{ categoryRangeLabel }}</span>
        </header>

        <div v-if="!categories.length" class="empty-box compact">{{ categoryRangeLabel }}暂无分类记录</div>
        <ul v-else class="cat-list">
          <li v-for="item in categories" :key="item.id">
            <div class="cat-row-top">
              <CategoryBadge :id="item.id" :name="item.name" />
              <span class="tertiary tabular" style="font-size: 11.5px">
                {{ item.rate === null ? '—' : `${Math.round(item.rate * 100)}% 完成` }}
              </span>
              <strong class="tabular">{{ duration(item.seconds) }}</strong>
            </div>
            <div class="cat-track">
              <span :style="{ width: `${totalCatSeconds ? (100 * item.seconds) / totalCatSeconds : 0}%` }"></span>
            </div>
          </li>
        </ul>
      </section>
    </div>

    <!-- 365-Day Heatmap -->
    <StudyHeatmap :calendar="data.calendar" :today="data.today" />

    <!-- Long-term Summary Pills -->
    <section class="lifetime-strip">
      <div class="glass-card life-tile">
        <span class="kpi-label"><Flame :size="14" class="accent-text" />当前连续</span>
        <strong class="tabular">{{ data.streak }} 天</strong>
      </div>
      <div class="glass-card life-tile">
        <span class="kpi-label"><Trophy :size="14" class="accent-text" />最长连胜</span>
        <strong class="tabular">{{ data.longest_streak ?? data.streak }} 天</strong>
      </div>
      <div class="glass-card life-tile">
        <span class="kpi-label"><CalendarCheck :size="14" class="accent-text" />累计打卡</span>
        <strong class="tabular">{{ data.checkins }} 天</strong>
      </div>
      <div class="glass-card life-tile">
        <span class="kpi-label"><Timer :size="14" class="accent-text" />累计专注</span>
        <strong class="tabular">{{ duration(data.seconds) }}</strong>
      </div>
      <div class="glass-card life-tile">
        <span class="kpi-label"><BookMarked :size="14" class="accent-text" />复盘手账</span>
        <strong class="tabular">{{ data.reviews_count ?? 0 }} 篇</strong>
      </div>
    </section>

    <AchievementGrid v-if="!compact && data.achievements?.length" :achievements="data.achievements" />
  </div>
</template>

<style scoped>
.report-stack {
  display: grid;
  gap: 18px;
  min-width: 0;
}
.overview-card {
  padding: 22px 24px;
  display: grid;
  gap: 16px;
}
.overview-card h2,
.cat-card h2 {
  font-size: 16px;
  font-weight: 680;
}
.custom-range-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px 14px;
  padding: 10px 12px;
  border-radius: 14px;
}
.range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.range-field {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}
.range-field input[type='date'] {
  width: auto;
  min-height: 32px;
  padding: 4px 9px;
  font-size: 12.5px;
  border-radius: 9px;
}
.range-sep {
  font-size: 12px;
}
.range-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-left: auto;
}
.range-presets {
  display: flex;
  align-items: center;
  gap: 2px;
}
.range-err {
  width: 100%;
  font-size: 12px;
}
.kpi-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) repeat(2, minmax(0, 1fr));
  gap: 12px;
  transition: opacity 0.18s;
}
.kpi-grid.is-loading {
  opacity: 0.65;
}
.kpi-tile {
  padding: 16px 18px;
  display: grid;
  gap: 6px;
  border-radius: 16px;
}
.primary-kpi {
  background:
    radial-gradient(80% 100% at 100% 0%, var(--accent-soft), transparent 72%),
    var(--surface-subtle);
  border-color: var(--accent-border);
}
.kpi-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 590;
  color: var(--ink-secondary);
}
.kpi-val {
  font-size: 30px;
  font-weight: 760;
  line-height: 1.1;
  letter-spacing: -0.035em;
}
.kpi-val small {
  font-size: 15px;
  font-weight: 560;
}
.kpi-delta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 590;
  color: var(--ink-secondary);
}
.kpi-delta.up {
  color: var(--success);
}
.kpi-delta.down {
  color: var(--warning);
}

.report-split {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(0, 1fr);
  gap: 18px;
}
.cat-card {
  padding: 20px 22px;
  display: grid;
  gap: 16px;
  align-content: start;
}
.cat-list {
  display: grid;
  gap: 13px;
}
.cat-row-top {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12.5px;
}
.cat-track {
  height: 6px;
  border-radius: var(--radius-pill);
  background: var(--surface-subtle);
  overflow: hidden;
}
.cat-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
}

.lifetime-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) minmax(156px, 1.4fr) minmax(0, 1fr);
  gap: 12px;
}
.life-tile {
  padding: 15px 16px;
  display: grid;
  gap: 6px;
}
.life-tile strong {
  font-size: clamp(16px, 1.45vw, 20px);
  font-weight: 730;
  letter-spacing: -0.025em;
  white-space: nowrap;
}

@media (max-width: 960px) {
  .report-split {
    grid-template-columns: 1fr;
  }
  .lifetime-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 768px) {
  .report-stack {
    gap: 14px;
  }
  .overview-card,
  .cat-card {
    padding: 15px 14px;
    gap: 12px;
  }
  .overview-card h2,
  .cat-card h2 {
    font-size: 15px;
  }
  .custom-range-bar {
    padding: 9px 10px;
    gap: 8px;
  }
  .range-inputs {
    width: 100%;
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
    gap: 6px;
  }
  .range-field {
    min-width: 0;
  }
  .range-field span {
    display: none;
  }
  .range-field input[type='date'] {
    width: 100%;
    min-width: 0;
    padding: 4px 7px;
    font-size: 12px;
  }
  .range-actions {
    width: 100%;
    margin-left: 0;
    justify-content: space-between;
  }
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 9px;
  }
  .primary-kpi {
    grid-column: 1 / -1;
  }
  .kpi-tile {
    padding: 13px 14px;
    gap: 4px;
    border-radius: 14px;
  }
  .kpi-val {
    font-size: 22px;
  }
  .primary-kpi .kpi-val {
    font-size: 26px;
  }
  .report-split {
    gap: 14px;
  }
  .lifetime-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 9px;
  }
  .life-tile {
    padding: 13px 14px;
    gap: 4px;
  }
  .life-tile:nth-child(4) {
    grid-column: 1 / -1;
    order: -1;
  }
  .life-tile strong {
    font-size: 18px;
  }
}
</style>
