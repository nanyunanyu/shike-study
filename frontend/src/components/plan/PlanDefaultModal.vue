<script setup lang="ts">
import { RotateCcw } from 'lucide-vue-next'
import GlassModal from '@/components/ui/GlassModal.vue'

const open = defineModel<boolean>({ required: true })
defineProps<{ busy: boolean }>()
const emit = defineEmits<{ confirm: [] }>()

function handleConfirm() {
  emit('confirm')
  open.value = false
}
</script>

<template>
  <GlassModal v-model="open" title="恢复默认计划" :busy="busy">
    <div class="form-stack">
      <p class="muted">将用内置的 24 项标准学习日程替换当前草稿，点击「保存计划」后才会真正生效。</p>
      <div class="dialog-actions">
        <button type="button" class="btn ghost" @click="open = false">取消</button>
        <button type="button" class="btn primary" @click="handleConfirm">
          <RotateCcw :size="15" />载入默认模板
        </button>
      </div>
    </div>
  </GlassModal>
</template>
