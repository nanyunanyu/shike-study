<script setup lang="ts">
import { ref, watch } from 'vue'
import { Save, Trash2 } from 'lucide-vue-next'
import GlassModal from '@/components/ui/GlassModal.vue'
import type { Category, Task } from '@/types'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{
  task: Task | null
  editing: boolean
  activeCategories: Category[]
  busy: boolean
}>()

const emit = defineEmits<{
  save: [task: Task]
  remove: [id: string]
}>()

const draft = ref<Task | null>(null)
const error = ref('')

watch(
  [open, () => props.task],
  ([isOpen, value]) => {
    if (isOpen && value) {
      draft.value = { ...value }
      error.value = ''
    }
  },
  { immediate: true },
)

function submit() {
  if (!draft.value) return
  const item: Task = {
    ...draft.value,
    title: draft.value.title.trim(),
    end: draft.value.end || null,
    estimate: draft.value.estimate || null,
  }
  if (!item.title) {
    error.value = '请输入任务名称'
    return
  }
  if (item.end && item.end <= item.start) {
    error.value = '结束时间须晚于开始时间'
    return
  }
  emit('save', item)
  open.value = false
}

function handleRemove() {
  if (!draft.value) return
  emit('remove', draft.value.id)
  open.value = false
}
</script>

<template>
  <GlassModal v-model="open" title="编辑计划任务" :busy="busy">
    <form v-if="draft" class="form-stack" @submit.prevent="submit">
      <label class="field">
        <span class="field-label">任务名称</span>
        <input v-model="draft.title" maxlength="100" required />
      </label>
      <div class="field-grid">
        <label class="field"><span class="field-label">开始时间</span><input v-model="draft.start" type="time" required /></label>
        <label class="field"><span class="field-label">结束时间</span><input v-model="draft.end" type="time" /></label>
        <label class="field">
          <span class="field-label">分类</span>
          <select v-model="draft.category" required>
            <option v-if="!activeCategories.some(c => c.id === draft?.category)" :value="draft.category" disabled>
              请选择分类
            </option>
            <option v-for="item in activeCategories" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
        </label>
        <label class="field">
          <span class="field-label">预计专注（分钟）</span>
          <input v-model.number="draft.estimate" type="number" min="1" max="1440" />
        </label>
      </div>
      <label class="field">
        <span class="field-label">备注</span>
        <textarea v-model="draft.note" rows="3" maxlength="2000" />
      </label>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="dialog-actions">
        <button v-if="editing" type="button" class="btn danger-ghost push-left" @click="handleRemove">
          <Trash2 :size="15" />删除任务
        </button>
        <button type="submit" class="btn primary"><Save :size="15" />应用到草稿</button>
      </div>
    </form>
  </GlassModal>
</template>
