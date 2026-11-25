<script setup lang="ts">
import { ref, watch } from 'vue'
import { History } from 'lucide-vue-next'
import { fetchPlanVersion } from '@/api/plan'
import GlassModal from '@/components/ui/GlassModal.vue'
import { session } from '@/stores/session'
import type { PlanVersion, Snapshot } from '@/types'
import { formatClockTime } from '@/utils/date'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{
  history: PlanVersion[]
  currentId: string
}>()

const emit = defineEmits<{
  apply: [tasks: Snapshot[]]
}>()

const selectedId = ref('')
const busy = ref(false)
const error = ref('')

watch(open, isOpen => {
  if (isOpen) {
    selectedId.value = ''
    error.value = ''
  }
})

async function submit() {
  if (!selectedId.value || busy.value) return
  busy.value = true
  error.value = ''
  try {
    const result = await fetchPlanVersion(selectedId.value)
    emit('apply', result.tasks)
    open.value = false
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <GlassModal v-model="open" title="历史计划版本" :busy="busy" drawer>
    <form class="form-stack" @submit.prevent="submit">
      <p class="muted" style="font-size: 13px">选择一个历史快照版本载入到当前草稿，保存后即从今天起生效。</p>
      <label class="field">
        <span class="field-label">历史计划版本</span>
        <select v-model="selectedId" required>
          <option value="" disabled>选择版本</option>
          <option v-for="item in props.history" :key="item.id" :value="item.id">
            {{ item.date }} · {{ formatClockTime(item.created_at, session?.timezone) }}{{ item.id === currentId ? '（当前）' : '' }}
          </option>
        </select>
      </label>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="dialog-actions">
        <button type="submit" class="btn primary" :disabled="busy"><History :size="15" />载入到草稿</button>
      </div>
    </form>
  </GlassModal>
</template>
