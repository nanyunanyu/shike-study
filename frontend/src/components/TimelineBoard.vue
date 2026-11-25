<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  Check,
  ChevronDown,
  Clock3,
  LayoutList,
  ListChecks,
  Navigation,
  Pencil,
  Play,
  Plus,
  Sparkles,
  Trash2,
} from 'lucide-vue-next'
import { currentHHMM, session } from '../state'
import type { DayTask } from '../types'
import CategoryBadge from './ui/CategoryBadge.vue'

const props = defineProps<{
  tasks: DayTask[]
  editable: boolean
  isToday: boolean
  busy: boolean
  justCheckedId: string | null
}>()

const emit = defineEmits<{
  toggle: [task: DayTask]
  editTimes: [task: DayTask]
  editAdhoc: [task: DayTask]
  deleteAdhoc: [task: DayTask]
  focus: [task: DayTask]
  addAdhoc: []
}>()

const viewMode = ref<'timeline' | 'list'>('timeline')
const filter = ref<'all' | 'open' | 'done'>('all')
const nowClock = ref(currentHHMM(session.value?.timezone))
const collapsed = ref<Record<string, boolean>>({})

let clockTimer = 0
onMounted(() => {
  clockTimer = window.setInterval(() => {
    nowClock.value = currentHHMM(session.value?.timezone)
  }, 30000)
})
onUnmounted(() => window.clearInterval(clockTimer))

const filteredTasks = computed(() =>
  props.tasks.filter(t => filter.value === 'all' || t.done === (filter.value === 'done')),
)

function taskStart(task: DayTask) {
  return (task.override ?? task).start
}
function taskEnd(task: DayTask) {
  return (task.override ?? task).end
}

function isCurrentSlot(task: DayTask): boolean {
  if (!props.isToday) return false
  const start = taskStart(task)
  const end = taskEnd(task)
  if (end) return nowClock.value >= start && nowClock.value < end
  return nowClock.value >= start && start >= '20:30'
}

const currentTaskId = computed(() => {
  const exact = props.tasks.find(t => isCurrentSlot(t))
  if (exact) return exact.id
  if (!props.isToday) return null
  const upcoming = props.tasks.find(t => !t.done && taskStart(t) >= nowClock.value)
  return upcoming?.id ?? null
})

interface PeriodGroup {
  id: string
  label: string
  range: string
  items: DayTask[]
  doneCount: number
}

const periodDefs = [
  { id: 'early', label: '清晨时光', range: '00:00 – 08:30', match: (s: string) => s < '08:30' },
  { id: 'morning', label: '上午专注', range: '08:30 – 12:00', match: (s: string) => s >= '08:30' && s < '12:00' },
  { id: 'afternoon', label: '午后深耕', range: '12:00 – 18:00', match: (s: string) => s >= '12:00' && s < '18:00' },
  { id: 'evening', label: '晚间沉淀', range: '18:00 – 24:00', match: (s: string) => s >= '18:00' },
]

const groups = computed<PeriodGroup[]>(() =>
  periodDefs
    .map(def => {
      const items = filteredTasks.value.filter(t => def.match(taskStart(t)))
      return {
        id: def.id,
        label: def.label,
        range: def.range,
        items,
        doneCount: items.filter(t => t.done).length,
      }
    })
    .filter(group => group.items.length > 0),
)

function toggleGroup(id: string) {
  collapsed.value[id] = !collapsed.value[id]
}

