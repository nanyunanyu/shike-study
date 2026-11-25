<script setup lang="ts">
import { computed, onMounted, ref, useId } from 'vue'
import { duration } from '../state'
import type { CalendarDay } from '../types'

const props = defineProps<{ calendar: CalendarDay[]; today: string }>()
const headline = useId()
const metric = ref<'rate' | 'seconds'>('rate')
const activeDate = ref('')
const heatScroll = ref<HTMLElement | null>(null)

onMounted(() => {
  if (heatScroll.value) heatScroll.value.scrollLeft = heatScroll.value.scrollWidth - heatScroll.value.clientWidth
})

const monday = computed(() =>
  props.calendar.length ? (new Date(`${props.calendar[0]!.date}T00:00:00Z`).getUTCDay() + 6) % 7 : 0,
)
const cells = computed(() => [...Array.from<null>({ length: monday.value }).fill(null), ...props.calendar])
const weeks = computed(() => Math.max(1, Math.ceil(cells.value.length / 7)))
const months = computed(() =>
  cells.value.flatMap((d, i) =>
    d && d.date.endsWith('-01') ? [{ position: Math.floor(i / 7), label: `${Number(d.date.slice(5, 7))}月` }] : [],
  ),
)
const selected = computed(
  () => props.calendar.find(d => d.date === activeDate.value) ?? props.calendar.find(d => d.date === props.today),
)

function level(d: CalendarDay) {
  if (d[metric.value] === null) return 'none'
  return metric.value === 'rate' ? Math.ceil((d.rate ?? 0) * 4) : Math.min(4, Math.ceil((d.seconds ?? 0) / 1800))
}

function detail(d: CalendarDay) {
  if (d.total === null) return `${d.date} · 暂无记录`
  const tasks = d.rate === null ? '无计划任务' : `完成率 ${Math.round(d.rate * 100)}%`
  return `${d.date} · ${tasks} · 专注 ${duration(d.seconds ?? 0)} · ${d.checked ? '已打卡' : '未打卡'}`
}
</script>

<template>
  <section class="heatmap-card glass-card" :aria-labelledby="headline">
    <header class="section-head">
      <div>
        <h2 :id="headline">学习热力图</h2>
        <p class="tertiary" style="font-size: 12px; margin-top: 2px">近 365 天持续足迹</p>
      </div>
      <div class="segmented" role="group" aria-label="热力图指标">
        <button type="button" :aria-pressed="metric === 'rate'" @click="metric = 'rate'">完成率</button>
        <button type="button" :aria-pressed="metric === 'seconds'" @click="metric = 'seconds'">专注时长</button>
      </div>
    </header>

    <div ref="heatScroll" class="heat-scroll" tabindex="0">
      <div class="heat-inner" :style="{ '--weeks': weeks }">
        <div class="heat-months">
          <span v-for="month in months" :key="month.position" :style="{ gridColumn: month.position + 1 }">
            {{ month.label }}
          </span>
        </div>
        <div class="heat-grid">
          <template v-for="(d, i) in cells" :key="d?.date ?? i">
            <button
              v-if="d"
              type="button"
              class="heat-cell"
              :data-level="level(d)"
              :class="{ checked: d.checked, selected: d.date === selected?.date }"
              :title="detail(d)"
              :aria-label="detail(d)"
              @click="activeDate = d.date"
              @mouseenter="activeDate = d.date"
            ></button>
            <span v-else class="heat-cell" data-level="blank" aria-hidden="true"></span>
          </template>
        </div>
      </div>
    </div>

    <div class="heat-foot">
      <span class="muted tabular">{{ selected ? detail(selected) : `${calendar[0]?.date} 至 ${today}` }}</span>
      <div class="heat-legend tertiary">
        <span>少</span>
        <span class="heat-cell" data-level="none"></span>
        <span class="heat-cell" data-level="1"></span>
        <span class="heat-cell" data-level="2"></span>
        <span class="heat-cell" data-level="3"></span>
        <span class="heat-cell" data-level="4"></span>
        <span>多</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.heatmap-card {
  padding: 20px 22px;
  display: grid;
  gap: 14px;
  min-width: 0;
}
.heatmap-card h2 {
  font-size: 16px;
  font-weight: 680;
}
.heat-scroll {
  overflow-x: auto;
  padding: 2px 2px 6px;
}
.heat-inner {
  min-width: 728px;
  width: 100%;
  padding: 2px 5px 4px 4px;
}
.heat-months,
.heat-grid {
  display: grid;
  grid-template-columns: repeat(var(--weeks), minmax(0, 1fr));
  gap: 3.5px;
}
.heat-months {
  padding-bottom: 6px;
  font-size: 10.5px;
  color: var(--ink-tertiary);
}
.heat-months span {
  white-space: nowrap;
}
.heat-grid {
  grid-template-rows: repeat(7, auto);
  grid-auto-flow: column;
  padding: 2px;
}
.heat-cell {
  display: block;
  aspect-ratio: 1;
  border-radius: 3.5px;
  background: var(--surface-subtle);
  border: 1px solid transparent;
  transition: transform 0.14s, border-color 0.14s, box-shadow 0.14s;
}
.heat-cell:hover {
  transform: scale(1.18);
  position: relative;
  z-index: 2;
}
.heat-cell[data-level='blank'] {
  visibility: hidden;
}
.heat-cell[data-level='none'] {
  background: var(--surface-subtle);
  border-color: var(--border);
}
.heat-cell[data-level='0'] {
  background: color-mix(in srgb, var(--chart) 12%, var(--surface-solid));
}
.heat-cell[data-level='1'] {
  background: color-mix(in srgb, var(--chart) 30%, var(--surface-solid));
}
.heat-cell[data-level='2'] {
  background: color-mix(in srgb, var(--chart) 52%, var(--surface-solid));
}
.heat-cell[data-level='3'] {
  background: color-mix(in srgb, var(--chart) 76%, var(--surface-solid));
}
.heat-cell[data-level='4'] {
  background: var(--chart);
}
.heat-cell.checked {
  border-color: color-mix(in srgb, var(--accent) 55%, transparent);
}
.heat-cell.selected {
  position: relative;
  z-index: 3;
  box-shadow: 0 0 0 1.5px var(--surface-solid), 0 0 0 3.2px var(--accent);
}
.heat-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 12px;
}
.heat-legend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}
.heat-legend .heat-cell {
  width: 11px;
  height: 11px;
}
@media (max-width: 768px) {
  .heatmap-card {
    padding: 15px 14px;
    gap: 11px;
  }
  .heatmap-card h2 {
    font-size: 15px;
  }
  .heat-foot {
    font-size: 11.5px;
    gap: 6px;
  }
}
</style>
