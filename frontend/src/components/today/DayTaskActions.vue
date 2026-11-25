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
      :title="task.adhoc ? '编辑临时任务' : '调整当天时段'"
      @click="task.adhoc ? emit('editAdhoc', task) : emit('editTimes', task)"
    >
      <Pencil :size="14" />
    </button>
    <button
      type="button"
      class="icon-btn sm accent-btn"
      :title="focusTitle ?? '为此任务开启专注'"
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
</template>

<style scoped>
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
@media (max-width: 768px) {
  .task-actions .icon-btn.sm {
    width: 26px;
    height: 26px;
    border-radius: 7px;
  }
}
</style>
