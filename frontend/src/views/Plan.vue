<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { FolderCog, History, ListChecks, Plus, RotateCcw, Save } from 'lucide-vue-next'
import { fetchPlan, savePlanApi } from '@/api/plan'
import PlanCategoriesModal from '@/components/plan/PlanCategoriesModal.vue'
import PlanDefaultModal from '@/components/plan/PlanDefaultModal.vue'
import PlanHistoryModal from '@/components/plan/PlanHistoryModal.vue'
import PlanTaskModal from '@/components/plan/PlanTaskModal.vue'
import PlanTaskRow from '@/components/plan/PlanTaskRow.vue'
import GlassModal from '@/components/ui/GlassModal.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PageSkeleton from '@/components/ui/PageSkeleton.vue'
import { useDragSort } from '@/composables/useDragSort'
import { useUnsavedGuard } from '@/composables/useUnsavedGuard'
import { notify } from '@/stores/ui'
import type { Category, Plan, Snapshot, Task } from '@/types'

const plan = ref<Plan | null>(null)
const tasks = ref<Task[]>([])
const busy = ref(false)
const loadError = ref('')

const taskModalOpen = ref(false)
const editingTask = ref<Task | null>(null)
const historyOpen = ref(false)
const defaultOpen = ref(false)
const categoriesOpen = ref(false)

const activeCategories = computed(() => plan.value?.categories.filter(c => !c.archived) ?? [])
const categoryMap = computed(() => new Map(plan.value?.categories.map(c => [c.id, c]) ?? []))
const baseTasks = computed(() => plan.value?.current.tasks.map(stripSnapshot) ?? [])
const dirty = computed(() => JSON.stringify(baseTasks.value) !== JSON.stringify(tasks.value))
const isEditingExisting = computed(() => tasks.value.some(t => t.id === editingTask.value?.id))

function stripSnapshot({ category_name: _name, ...plain }: Snapshot): Task {
  return plain
}

function move(from: number, to: number) {
  if (to < 0 || from < 0 || to >= tasks.value.length || from === to) return
  const [item] = tasks.value.splice(from, 1)
  tasks.value.splice(to, 0, item!)
}

const { dragged, hover, dragIndex, startDrag, trackDrag, finishDrag, clearDrag } = useDragSort(tasks, {
  itemAttr: 'data-plan-task',
  datasetKey: 'planTask',
  ghostClass: 'plan-drag-ghost',
  onMove: move,
})

const { leaveOpen, resolveLeave } = useUnsavedGuard(dirty, clearDrag)

async function load() {
  loadError.value = ''
  try {
    const data = await fetchPlan()
    plan.value = data
    tasks.value = data.current.tasks.map(stripSnapshot)
  } catch (e) {
    loadError.value = (e as Error).message
  }
}

onMounted(() => void load())

function openTaskModal(item?: Task) {
  editingTask.value = item
    ? { ...item }
    : {
        id: crypto.randomUUID(),
        title: '',
        start: '08:00',
        end: null,
        category: activeCategories.value[0]?.id ?? 'lecture',
        note: '',
        estimate: null,
      }
  taskModalOpen.value = true
}

function upsertTask(item: Task) {
  const index = tasks.value.findIndex(t => t.id === item.id)
  if (index === -1) tasks.value.push(item)
  else tasks.value[index] = item
}

function removeTask(id: string) {
  tasks.value = tasks.value.filter(t => t.id !== id)
}

function applyDraft(rows: Snapshot[]) {
  tasks.value = rows.map(stripSnapshot)
  notify('已载入草稿，点击右上角「保存计划」生效')
}

function updateCategories(updated: Category[]) {
  if (plan.value) plan.value.categories = updated
}

