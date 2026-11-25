<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowDownRight, ArrowUpRight, BookMarked, CalendarCheck, Flame, ListChecks, Timer, Trophy } from 'lucide-vue-next'
import { duration } from '../state'
import type { CalendarDay, Statistics } from '../types'
import AchievementGrid from './AchievementGrid.vue'
import CategoryBadge from './ui/CategoryBadge.vue'
import StudyHeatmap from './StudyHeatmap.vue'
import StudyTrend from './StudyTrend.vue'

const props = defineProps<{ data: Statistics; compact?: boolean }>()

const periods = [7, 30] as const
const period = ref<(typeof periods)[number]>(7)
const days = computed(() => props.data.calendar.slice(-period.value))
const previous = computed(() => props.data.calendar.slice(-2 * period.value, -period.value))
const sumSeconds = (rows: CalendarDay[]) => rows.reduce((sum, day) => sum + (day.seconds ?? 0), 0)
const focus = computed(() => sumSeconds(days.value))
const delta = computed(() => focus.value - sumSeconds(previous.value))
const comparison = computed(() => {
  if (!previous.value.some(day => day.total !== null)) return '上期无记录'
  if (delta.value === 0) return '与上期持平'
  return `较上期${delta.value > 0 ? '增加' : '减少'} ${duration(Math.abs(delta.value))}`
})
const completed = computed(() => days.value.reduce((sum, day) => sum + (day.completed ?? 0), 0))
const planned = computed(() => days.value.reduce((sum, day) => sum + (day.total ?? 0), 0))
const checked = computed(() => days.value.filter(day => day.checked).length)
const categories = computed(() =>
  [...props.data.categories].sort((a, b) => b.seconds - a.seconds || b.total - a.total || a.name.localeCompare(b.name, 'zh-CN')),
)
const totalCatSeconds = computed(() => categories.value.reduce((sum, item) => sum + item.seconds, 0))
</script>

<template>
  <div class="report-stack">
    <!-- Period Overview Bento Hero -->
    <section class="overview-card glass-card">
      <header class="section-head">
        <div>
          <h2>周期学习概览</h2>
          <p v-if="days.length" class="tertiary tabular" style="font-size: 12px; margin-top: 2px">
            {{ days[0]!.date }} 至 {{ data.today }}
          </p>
        </div>
        <div class="segmented" role="group" aria-label="统计周期">
          <button v-for="item in periods" :key="item" type="button" :aria-pressed="period === item" @click="period = item">
            最近 {{ item }} 天
          </button>
        </div>
      </header>

      <div class="kpi-grid">
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
          <strong class="kpi-val tabular">{{ checked }}<small class="tertiary"> / {{ period }} 天</small></strong>
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
          <span class="tertiary" style="font-size: 12px">近 30 天</span>
        </header>

        <div v-if="!categories.length" class="empty-box compact">最近 30 天暂无分类记录</div>
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
  gap: 18px;
}
.overview-card h2,
.cat-card h2 {
  font-size: 16px;
  font-weight: 680;
}
.kpi-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) repeat(2, minmax(0, 1fr));
  gap: 12px;
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
    gap: 13px;
  }
  .overview-card h2,
  .cat-card h2 {
    font-size: 15px;
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
