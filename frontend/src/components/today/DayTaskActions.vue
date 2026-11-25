<script setup lang="ts">
import { Pencil, Play, Trash2 } from 'lucide-vue-next'
import type { DayTask } from '@/types'

defineProps<{
  task: DayTask
  focusTitle?: string
}>()

const emit = defineEmits<{
  editTimes: [task: DayTask]
  editAdhoc: [task: DayTask]
  deleteAdhoc: [task: DayTask]
  focus: [task: DayTask]
}>()
</script>

<template>
  <div class="task-actions">
    <button
      type="button"
      class="icon-btn sm"
      :aria-label="task.adhoc ? '编辑临时任务' : '调整当天时段'"
      :title="task.adhoc ? '编辑临时任务' : '调整当天时段'"
      @click="task.adhoc ? emit('editAdhoc', task) : emit('editTimes', task)"
    >
      <Pencil :size="14" />
    </button>
    <button
      type="button"
      class="icon-btn sm accent-btn focus-action-btn"
      data-floating-clock-trigger
      :aria-label="focusTitle ?? '为此任务开启专注'"
      :title="focusTitle ?? '为此任务开启专注'"
      @click="emit('focus', task)"
    >
      <Play :size="13" />
    </button>
    <button
      v-if="task.adhoc"
      type="button"
      class="icon-btn sm danger-ghost"
      aria-label="删除临时任务"
      title="删除临时任务"
      @click="emit('deleteAdhoc', task)"
    >
      <Trash2 :size="14" />
    </button>
  </div>
</template>

<style scoped>
.task-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: none;
}
.focus-action-btn {
  border-radius: var(--radius-pill);
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent);
}
.focus-action-btn:hover:not(:disabled) {
  background: var(--accent-soft-strong);
  color: var(--accent);
}
.focus-action-btn :deep(svg) {
  transform: translateX(0.5px);
}
@media (max-width: 768px) {
  .task-actions {
    gap: 4px;
  }
  .task-actions .icon-btn.sm {
    width: 28px;
    height: 28px;
    border-radius: 8px;
  }
  .task-actions .icon-btn.sm.focus-action-btn {
    border-radius: var(--radius-pill);
  }
}
</style>
