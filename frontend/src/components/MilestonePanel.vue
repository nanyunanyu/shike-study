<script setup lang="ts">
import { ref } from 'vue'
import { CheckCircle2, Flag, Pencil, Pin, Plus, Save, Trash2 } from 'lucide-vue-next'
import { api, notify, PALETTES, today } from '../state'
import type { Milestone, Palette } from '../types'
import GlassModal from './ui/GlassModal.vue'

defineProps<{ milestones: Milestone[] }>()
const emit = defineEmits<{ changed: [] }>()

const open = ref(false)
const busy = ref(false)
const editingId = ref<string | null>(null)
const error = ref('')
const form = ref({
  title: '',
  target_date: '',
  note: '',
  color: 'blue' as Palette,
  pinned: true,
  completed: false,
})

function openCreate() {
  editingId.value = null
  const nextMonth = new Date(`${today.value || '2026-11-25'}T00:00:00Z`)
  nextMonth.setUTCDate(nextMonth.getUTCDate() + 30)
  form.value = {
    title: '',
    target_date: nextMonth.toISOString().slice(0, 10),
    note: '',
    color: 'blue',
    pinned: true,
    completed: false,
  }
  error.value = ''
  open.value = true
}

function openEdit(item: Milestone) {
  editingId.value = item.id
  form.value = {
    title: item.title,
    target_date: item.target_date,
    note: item.note,
    color: item.color,
    pinned: item.pinned,
    completed: item.completed,
  }
  error.value = ''
  open.value = true
}

async function submit() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    if (editingId.value) {
      await api(`/milestones/${editingId.value}`, 'PUT', form.value)
      notify('里程碑已更新')
    } else {
      await api('/milestones', 'POST', {
        title: form.value.title,
        target_date: form.value.target_date,
        note: form.value.note,
        color: form.value.color,
        pinned: form.value.pinned,
      })
      notify('已添加目标倒计时')
    }
    open.value = false
    emit('changed')
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}

async function quickToggle(item: Milestone, field: 'pinned' | 'completed') {
  try {
    await api(`/milestones/${item.id}`, 'PUT', {
      title: item.title,
      target_date: item.target_date,
      note: item.note,
      color: item.color,
      pinned: field === 'pinned' ? !item.pinned : item.pinned,
      completed: field === 'completed' ? !item.completed : item.completed,
    })
    emit('changed')
  } catch (e) {
    notify((e as Error).message, true)
  }
}

async function remove(item: Milestone) {
  busy.value = true
  try {
    await api(`/milestones/${item.id}`, 'DELETE')
    open.value = false
    notify('里程碑已删除')
    emit('changed')
  } catch (e) {
    notify((e as Error).message, true)
  } finally {
    busy.value = false
  }
}

function swatchFor(color: Palette) {
  return PALETTES.find(p => p.id === color)?.swatch ?? '#2563eb'
}
</script>

