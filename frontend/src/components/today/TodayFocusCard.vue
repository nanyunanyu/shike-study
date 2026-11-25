<script setup lang="ts">
import { ArrowRight, Play, Timer as TimerIcon } from 'lucide-vue-next'
import type { DayTask, Focus } from '@/types'
import { duration } from '@/utils/date'

defineProps<{
  focus: Focus[]
  focusSeconds: number
  goalMinutes: number
  focusRatio: number
  editable: boolean
  nextTask?: DayTask
}>()
</script>

<template>
  <section class="aside-card glass-card">
    <header class="section-head">
      <div class="section-title"><TimerIcon :size="18" /><h2>专注记录</h2></div>
      <span class="pill tabular">{{ focus.length }} 次</span>
    </header>

    <div class="focus-metric">
      <strong class="tabular">{{ duration(focusSeconds) }}</strong>
      <small class="muted tabular">目标 {{ Math.round((goalMinutes / 60) * 10) / 10 }} 小时</small>
    </div>

    <div class="goal-bar">
      <span :style="{ width: `${Math.round(focusRatio * 100)}%` }"></span>
    </div>

    <ul v-if="focus.length" class="focus-sessions">
      <li v-for="entry in focus.slice(0, 6)" :key="entry.id">
        <span class="session-name">{{ entry.task?.title ?? '自由专注' }}</span>
        <strong class="tabular">{{ duration(entry.seconds) }}</strong>
      </li>
    </ul>

    <RouterLink
      v-if="editable"
      class="btn tinted pill focus-cta"
      :to="{ name: 'timer', query: nextTask ? { task: nextTask.id } : {} }"
    >
      <Play :size="15" />进入沉浸专注
      <ArrowRight :size="15" class="focus-cta-arrow" />
    </RouterLink>
  </section>
</template>

<style scoped>
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
.focus-cta {
  width: 100%;
  border-radius: var(--radius-sm);
}
.focus-cta-arrow {
  margin-left: auto;
}
@media (max-width: 768px) {
  .aside-card {
    padding: 15px 14px;
    gap: 12px;
  }
  .focus-metric strong {
    font-size: 21px;
  }
  .focus-cta {
    width: auto;
    justify-self: start;
    border-radius: var(--radius-pill);
    padding: 0 15px;
  }
  .focus-cta-arrow {
    margin-left: 2px;
  }
}
</style>