function scrollToNow() {
  if (!currentTaskId.value) return
  const targetGroup = groups.value.find(g => g.items.some(t => t.id === currentTaskId.value))
  if (targetGroup) collapsed.value[targetGroup.id] = false
  requestAnimationFrame(() => {
    const el = document.querySelector<HTMLElement>(`[data-task-id="${currentTaskId.value}"]`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}
</script>

<template>
  <section class="schedule-card glass-card">
    <header class="schedule-top">
      <div class="schedule-head-row">
        <div class="schedule-title">
          <h2>今日日程</h2>
          <span class="pill tabular">{{ tasks.filter(t => t.done).length }} / {{ tasks.length }}</span>
        </div>
        <div class="schedule-quick-actions">
          <button v-if="isToday && currentTaskId" type="button" class="btn ghost sm" title="定位当前时段" @click="scrollToNow">
            <Navigation :size="13" /><span>当前</span>
          </button>
          <button v-if="editable" type="button" class="btn tinted sm pill" @click="emit('addAdhoc')">
            <Plus :size="14" />临时任务
          </button>
        </div>
      </div>

      <div class="schedule-controls">
        <div class="segmented" role="group" aria-label="视图切换">
          <button type="button" :aria-pressed="viewMode === 'timeline'" @click="viewMode = 'timeline'">
            <Clock3 :size="13" />时间轴
          </button>
          <button type="button" :aria-pressed="viewMode === 'list'" @click="viewMode = 'list'">
            <LayoutList :size="13" />清单
          </button>
        </div>

        <div class="segmented filter-seg" role="group" aria-label="筛选任务">
          <button type="button" :aria-pressed="filter === 'all'" @click="filter = 'all'">全部</button>
          <button type="button" :aria-pressed="filter === 'open'" @click="filter = 'open'">待办</button>
          <button type="button" :aria-pressed="filter === 'done'" @click="filter = 'done'">已完成</button>
        </div>
      </div>
    </header>

    <div v-if="!filteredTasks.length" class="empty-box compact" style="margin: 8px 0">
      <ListChecks :size="22" class="tertiary" />
      <p>{{ tasks.length ? '当前筛选下没有匹配任务' : '今天还没有安排任务' }}</p>
      <button v-if="editable" type="button" class="btn secondary sm" @click="emit('addAdhoc')">
        <Plus :size="14" />添加今日临时任务
      </button>
    </div>

    <!-- Visual Timeline Mode -->
    <div v-else-if="viewMode === 'timeline'" class="timeline-groups">
      <section v-for="group in groups" :key="group.id" class="period-section">
        <button type="button" class="period-header" @click="toggleGroup(group.id)">
          <ChevronDown :size="15" class="period-chevron" :class="{ rotated: collapsed[group.id] }" />
          <strong>{{ group.label }}</strong>
          <span class="tertiary tabular">{{ group.range }}</span>
          <span class="period-count tabular">{{ group.doneCount }}/{{ group.items.length }}</span>
        </button>

        <div v-show="!collapsed[group.id]" class="timeline-rail">
          <article
            v-for="task in group.items"
            :key="task.id"
            :data-task-id="task.id"
            class="timeline-item"
            :class="{
              'is-done': task.done,
              'is-now': isCurrentSlot(task),
              'is-next': !isCurrentSlot(task) && currentTaskId === task.id,
            }"
          >
            <div class="rail-time tabular">
              <time>{{ taskStart(task) }}</time>
              <small v-if="taskEnd(task)" class="tertiary">{{ taskEnd(task) }}</small>
            </div>

            <div class="rail-axis" aria-hidden="true">
              <span class="rail-node"></span>
            </div>

            <div class="task-card">
              <label class="circle-check">
                <input
                  type="checkbox"
                  :checked="task.done"
                  :disabled="!editable || busy"
                  :aria-label="task.title"
                  @change="emit('toggle', task)"
                />
                <span :class="{ popped: task.done && justCheckedId === task.id }">
                  <Check :size="13" :stroke-width="2.8" />
                </span>
              </label>

              <div class="task-body">
                <div class="task-title-line">
                  <strong>{{ task.title }}</strong>
                  <span v-if="isCurrentSlot(task)" class="now-badge"><i></i>进行中</span>
                  <span v-else-if="currentTaskId === task.id && isToday" class="next-badge">即将开始</span>
                  <span v-if="task.adhoc" class="adhoc-badge"><Sparkles :size="10" />临时</span>
                </div>
                <p v-if="task.note" class="task-note muted">{{ task.note }}</p>
                <div class="task-meta-row">
                  <CategoryBadge :id="task.category" :name="task.category_name" />
                  <span v-if="task.estimate" class="tertiary meta-est tabular">约 {{ task.estimate }} 分钟</span>
                  <span v-if="task.override" class="accent-text meta-est">已调时段</span>
                </div>
              </div>

              <div v-if="editable" class="task-actions">
                <button
                  type="button"
                  class="icon-btn sm"
                  :title="task.adhoc ? '编辑临时任务' : '调整当天时段'"
                  @click="task.adhoc ? emit('editAdhoc', task) : emit('editTimes', task)"
                >
                  <Pencil :size="14" />
                </button>
                <button
                  type="button"
                  class="icon-btn sm accent-btn"
                  title="为此任务开启专注"
                  @click="emit('focus', task)"
                >
                  <Play :size="14" />
                </button>
                <button
                  v-if="task.adhoc"
                  type="button"
                  class="icon-btn sm danger-ghost"
                  title="删除临时任务"
                  @click="emit('deleteAdhoc', task)"
                >
                  <Trash2 :size="14" />
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>

    <!-- Clean Card List Mode -->
    <div v-else class="clean-list">
      <article
        v-for="task in filteredTasks"
        :key="task.id"
        :data-task-id="task.id"
        class="list-item"
        :class="{ 'is-done': task.done, 'is-now': isCurrentSlot(task) }"
      >
        <label class="circle-check">
          <input
            type="checkbox"
            :checked="task.done"
            :disabled="!editable || busy"
            :aria-label="task.title"
            @change="emit('toggle', task)"
          />
          <span :class="{ popped: task.done && justCheckedId === task.id }">
            <Check :size="13" :stroke-width="2.8" />
          </span>
        </label>

        <span class="list-time tabular">
          {{ taskStart(task) }}<template v-if="taskEnd(task)"> – {{ taskEnd(task) }}</template>
        </span>

        <div class="list-main">
          <div class="task-title-line">
            <strong>{{ task.title }}</strong>
            <span v-if="task.adhoc" class="adhoc-badge"><Sparkles :size="10" />临时</span>
          </div>
          <small v-if="task.note" class="muted">{{ task.note }}</small>
        </div>

        <CategoryBadge :id="task.category" :name="task.category_name" />

        <div v-if="editable" class="task-actions">
          <button
            type="button"
            class="icon-btn sm"
            :title="task.adhoc ? '编辑临时任务' : '调整当天时段'"
            @click="task.adhoc ? emit('editAdhoc', task) : emit('editTimes', task)"
          >
            <Pencil :size="14" />
          </button>
          <button type="button" class="icon-btn sm accent-btn" title="开始专注" @click="emit('focus', task)">
            <Play :size="14" />
          </button>
          <button
            v-if="task.adhoc"
            type="button"
            class="icon-btn sm danger-ghost"
            title="删除临时任务"
            @click="emit('deleteAdhoc', task)"
          >
            <Trash2 :size="14" />
          </button>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.schedule-card {
  padding: 20px 22px 24px;
  display: grid;
  gap: 18px;
}
.schedule-top {
  display: grid;
  gap: 11px;
}
.schedule-head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.schedule-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.schedule-title h2 {
  font-size: 17px;
  font-weight: 680;
  letter-spacing: -0.02em;
}
.schedule-quick-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.schedule-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}
.timeline-groups {
  display: grid;
  gap: 16px;
}
.period-section {
  display: grid;
  gap: 10px;
}
.period-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 10px;
  background: var(--surface-subtle);
  font-size: 12.5px;
  text-align: left;
  transition: background 0.16s;
}
.period-header:hover {
  background: var(--surface-hover);
}
.period-header strong {
  font-weight: 640;
}
.period-chevron {
  color: var(--ink-tertiary);
  transition: transform 0.2s var(--ease-out);
}
.period-chevron.rotated {
  transform: rotate(-90deg);
}
.period-count {
  margin-left: auto;
  font-size: 11.5px;
  font-weight: 620;
  color: var(--ink-secondary);
}