async function save() {
  if (!plan.value || busy.value) return
  busy.value = true
  try {
    const result = await savePlanApi(plan.value.current.id, tasks.value)
    plan.value = result
    tasks.value = result.current.tasks.map(stripSnapshot)
    notify('学习计划已保存，今天起立即生效（当日临时任务已保留）')
  } catch (e) {
    notify((e as Error).message, true)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page plan-page">
    <PageHeader
      eyebrow="SCHEDULE BLUEPRINT"
      title="学习计划"
      :subtitle="plan ? `共 ${tasks.length} 项循环日程 · 当前版本 ${plan.current.date}` : '编排每日学习蓝图'"
    >
      <span v-if="dirty" class="pill warning">有未保存更改</span>
      <button type="button" class="btn primary pill" :disabled="!dirty || busy" @click="save">
        <Save :size="15" />保存计划
      </button>
    </PageHeader>

    <p v-if="loadError" class="error-text" role="alert">
      {{ loadError }} <button type="button" class="btn ghost sm" @click="load">重试</button>
    </p>
    <PageSkeleton v-else-if="!plan" layout="plan" />

    <section v-else class="plan-card glass-card">
      <div class="plan-toolbar">
        <button type="button" class="btn tinted pill" @click="openTaskModal()">
          <Plus :size="15" />新增任务
        </button>
        <div class="plan-toolbar-right">
          <button type="button" class="btn ghost sm" @click="categoriesOpen = true"><FolderCog :size="15" />分类管理</button>
          <button type="button" class="btn ghost sm" @click="historyOpen = true"><History :size="15" />历史版本</button>
          <button type="button" class="btn ghost sm" @click="defaultOpen = true"><RotateCcw :size="15" />恢复默认</button>
        </div>
      </div>

      <div v-if="!tasks.length" class="empty-box">
        <ListChecks :size="26" class="tertiary" />
        <h3>暂无计划任务</h3>
        <button type="button" class="btn secondary" @click="openTaskModal()"><Plus :size="15" />创建第一项日程</button>
      </div>

      <TransitionGroup v-else name="reorder" tag="div" class="plan-list">
        <PlanTaskRow
          v-for="(item, index) in tasks"
          :key="item.id"
          :item="item"
          :index="index"
          :total="tasks.length"
          :category="categoryMap.get(item.category)"
          :drop-target="hover === item.id && dragged !== item.id"
          :drop-after="hover === item.id && dragIndex < index"
          :drag-source="dragged === item.id"
          @drag-start="startDrag"
          @drag-move="trackDrag"
          @drag-end="finishDrag"
          @move-up="move(index, index - 1)"
          @move-down="move(index, index + 1)"
          @edit="openTaskModal(item)"
        />
      </TransitionGroup>
    </section>

    <PlanTaskModal
      v-model="taskModalOpen"
      :task="editingTask"
      :editing="isEditingExisting"
      :active-categories="activeCategories"
      :busy="busy"
      @save="upsertTask"
      @remove="removeTask"
    />

    <PlanHistoryModal
      v-if="plan"
      v-model="historyOpen"
      :history="plan.history"
      :current-id="plan.current.id"
      @apply="applyDraft"
    />

    <PlanDefaultModal v-if="plan" v-model="defaultOpen" :busy="busy" @confirm="applyDraft(plan.defaults)" />

    <PlanCategoriesModal
      v-if="plan"
      v-model="categoriesOpen"
      :categories="plan.categories"
      @saved="updateCategories"
    />

    <GlassModal :model-value="leaveOpen" title="计划尚未保存" @update:model-value="value => { if (!value) resolveLeave(false) }">
      <div class="form-stack">
        <p class="muted">当前计划草稿有未保存的调整，离开页面后本次修改将会丢失。</p>
        <div class="dialog-actions">
          <button type="button" class="btn secondary" @click="resolveLeave(false)">继续编辑</button>
          <button type="button" class="btn danger" @click="resolveLeave(true)">放弃修改并离开</button>
        </div>
      </div>
    </GlassModal>
  </div>
</template>

<style scoped>
.plan-card {
  padding: 20px 22px 24px;
  display: grid;
  gap: 16px;
}
.plan-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}
.plan-toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.plan-list {
  display: grid;
  gap: 8px;
}
.reorder-move {
  transition: transform 0.25s var(--ease-spring);
}

:global(.plan-drag-ghost) {
  position: fixed;
  z-index: 200;
  top: 0;
  left: 0;
  pointer-events: none;
  background: var(--surface-glass-strong) !important;
  backdrop-filter: blur(20px);
  border: 1px solid var(--accent-border) !important;
  box-shadow: var(--shadow-float);
  border-radius: 15px;
}

@media (max-width: 768px) {
  .plan-page :deep(.page-header-actions) {
    justify-content: flex-start;
  }
  .plan-card {
    padding: 12px 10px;
    gap: 10px;
  }
  .plan-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }
  .plan-toolbar > .btn {
    width: auto;
    min-height: 32px;
    padding: 0 12px;
    font-size: 12.5px;
  }
  .plan-toolbar-right {
    width: auto;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 5px;
  }
  .plan-toolbar-right .btn {
    padding: 0 9px;
    min-height: 30px;
    font-size: 12px;
    background: var(--surface-subtle);
    border: 1px solid var(--border);
  }
  .plan-list {
    gap: 6px;
  }
}
</style>
