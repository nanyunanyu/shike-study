<script setup lang="ts">
import { ref, watch } from 'vue'
import { Clock3, RotateCcw } from 'lucide-vue-next'
import GlassModal from '@/components/ui/GlassModal.vue'
import type { DayTask, Times } from '@/types'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{
  task: DayTask | null
  busy: boolean
}>()

const emit = defineEmits<{
  save: [taskId: string, times: Times | null]
}>()

const start = ref('')
const end = ref('')
const error = ref('')

watch(
  [open, () => props.task],
  ([isOpen, task]) => {
    if (isOpen && task) {
      const active = task.override ?? task
      start.value = active.start
      end.value = active.end ?? ''
      error.value = ''
    }
  },
  { immediate: true },
)

function submit(reset = false) {
  if (!props.task) return
  const payload: Times = { start: start.value, end: end.value || null }
  if (!reset && payload.end && payload.end <= payload.start) {
    error.value = '结束时间须晚于开始时间'
    return
  }
  emit('save', props.task.id, reset ? null : payload)
}
</script>

<template>
  <GlassModal v-model="open" title="调整当天时段" :subtitle="task?.title" :busy="busy">
    <form class="form-stack" @submit.prevent="submit(false)">
      <div class="field-grid">
        <label class="field"><span class="field-label">开始时间</span><input v-model="start" type="time" required /></label>
        <label class="field"><span class="field-label">结束时间</span><input v-model="end" type="time" /></label>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="dialog-actions">
        <button v-if="task?.override" type="button" class="btn ghost push-left" :disabled="busy" @click="submit(true)">
          <RotateCcw :size="15" />恢复计划时段
        </button>
        <button type="submit" class="btn primary" :disabled="busy"><Clock3 :size="15" />保存时段</button>
      </div>
    </form>
  </GlassModal>
</template>