.timeline-rail {
  display: grid;
  gap: 8px;
  padding-left: 2px;
}
.timeline-item {
  display: grid;
  grid-template-columns: 50px 18px minmax(0, 1fr);
  gap: 10px;
  align-items: stretch;
}
.rail-time {
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  line-height: 1.25;
}
.rail-time time {
  font-size: 12.5px;
  font-weight: 650;
  color: var(--ink);
}
.rail-time small {
  font-size: 11px;
}
.rail-axis {
  position: relative;
  display: flex;
  justify-content: center;
}
.rail-axis::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: -8px;
  width: 1.5px;
  background: var(--border);
}
.timeline-item:last-child .rail-axis::before {
  bottom: 50%;
}
.rail-node {
  position: relative;
  z-index: 1;
  margin-top: 16px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--surface-solid);
  border: 2px solid var(--border-strong);
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
}
.timeline-item.is-done .rail-node {
  background: var(--accent);
  border-color: var(--accent);
}
.timeline-item.is-now .rail-node {
  background: var(--accent);
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-soft-strong);
}

.task-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 15px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  transition: background 0.18s, border-color 0.18s, transform 0.18s;
}
.task-card:hover {
  background: var(--surface-solid);
  border-color: var(--border-strong);
}
.timeline-item.is-done .task-card {
  background: color-mix(in srgb, var(--accent-soft) 45%, transparent);
  border-color: color-mix(in srgb, var(--accent-border) 50%, transparent);
}
.timeline-item.is-now .task-card {
  background: var(--surface-solid);
  border-color: var(--accent-border);
  box-shadow: 0 6px 20px -10px var(--accent);
}

