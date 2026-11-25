<script setup lang="ts">
import { ref, watch } from 'vue'
import { Save } from 'lucide-vue-next'
import GlassModal from '@/components/ui/GlassModal.vue'
import { session } from '@/stores/session'
import type { AdhocTaskPayload, Category, DayTask } from '@/types'
import { currentHHMM } from '@/utils/date'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{
  editingTask: DayTask | null
  categories: Category[]
  busy: boolean
}>()

const emit = defineEmits<{
  submit: [payload: AdhocTaskPayload, editingId: string | null]
}>()

const form = ref({
  title: '',
  start: '14:00',
  end: '',
  category: 'practice',
  note: '',
  estimate: 30 as number | null,
})
const error = ref('')

watch(
  [open, () => props.editingTask],
  ([isOpen, task]) => {
    if (!isOpen) return
    error.value = ''
    if (task) {
      form.value = {
        title: task.title,
        start: (task.override ?? task).start,
        end: (task.override ?? task).end ?? '',
        category: task.category,
        note: task.note,
        estimate: task.estimate,
      }
    } else {
      form.value = {
        title: '',
        start: currentHHMM(session.value?.timezone),
        end: '',
        category: props.categories[0]?.id ?? 'practice',
        note: '',
        estimate: 30,
      }
    }
  },
  { immediate: true },
)

function submit() {
  const title = form.value.title.trim()
  if (!title) {
    error.value = '请输入临时任务名称'
    return
  }
  const end = form.value.end || null
  if (end && end <= form.value.start) {
    error.value = '结束时间须晚于开始时间'
    return
  }
  emit(
    'submit',
    {
      title,
      start: form.value.start,
      end,
      category: form.value.category,
      note: form.value.note.trim(),
      estimate: form.value.estimate ? Number(form.value.estimate) : null,
    },
    props.editingTask?.id ?? null,
  )
}
</script>

<template>
  <GlassModal
    v-model="open"
    :title="editingTask ? '编辑今日临时任务' : '添加今日临时任务'"
    subtitle="仅作用于今天，不会改动你的主学习计划模板"
    :busy="busy"
  >
    <form class="form-stack" @submit.prevent="submit">
      <label class="field">
        <span class="field-label">任务名称</span>
        <input v-model="form.title" required maxlength="100" placeholder="例如：整理今天错题本、刷一套真题…" />
      </label>
      <div class="field-grid">
        <label class="field"><span class="field-label">开始时间</span><input v-model="form.start" type="time" required /></label>
        <label class="field"><span class="field-label">结束时间（选填）</span><input v-model="form.end" type="time" /></label>
        <label class="field">
          <span class="field-label">分类</span>
          <select v-model="form.category" required>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
        </label>
        <label class="field">
          <span class="field-label">预计专注（分钟）</span>
          <input v-model.number="form.estimate" type="number" min="1" max="1440" />
        </label>
      </div>
      <label class="field">
        <span class="field-label">备注</span>
        <textarea v-model="form.note" rows="2" maxlength="2000" placeholder="可选：补充目标或资料页码" />
      </label>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="dialog-actions">
        <button type="button" class="btn ghost" :disabled="busy" @click="open = false">取消</button>
        <button type="submit" class="btn primary" :disabled="busy">
          <Save :size="15" />{{ editingTask ? '保存修改' : '添加到今日时间轴' }}
        </button>
      </div>
    </form>
  </GlassModal>
</template>
