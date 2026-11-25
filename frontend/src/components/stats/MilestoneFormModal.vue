<script setup lang="ts">
import { ref, watch } from 'vue'
import { Save, Trash2 } from 'lucide-vue-next'
import { createMilestoneApi, deleteMilestoneApi, updateMilestoneApi } from '@/api/stats'
import GlassModal from '@/components/ui/GlassModal.vue'
import { PALETTES } from '@/constants/theme'
import { today } from '@/stores/session'
import { notify } from '@/stores/ui'
import type { Milestone, Palette } from '@/types'
import { addDaysIso } from '@/utils/date'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{ editing: Milestone | null }>()
const emit = defineEmits<{ changed: [] }>()

const busy = ref(false)
const error = ref('')
const form = ref({
  title: '',
  target_date: '',
  note: '',
  color: 'blue' as Palette,
  pinned: true,
  completed: false,
})

watch(
  [open, () => props.editing],
  ([isOpen, item]) => {
    if (!isOpen) return
    error.value = ''
    if (item) {
      form.value = {
        title: item.title,
        target_date: item.target_date,
        note: item.note,
        color: item.color,
        pinned: item.pinned,
        completed: item.completed,
      }
    } else {
      form.value = {
        title: '',
        target_date: addDaysIso(today.value || '2026-11-25', 30),
        note: '',
        color: 'blue',
        pinned: true,
        completed: false,
      }
    }
  },
  { immediate: true },
)

async function submit() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    if (props.editing) {
      await updateMilestoneApi(props.editing.id, form.value)
      notify('里程碑已更新')
    } else {
      await createMilestoneApi({
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

async function remove() {
  if (!props.editing || busy.value) return
  busy.value = true
  try {
    await deleteMilestoneApi(props.editing.id)
    open.value = false
    notify('里程碑已删除')
    emit('changed')
  } catch (e) {
    notify((e as Error).message, true)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <GlassModal v-model="open" :title="editing ? '编辑学习里程碑' : '新建学习里程碑'" :busy="busy">
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
      <label v-if="editing" class="switch-row glass-inset" style="padding: 8px 14px">
        <span>标记为已达成</span>
        <input v-model="form.completed" type="checkbox" role="switch" />
      </label>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="dialog-actions">
        <button v-if="editing" type="button" class="btn danger-ghost push-left" :disabled="busy" @click="remove">
          <Trash2 :size="15" />删除
        </button>
        <button type="submit" class="btn primary" :disabled="busy"><Save :size="15" />保存里程碑</button>
      </div>
    </form>
  </GlassModal>
</template>