.circle-check {
  position: relative;
  width: 24px;
  height: 24px;
  flex: none;
  margin-top: 1px;
  display: grid;
  place-items: center;
  cursor: pointer;
}
.circle-check input {
  position: absolute;
  inset: -6px;
  opacity: 0;
  cursor: pointer;
  margin: 0;
}
.circle-check span {
  width: 21px;
  height: 21px;
  border-radius: 50%;
  border: 1.8px solid var(--border-strong);
  background: var(--surface-solid);
  color: transparent;
  display: grid;
  place-items: center;
  transition: background 0.18s, border-color 0.18s, color 0.18s, transform 0.18s var(--ease-spring);
}
.circle-check input:checked + span {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--on-accent);
}
.circle-check span.popped {
  animation: check-pop 0.28s var(--ease-spring);
}

.task-body {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 5px;
}
.task-title-line {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
}
.task-title-line strong {
  font-size: 13.5px;
  font-weight: 600;
  line-height: 1.4;
  overflow-wrap: anywhere;
}
.is-done .task-title-line strong {
  color: var(--ink-secondary);
  text-decoration: line-through;
  text-decoration-color: var(--ink-tertiary);
}
.task-note {
  font-size: 12px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
.task-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.meta-est {
  font-size: 11.5px;
}

.now-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: var(--accent);
  color: var(--on-accent);
  font-size: 10.5px;
  font-weight: 660;
}
.now-badge i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse-soft 1.5s infinite;
}
.next-badge {
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 10.5px;
  font-weight: 620;
}
.adhoc-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px;
  border-radius: var(--radius-pill);
  background: var(--warning-soft);
  color: var(--warning);
  font-size: 10.5px;
  font-weight: 630;
}

.task-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: none;
}
.accent-btn:hover:not(:disabled) {
  background: var(--accent-soft);
  color: var(--accent);
}

/* Clean List Mode */
.clean-list {
  display: grid;
  gap: 7px;
}
.list-item {
  display: grid;
  grid-template-columns: auto 96px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: 14px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  transition: background 0.16s, border-color 0.16s;
}
.list-item:hover {
  background: var(--surface-solid);
  border-color: var(--border-strong);
}
.list-item.is-done {
  background: color-mix(in srgb, var(--accent-soft) 40%, transparent);
}
.list-item.is-now {
  border-color: var(--accent-border);
}
.list-time {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-secondary);
}
.list-main {
  min-width: 0;
  display: grid;
  gap: 2px;
}

@media (max-width: 768px) {
  .schedule-card {
    padding: 14px 12px 16px;
    gap: 14px;
  }
  .schedule-title h2 {
    font-size: 15.5px;
  }
  .schedule-controls {
    flex-wrap: nowrap;
    gap: 6px;
  }
  .schedule-controls .segmented {
    flex-shrink: 0;
  }
  .schedule-controls .filter-seg {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .schedule-controls .filter-seg button {
    padding: 0 4px;
  }
  .period-header {
    padding: 5px 8px;
    font-size: 12px;
  }
  .timeline-item {
    grid-template-columns: 36px 12px minmax(0, 1fr);
    gap: 6px;
  }
  .rail-time {
    padding-top: 10px;
  }
  .rail-time time {
    font-size: 11.5px;
  }
  .rail-time small {
    font-size: 10px;
  }
  .rail-node {
    margin-top: 14px;
    width: 8px;
    height: 8px;
  }
  .task-card {
    padding: 10px 10px;
    gap: 8px;
    border-radius: 13px;
  }
  .task-title-line strong {
    font-size: 13px;
  }
  .task-actions .icon-btn.sm {
    width: 28px;
    height: 28px;
  }
  .list-item {
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: 6px 8px;
    padding: 10px;
  }
  .list-time {
    grid-column: 2;
    font-size: 11px;
  }
}
</style>
