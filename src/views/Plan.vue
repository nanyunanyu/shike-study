<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import {
  ArrowDown,
  ArrowUp,
  FolderCog,
  GripVertical,
  History,
  ListChecks,
  Pencil,
  Plus,
  RotateCcw,
  Save,
  Trash2,
} from 'lucide-vue-next'
import { api, notify, session } from '../state'
import type { Category, Plan, Snapshot, Task } from '../types'
import CategoryBadge from '../components/ui/CategoryBadge.vue'
import GlassModal from '../components/ui/GlassModal.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageSkeleton from '../components/ui/PageSkeleton.vue'

const plan = ref<Plan | null>(null)
const tasks = ref<Task[]>([])
const busy = ref(false)
const loadError = ref('')
const pane = ref<'task' | 'history' | 'default' | 'categories' | null>(null)
const open = computed({
  get: () => pane.value !== null,
  set: value => {
    if (!value) pane.value = null
  },
})
const task = ref<Task | null>(null)
const formError = ref('')
const lastVersion = ref('')
const dragged = ref<string | null>(null)
const hover = ref<string | null>(null)
const leaveOpen = ref(false)
let leaveConfirmation: { promise: Promise<boolean>; resolve: (leave: boolean) => void } | null = null
let drag: {
  id: string
  pointer: number
  handle: HTMLElement
  row: HTMLElement
  startX: number
  startY: number
  offsetX: number
  offsetY: number
  x: number
  y: number
} | null = null
let ghost: HTMLElement | null = null
let scrollFrame = 0

const categories = ref<Category[]>([])
const active = computed(() => plan.value?.categories.filter(c => !c.archived) ?? [])
const info = computed(() => new Map(plan.value?.categories.map(c => [c.id, c]) ?? []))
const base = computed(() => plan.value?.current.tasks.map(strip) ?? [])
const dirty = computed(() => JSON.stringify(base.value) !== JSON.stringify(tasks.value))
const dragIndex = computed(() => tasks.value.findIndex(item => item.id === dragged.value))
const editing = computed(() => tasks.value.some(t => t.id === task.value?.id))
const titles = {
  task: '编辑计划任务',
  history: '历史计划版本',
  default: '恢复默认计划',
  categories: '管理学习分类',
}

