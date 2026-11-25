<script setup lang="ts">
import { ref } from 'vue'
import { CheckCircle2, Flag, Pencil, Pin, Plus } from 'lucide-vue-next'
import { updateMilestoneApi } from '@/api/stats'
import { paletteSwatch } from '@/constants/theme'
import { notify } from '@/stores/ui'
import type { Milestone } from '@/types'
import MilestoneFormModal from './MilestoneFormModal.vue'

defineProps<{ milestones: Milestone[] }>()
const emit = defineEmits<{ changed: [] }>()

const open = ref(false)
const editing = ref<Milestone | null>(null)

function openCreate() {
  editing.value = null
  open.value = true
}

function openEdit(item: Milestone) {
  editing.value = item
  open.value = true
}

async function quickToggle(item: Milestone, field: 'pinned' | 'completed') {
  try {
    await updateMilestoneApi(item.id, {
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
        :style="{ '--ms-color': paletteSwatch(item.color) }"
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

    <MilestoneFormModal v-model="open" :editing="editing" @changed="emit('changed')" />
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
