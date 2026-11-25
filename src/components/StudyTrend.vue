<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'
import { duration, labelDate } from '../state'
import type { CalendarDay } from '../types'

const props = defineProps<{ days: CalendarDay[]; today: string }>()
const headline = useId()
const metric = ref<'seconds' | 'rate'>('seconds')
const activeDate = ref('')

const selected = computed(
  () => props.days.find(day => day.date === activeDate.value) ?? props.days.find(day => day.date === props.today),
)
const timeStep = computed(() => Math.max(15, Math.ceil(Math.max(0, ...props.days.map(day => day.seconds ?? 0)) / 1800) * 15))
const scale = computed(() =>
  metric.value === 'rate' ? ['100%', '50%', '0%'] : [`${timeStep.value * 2}m`, `${timeStep.value}m`, '0'],
)

function height(day: CalendarDay) {
  return metric.value === 'rate' ? (day.rate ?? 0) * 100 : ((day.seconds ?? 0) / (timeStep.value * 120)) * 100
}

function detail(day: CalendarDay) {
  if (day.total === null) return '当日无记录'
  const tasks = day.total === 0 ? '无计划任务' : `完成 ${day.completed}/${day.total}（${Math.round((day.rate ?? 0) * 100)}%）`
  return `${tasks} · 专注 ${duration(day.seconds ?? 0)} · ${day.checked ? '已打卡' : '未打卡'}`
}

watch([() => props.days.length, () => props.today], () => {
  if (!props.days.some(day => day.date === activeDate.value)) activeDate.value = ''
})
</script>

<template>
  <section class="trend-card glass-card" :aria-labelledby="headline">
    <header class="section-head">
      <h2 :id="headline">每日趋势</h2>
      <div class="segmented" role="group" aria-label="趋势指标">
        <button type="button" :aria-pressed="metric === 'seconds'" @click="metric = 'seconds'">专注时长</button>
        <button type="button" :aria-pressed="metric === 'rate'" @click="metric = 'rate'">完成率</button>
      </div>
    </header>

    <div class="trend-chart">
      <div class="trend-scale tabular" aria-hidden="true">
        <span v-for="tick in scale" :key="tick">{{ tick }}</span>
      </div>
      <div class="trend-scroll">
        <div class="trend-bars" :class="{ dense: days.length > 10 }" :style="{ '--days': days.length || 1 }">
          <button
            v-for="(day, index) in days"
            :key="day.date"
            type="button"
            class="bar-col"
            :aria-pressed="day.date === selected?.date"
            :title="`${day.date} · ${detail(day)}`"
            @click="activeDate = day.date"
            @mouseenter="activeDate = day.date"
          >
            <span class="bar-slot">
              <span
                v-if="day[metric] !== null"
                class="bar-fill"
                :class="{ zero: day[metric] === 0 }"
                :style="{ height: `${Math.max(3, height(day))}%` }"
              ></span>
            </span>
            <span class="bar-tick tabular">
              {{ day.date === today ? '今' : days.length <= 7 || index % 3 === 0 ? Number(day.date.slice(-2)) : '' }}
            </span>
          </button>
        </div>
      </div>
    </div>

    <div class="trend-detail glass-inset" role="status">
      <strong v-if="selected">{{ labelDate(selected.date, 'short') }}</strong>
      <span class="muted">{{ selected ? detail(selected) : '暂无数据' }}</span>
    </div>
  </section>
</template>

<style scoped>
.trend-card {
  padding: 20px 22px;
  display: grid;
  gap: 16px;
  min-width: 0;
}
.trend-card h2 {
  font-size: 16px;
  font-weight: 680;
}
.trend-chart {
  --plot-h: 170px;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 8px;
}
.trend-scale {
  height: var(--plot-h);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  text-align: right;
  font-size: 10.5px;
  color: var(--ink-tertiary);
}
.trend-scroll {
  overflow-x: auto;
  min-width: 0;
}
.trend-bars {
  position: relative;
  display: grid;
  grid-template-columns: repeat(var(--days), minmax(0, 1fr));
  gap: 4px;
}
.trend-bars.dense {
  min-width: calc(var(--days) * 22px);
}
.trend-bars::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: var(--plot-h);
  pointer-events: none;
  background: linear-gradient(to bottom, var(--border) 1px, transparent 1px) 0 0 / 100% 50%;
  border-bottom: 1px solid var(--border);
}
.bar-col {
  display: grid;
  grid-template-rows: var(--plot-h) 24px;
  border-radius: 10px;
  transition: background 0.16s;
}
.bar-col:hover,
.bar-col[aria-pressed='true'] {
  background: var(--accent-soft);
}
.bar-slot {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 4px 2px 0;
}
.bar-fill {
  width: 64%;
  max-width: 30px;
  border-radius: 8px 8px 3px 3px;
  background: linear-gradient(180deg, var(--accent-2), var(--accent));
  opacity: 0.72;
  transition: height 0.36s var(--ease-spring), opacity 0.16s;
}
.bar-fill.zero {
  height: 3px !important;
  opacity: 0.28;
}
.bar-col[aria-pressed='true'] .bar-fill:not(.zero) {
  opacity: 1;
  box-shadow: 0 4px 12px -4px var(--accent);
}
.bar-tick {
  align-self: center;
  font-size: 10.5px;
  color: var(--ink-tertiary);
}
.bar-col[aria-pressed='true'] .bar-tick {
  color: var(--accent);
  font-weight: 700;
}
.trend-detail {
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 12.5px;
}
@media (max-width: 768px) {
  .trend-card {
    padding: 15px 14px;
    gap: 12px;
  }
  .trend-card h2 {
    font-size: 15px;
  }
  .trend-chart {
    --plot-h: 136px;
    grid-template-columns: 34px minmax(0, 1fr);
    gap: 6px;
  }
  .trend-detail {
    padding: 9px 11px;
    font-size: 12px;
    gap: 4px 8px;
  }
}
</style>