const dateTime = (timestamp: number) =>
  new Intl.DateTimeFormat('zh-CN', {
    timeZone: session.value?.timezone,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(timestamp * 1000)

function strip({ category_name: _name, ...plain }: Snapshot): Task {
  return plain
}

async function load() {
  loadError.value = ''
  try {
    const data = await api<Plan>('/plan')
    plan.value = data
    tasks.value = data.current.tasks.map(strip)
  } catch (e) {
    loadError.value = (e as Error).message
  }
}

function pageExit(e: BeforeUnloadEvent) {
  if (dirty.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}

onMounted(() => {
  void load()
  window.addEventListener('beforeunload', pageExit)
  window.addEventListener('keydown', cancelDragOnEscape)
  window.addEventListener('blur', clearDrag)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', pageExit)
  window.removeEventListener('keydown', cancelDragOnEscape)
  window.removeEventListener('blur', clearDrag)
  clearDrag()
  resolveLeave(false)
})

onBeforeRouteLeave(() => {
  clearDrag()
  if (!dirty.value) return true
  if (!leaveConfirmation) {
    let resolve!: (leave: boolean) => void
    const promise = new Promise<boolean>(finish => {
      resolve = finish
    })
    leaveConfirmation = { promise, resolve }
    leaveOpen.value = true
  }
  return leaveConfirmation.promise
})

function resolveLeave(leave: boolean) {
  const confirmation = leaveConfirmation
  leaveConfirmation = null
  leaveOpen.value = false
  confirmation?.resolve(leave)
}

function dialog(value: typeof pane.value) {
  formError.value = ''
  pane.value = value
}

function edit(item?: Task) {
  task.value = item
    ? { ...item }
    : {
        id: crypto.randomUUID(),
        title: '',
        start: '08:00',
        end: null,
        category: active.value[0]?.id ?? 'lecture',
        note: '',
        estimate: null,
      }
  dialog('task')
}

function saveTask() {
  if (!task.value) return
  const item = {
    ...task.value,
    title: task.value.title.trim(),
    end: task.value.end || null,
    estimate: task.value.estimate || null,
  }
  if (!item.title) {
    formError.value = '请输入任务名称'
    return
  }
  if (item.end && item.end <= item.start) {
    formError.value = '结束时间须晚于开始时间'
    return
  }
  const index = tasks.value.findIndex(t => t.id === item.id)
  if (index === -1) tasks.value.push(item)
  else tasks.value[index] = item
  pane.value = null
}

function remove(id: string) {
  tasks.value = tasks.value.filter(t => t.id !== id)
  pane.value = null
}

function move(from: number, to: number) {
  if (to < 0 || from < 0 || to >= tasks.value.length || from === to) return
  const [item] = tasks.value.splice(from, 1)
  tasks.value.splice(to, 0, item)
}

function startDrag(event: PointerEvent, id: string) {
  if (!event.isPrimary || event.button !== 0 || drag) return
  const { pointerId, clientX, clientY } = event
  const handle = event.currentTarget as HTMLElement
  const row = handle.closest<HTMLElement>('[data-plan-task]')
  if (!row) return
  const { left, top } = row.getBoundingClientRect()
  handle.setPointerCapture(pointerId)
  drag = { id, pointer: pointerId, handle, row, startX: clientX, startY: clientY, offsetX: clientX - left, offsetY: clientY - top, x: clientX, y: clientY }
}

function makeGhost(row: HTMLElement) {
  const { width, height } = row.getBoundingClientRect()
  const preview = row.cloneNode(true) as HTMLElement
  preview.removeAttribute('data-plan-task')
  preview.classList.add('plan-drag-ghost')
  preview.setAttribute('aria-hidden', 'true')
  preview.style.width = `${width}px`
  preview.style.height = `${height}px`
  document.body.append(preview)
  return preview
}

function taskAt(x: number, y: number) {
  return document.elementFromPoint(x, y)?.closest<HTMLElement>('[data-plan-task]')?.dataset.planTask ?? null
}

function scrollNearEdge() {
  scrollFrame = 0
  if (!drag || !ghost) return
  const { x, y } = drag
  const step = y < 56 ? -10 : y > window.innerHeight - 64 ? 10 : 0
  if (!step) return
  const before = window.scrollY
  window.scrollBy(0, step)
  if (window.scrollY === before) return
  hover.value = taskAt(x, y)
  scrollFrame = requestAnimationFrame(scrollNearEdge)
}

function trackDrag(event: PointerEvent) {
  if (drag?.pointer !== event.pointerId) return
  if (!ghost) {
    if (Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) < 6) return
    ghost = makeGhost(drag.row)
    dragged.value = drag.id
  }
  drag.x = event.clientX
  drag.y = event.clientY
  ghost.style.transform = `translate3d(${drag.x - drag.offsetX}px, ${drag.y - drag.offsetY}px, 0)`
  hover.value = taskAt(event.clientX, event.clientY)
  if (!scrollFrame) scrollFrame = requestAnimationFrame(scrollNearEdge)
}

function clearDrag() {
  const gesture = drag
  drag = null
  cancelAnimationFrame(scrollFrame)
  scrollFrame = 0
  ghost?.remove()
  ghost = null
  dragged.value = hover.value = null
  if (gesture?.handle.hasPointerCapture(gesture.pointer)) gesture.handle.releasePointerCapture(gesture.pointer)
}

function finishDrag(event: PointerEvent) {
  if (drag?.pointer !== event.pointerId) return
  const target = event.type === 'pointerup' && ghost ? taskAt(event.clientX, event.clientY) : null
  if (target) move(dragIndex.value, tasks.value.findIndex(item => item.id === target))
  clearDrag()
}

function cancelDragOnEscape(event: KeyboardEvent) {
  if (event.key === 'Escape' && drag) clearDrag()
}

async function save() {
  if (!plan.value || busy.value) return
  busy.value = true
  try {
    const result = await api<Plan>('/plan', 'PUT', { base: plan.value.current.id, tasks: tasks.value })
    plan.value = result
    tasks.value = result.current.tasks.map(strip)
    notify('学习计划已保存，今天起立即生效（当日临时任务已保留）')
  } catch (e) {
    notify((e as Error).message, true)
  } finally {
    busy.value = false
  }
}

function applyDraft(rows: Snapshot[]) {
  tasks.value = rows.map(strip)
  pane.value = null
  notify('已载入草稿，点击右上角「保存计划」生效')
}

async function loadVersion() {
  if (!lastVersion.value) return
  busy.value = true
  try {
    const result = await api<Plan['current']>(`/plan/versions/${lastVersion.value}`)
    applyDraft(result.tasks)
  } catch (e) {
    formError.value = (e as Error).message
  } finally {
    busy.value = false
  }
}

function editCategories() {
  categories.value = plan.value?.categories.map(c => ({ ...c })) ?? []
  dialog('categories')
}

function addCategory() {
  categories.value.push({ id: crypto.randomUUID(), name: '', builtin: false, archived: false })
}

async function saveCategories() {
  if (!plan.value) return
  formError.value = ''
  busy.value = true
  try {
    plan.value.categories = await api<Category[]>('/categories', 'PUT', { categories: categories.value })
    pane.value = null
    notify('学习分类已保存')
  } catch (e) {
    formError.value = (e as Error).message
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
        <button type="button" class="btn tinted pill" @click="edit()">
          <Plus :size="15" />新增任务
        </button>
        <div class="plan-toolbar-right">
          <button type="button" class="btn ghost sm" @click="editCategories"><FolderCog :size="15" />分类管理</button>
          <button type="button" class="btn ghost sm" @click="lastVersion = ''; dialog('history')"><History :size="15" />历史版本</button>
          <button type="button" class="btn ghost sm" @click="dialog('default')"><RotateCcw :size="15" />恢复默认</button>
        </div>
      </div>

      <div v-if="!tasks.length" class="empty-box">
        <ListChecks :size="26" class="tertiary" />
        <h3>暂无计划任务</h3>
        <button type="button" class="btn secondary" @click="edit()"><Plus :size="15" />创建第一项日程</button>
      </div>

      <TransitionGroup v-else name="reorder" tag="div" class="plan-list">
        <div
          v-for="(item, index) in tasks"
          :key="item.id"
          :data-plan-task="item.id"
          class="plan-item"
          :class="{
            'drop-target': hover === item.id && dragged !== item.id,
            'drop-after': hover === item.id && dragIndex < index,
            'drag-source': dragged === item.id,
          }"
        >
          <span
            class="drag-handle"
            title="按住拖动排序"
            @pointerdown="startDrag($event, item.id)"
            @pointermove="trackDrag"
            @pointerup="finishDrag"
            @pointercancel="finishDrag"
            @lostpointercapture="finishDrag"
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
            <CategoryBadge
              v-if="info.get(item.category) && !info.get(item.category)?.archived"
              :id="item.category"
              :name="info.get(item.category)?.name ?? ''"
            />
            <span v-else class="pill danger">分类已归档</span>
            <span v-if="item.estimate" class="tertiary tabular est-label">{{ item.estimate }} 分钟</span>
          </div>

          <div class="plan-ops">
            <button type="button" class="icon-btn sm" :disabled="index === 0" title="上移" @click="move(index, index - 1)">
              <ArrowUp :size="14" />
            </button>
            <button
              type="button"
              class="icon-btn sm"
              :disabled="index === tasks.length - 1"
              title="下移"
              @click="move(index, index + 1)"
            >
              <ArrowDown :size="14" />
            </button>
            <button type="button" class="icon-btn sm" title="编辑" @click="edit(item)">
              <Pencil :size="14" />
            </button>
          </div>
        </div>
      </TransitionGroup>
    </section>

    <GlassModal v-model="open" :title="pane ? titles[pane] : ''" :busy="busy" :drawer="pane === 'history'">
      <form v-if="pane === 'task' && task" class="form-stack" @submit.prevent="saveTask">
        <label class="field">
          <span class="field-label">任务名称</span>
          <input v-model="task.title" maxlength="100" required />
        </label>
        <div class="field-grid">
          <label class="field"><span class="field-label">开始时间</span><input v-model="task.start" type="time" required /></label>
          <label class="field"><span class="field-label">结束时间</span><input v-model="task.end" type="time" /></label>
          <label class="field">
            <span class="field-label">分类</span>
            <select v-model="task.category" required>
              <option v-if="!active.some(c => c.id === task?.category)" :value="task.category" disabled>请选择分类</option>
              <option v-for="item in active" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">预计专注（分钟）</span>
            <input v-model.number="task.estimate" type="number" min="1" max="1440" />
          </label>
        </div>
        <label class="field">
          <span class="field-label">备注</span>
          <textarea v-model="task.note" rows="3" maxlength="2000" />
        </label>
        <p v-if="formError" class="error-text" role="alert">{{ formError }}</p>
        <div class="dialog-actions">
          <button v-if="editing" type="button" class="btn danger-ghost push-left" @click="remove(task.id)">
            <Trash2 :size="15" />删除任务
          </button>
          <button type="submit" class="btn primary"><Save :size="15" />应用到草稿</button>
        </div>
      </form>

      <form v-else-if="pane === 'history' && plan" class="form-stack" @submit.prevent="loadVersion">
        <p class="muted" style="font-size: 13px">选择一个历史快照版本载入到当前草稿，保存后即从今天起生效。</p>
        <label class="field">
          <span class="field-label">历史计划版本</span>
          <select v-model="lastVersion" required>
            <option value="" disabled>选择版本</option>
            <option v-for="item in plan.history" :key="item.id" :value="item.id">
              {{ item.date }} · {{ dateTime(item.created_at) }}{{ item.id === plan.current.id ? '（当前）' : '' }}
            </option>
          </select>
        </label>
        <p v-if="formError" class="error-text" role="alert">{{ formError }}</p>
        <div class="dialog-actions">
          <button type="submit" class="btn primary full" :disabled="busy"><History :size="15" />载入到草稿</button>
        </div>
      </form>

      <div v-else-if="pane === 'default' && plan" class="form-stack">
        <p class="muted">将用内置的 24 项标准学习日程替换当前草稿，点击「保存计划」后才会真正生效。</p>
        <div class="dialog-actions">
          <button type="button" class="btn ghost" @click="pane = null">取消</button>
          <button type="button" class="btn primary" @click="applyDraft(plan.defaults)">
            <RotateCcw :size="15" />载入默认模板
          </button>
        </div>
      </div>

      <form v-else-if="pane === 'categories'" class="form-stack" @submit.prevent="saveCategories">
        <div v-for="item in categories" :key="item.id" class="cat-edit-row">
          <input v-model="item.name" :disabled="item.builtin" maxlength="100" required placeholder="输入分类名称" />
          <label v-if="!item.builtin" class="archive-check">
            <input v-model="item.archived" type="checkbox" />归档
          </label>
          <span v-else class="pill">内置</span>
        </div>
        <div>
          <button type="button" class="btn secondary sm" :disabled="categories.length >= 100" @click="addCategory">
            <Plus :size="14" />新增分类
          </button>
        </div>
        <p v-if="formError" class="error-text" role="alert">{{ formError }}</p>
        <div class="dialog-actions">
          <button type="submit" class="btn primary full" :disabled="busy"><Save :size="15" />保存分类</button>
        </div>
      </form>
    </GlassModal>

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
.reorder-move {
  transition: transform 0.25s var(--ease-spring);
}
.cat-edit-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}
.archive-check {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12.5px;
  color: var(--ink-secondary);
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
    justify-content: space-between;
  }
  .plan-page :deep(.page-header-actions .btn.primary) {
    flex: 1;
  }
  .plan-card {
    padding: 14px 12px;
    gap: 12px;
  }
  .plan-toolbar {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    justify-items: stretch;
    gap: 8px;
  }
  .plan-toolbar > .btn {
    width: 100%;
  }
  .plan-toolbar-right {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
  }
  .plan-toolbar-right .btn {
    padding: 0 6px;
    background: var(--surface-subtle);
    border: 1px solid var(--border);
  }
  .plan-item {
    grid-template-columns: 20px 44px minmax(0, 1fr);
    gap: 6px 8px;
    padding: 10px 10px;
    border-radius: 13px;
  }
  .drag-handle {
    grid-row: 1 / span 2;
  }
  .plan-time {
    grid-row: 1 / span 2;
    align-self: start;
    padding-top: 2px;
  }
  .plan-time time {
    font-size: 12px;
  }
  .plan-title-col {
    grid-column: 3;
  }
  .plan-title-col strong {
    font-size: 13px;
  }
  .plan-meta-col {
    grid-column: 3;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 6px;
  }
  .plan-ops {
    grid-column: 3;
    justify-content: flex-end;
    margin-top: -2px;
    padding-top: 6px;
    border-top: 1px solid var(--border);
  }
}
</style>
