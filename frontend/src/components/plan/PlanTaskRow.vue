<script setup lang="ts">
import { ArrowDown, ArrowUp, GripVertical, Pencil } from 'lucide-vue-next'
import CategoryBadge from '@/components/ui/CategoryBadge.vue'
import type { Category, Task } from '@/types'

defineProps<{
  item: Task
  index: number
  total: number
  category?: Category
  dropTarget: boolean
  dropAfter: boolean
  dragSource: boolean
}>()

const emit = defineEmits<{
  dragStart: [event: PointerEvent, id: string]
  dragMove: [event: PointerEvent]
  dragEnd: [event: PointerEvent]
  moveUp: []
  moveDown: []
  edit: []
}>()
</script>

<template>
  <div
    :data-plan-task="item.id"
    class="plan-item"
    :class="{
      'drop-target': dropTarget,
      'drop-after': dropAfter,
      'drag-source': dragSource,
    }"
  >
    <span
      class="drag-handle"
      title="按住拖动排序"
      @pointerdown="emit('dragStart', $event, item.id)"
      @pointermove="emit('dragMove', $event)"
      @pointerup="emit('dragEnd', $event)"
      @pointercancel="emit('dragEnd', $event)"
      @lostpointercapture="emit('dragEnd', $event)"
      @contextmenu.prevent
    >
      <GripVertical :size="16" />
    </span>

    <div class="plan-time tabular">
      <time>{{ item.start }}</time>
      <small v-if="item.end" class="tertiary">{{ item.end }}</small>
    </div>

    <div class="plan-title-col">
      <strong>{{ item.title }}</strong>
      <small v-if="item.note" class="muted">{{ item.note }}</small>
    </div>

    <div class="plan-meta-col">
      <CategoryBadge v-if="category && !category.archived" :id="item.category" :name="category.name" />
      <span v-else class="pill danger">分类已归档</span>
      <span v-if="item.estimate" class="tertiary tabular est-label">{{ item.estimate }} 分钟</span>
    </div>

    <div class="plan-ops">
      <button type="button" class="icon-btn sm" :disabled="index === 0" title="上移" @click="emit('moveUp')">
        <ArrowUp :size="14" />
      </button>
      <button type="button" class="icon-btn sm" :disabled="index === total - 1" title="下移" @click="emit('moveDown')">
        <ArrowDown :size="14" />
      </button>
      <button type="button" class="icon-btn sm" title="编辑" @click="emit('edit')">
        <Pencil :size="14" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.plan-item {
  display: grid;
  grid-template-columns: 28px 66px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: 15px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  transition: background 0.16s, border-color 0.16s, box-shadow 0.16s;
}
.plan-item:hover {
  background: var(--surface-solid);
  border-color: var(--border-strong);
}
.plan-item.drop-target {
  background: var(--accent-soft);
  box-shadow: inset 0 2.5px 0 var(--accent);
}
.plan-item.drop-target.drop-after {
  box-shadow: inset 0 -2.5px 0 var(--accent);
}
.plan-item.drag-source {
  opacity: 0.35;
}
.drag-handle {
  display: grid;
  place-items: center;
  height: 36px;
  color: var(--ink-tertiary);
  cursor: grab;
  touch-action: none;
  user-select: none;
}
.plan-time {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}
.plan-time time {
  font-size: 13px;
  font-weight: 660;
}
.plan-time small {
  font-size: 11px;
}
.plan-title-col {
  min-width: 0;
  display: grid;
  gap: 2px;
}
.plan-title-col strong {
  font-size: 13.5px;
  font-weight: 600;
  overflow-wrap: anywhere;
}
.plan-meta-col {
  display: flex;
  align-items: center;
  gap: 8px;
}
.est-label {
  font-size: 11.5px;
  min-width: 52px;
  text-align: right;
}
.plan-ops {
  display: flex;
  align-items: center;
  gap: 2px;
}

@media (max-width: 768px) {
  .plan-item {
    grid-template-columns: 18px 40px minmax(0, 1fr) auto;
    grid-template-rows: auto auto;
    gap: 4px 8px;
    padding: 8px 10px;
    border-radius: 12px;
  }
  .drag-handle {
    grid-column: 1;
    grid-row: 1 / span 2;
    height: auto;
    min-height: 36px;
    align-self: center;
  }
  .plan-time {
    grid-column: 2;
    grid-row: 1 / span 2;
    align-self: center;
    line-height: 1.2;
  }
  .plan-time time {
    font-size: 12px;
  }
  .plan-time small {
    font-size: 10.5px;
  }
  .plan-title-col {
    grid-column: 3 / 5;
    grid-row: 1;
    gap: 1px;
  }
  .plan-title-col strong {
    font-size: 13px;
    line-height: 1.35;
  }
  .plan-title-col small {
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .plan-meta-col {
    grid-column: 3;
    grid-row: 2;
    min-width: 0;
    gap: 6px;
    flex-wrap: nowrap;
    overflow: hidden;
  }
  .est-label {
    min-width: 0;
    text-align: left;
    font-size: 11px;
    white-space: nowrap;
  }
  .plan-ops {
    grid-column: 4;
    grid-row: 2;
    justify-self: end;
    gap: 2px;
  }
  .plan-ops .icon-btn.sm {
    width: 26px;
    height: 26px;
    border-radius: 7px;
  }
}
</style>