<template>
  <section class="milestone-panel glass-card">
    <header class="section-head">
      <div class="section-title">
        <Flag :size="18" />
        <h2>学习目标与倒计时</h2>
      </div>
      <button type="button" class="btn tinted sm pill" @click="openCreate">
        <Plus :size="14" />新建倒计时
      </button>
    </header>

    <div v-if="!milestones.length" class="empty-box compact">
      <Flag :size="22" class="tertiary" />
      <p>设定考试、答辩或阶段目标日期，置顶后会在「今日」页持续提醒。</p>
      <button type="button" class="btn secondary sm" @click="openCreate"><Plus :size="14" />添加首个里程碑</button>
    </div>

    <div v-else class="ms-grid">
      <article
        v-for="item in milestones"
        :key="item.id"
        class="ms-card"
        :class="{ done: item.completed }"
        :style="{ '--ms-color': swatchFor(item.color) }"
      >
        <div class="ms-top">
          <div class="ms-title-wrap">
            <span class="ms-dot"></span>
            <strong>{{ item.title }}</strong>
          </div>
          <div class="ms-ops">
            <button
              type="button"
              class="icon-btn sm"
              :class="{ pinned: item.pinned }"
              :title="item.pinned ? '取消置顶到今日页' : '置顶到今日页'"
              @click="quickToggle(item, 'pinned')"
            >
              <Pin :size="14" />
            </button>
            <button
              type="button"
              class="icon-btn sm"
              :title="item.completed ? '标记为进行中' : '标记已达成'"
              @click="quickToggle(item, 'completed')"
            >
              <CheckCircle2 :size="14" />
            </button>
            <button type="button" class="icon-btn sm" title="编辑" @click="openEdit(item)">
              <Pencil :size="14" />
            </button>
          </div>
        </div>

        <div class="ms-countdown">
          <template v-if="item.completed">
            <span class="pill success"><CheckCircle2 :size="12" />目标已达成</span>
          </template>
          <template v-else-if="item.days_left > 0">
            <strong class="ms-days tabular">{{ item.days_left }}</strong>
            <span class="muted">天后</span>
          </template>
          <template v-else-if="item.days_left === 0">
            <strong class="ms-days">就是今天</strong>
          </template>
          <template v-else>
            <strong class="ms-days tabular">+{{ -item.days_left }}</strong>
            <span class="muted">天已过</span>
          </template>
          <small class="tertiary tabular ms-date">{{ item.target_date }}</small>
        </div>

        <p v-if="item.note" class="ms-note muted">{{ item.note }}</p>
      </article>
    </div>

    <GlassModal v-model="open" :title="editingId ? '编辑学习里程碑' : '新建学习里程碑'" :busy="busy">
      <form class="form-stack" @submit.prevent="submit">
        <label class="field">
          <span class="field-label">目标名称</span>
          <input v-model="form.title" required maxlength="100" placeholder="例如：考研初试、英语六级、毕业答辩" />
        </label>
        <div class="field-grid">
          <label class="field">
            <span class="field-label">目标日期</span>
            <input v-model="form.target_date" type="date" required />
          </label>
          <label class="field">
            <span class="field-label">主题标识色</span>
            <select v-model="form.color">
              <option v-for="p in PALETTES" :key="p.id" :value="p.id">{{ p.label }}</option>
            </select>
          </label>
        </div>
        <label class="field">
          <span class="field-label">阶段备忘</span>
          <textarea v-model="form.note" rows="2" maxlength="2000" placeholder="写下这一阶段的聚焦方向…" />
        </label>
        <label class="switch-row glass-inset" style="padding: 8px 14px">
          <span>置顶到「今日学习」顶部卡片</span>
          <input v-model="form.pinned" type="checkbox" role="switch" />
        </label>
        <label v-if="editingId" class="switch-row glass-inset" style="padding: 8px 14px">
          <span>标记为已达成</span>
          <input v-model="form.completed" type="checkbox" role="switch" />
        </label>
        <p v-if="error" class="error-text" role="alert">{{ error }}</p>
        <div class="dialog-actions">
          <button
            v-if="editingId"
            type="button"
            class="btn danger-ghost push-left"
            :disabled="busy"
            @click="remove(milestones.find(m => m.id === editingId)!)"
          >
            <Trash2 :size="15" />删除
          </button>
          <button type="submit" class="btn primary" :disabled="busy"><Save :size="15" />保存里程碑</button>
        </div>
      </form>
    </GlassModal>
  </section>
</template>

<style scoped>
.milestone-panel {
  padding: 20px 22px;
  display: grid;
  gap: 16px;
}
.ms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(248px, 1fr));
  gap: 12px;
}
.ms-card {
  padding: 15px 16px;
  border-radius: 16px;
  background:
    radial-gradient(90% 90% at 100% 0%, color-mix(in srgb, var(--ms-color) 11%, transparent), transparent 68%),
    var(--surface-subtle);
  border: 1px solid var(--border);
  display: grid;
  gap: 10px;
  align-content: start;
}
.ms-card.done {
  opacity: 0.72;
}
.ms-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.ms-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.ms-title-wrap strong {
  font-size: 14px;
  font-weight: 640;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ms-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ms-color);
  flex: none;
}
.ms-ops {
  display: flex;
  gap: 2px;
  flex: none;
}
.ms-ops .pinned {
  color: var(--accent);
  background: var(--accent-soft);
}
.ms-countdown {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.ms-days {
  font-size: 32px;
  font-weight: 760;
  line-height: 1;
  letter-spacing: -0.04em;
  color: var(--ms-color);
}
.ms-date {
  margin-left: auto;
  font-size: 11.5px;
}
.ms-note {
  font-size: 12px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}
@media (max-width: 768px) {
  .milestone-panel {
    padding: 15px 14px;
    gap: 12px;
  }
  .ms-grid {
    grid-template-columns: 1fr;
    gap: 9px;
  }
  .ms-card {
    padding: 13px 14px;
    gap: 8px;
    border-radius: 14px;
  }
  .ms-days {
    font-size: 26px;
  }
}
</style>
