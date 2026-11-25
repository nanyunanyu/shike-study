<script setup lang="ts">
import { Upload } from 'lucide-vue-next'
import GlassModal from '@/components/ui/GlassModal.vue'
import type { BackupCounts } from '@/types'

const open = defineModel<boolean>({ required: true })

defineProps<{
  preview: { name: string; counts: BackupCounts } | null
  busy: boolean
  error: string
}>()

const emit = defineEmits<{ confirm: [] }>()
</script>

<template>
  <GlassModal v-model="open" title="确认导入并覆盖学习数据" :busy="busy">
    <div v-if="preview" class="form-stack">
      <strong class="break-text">{{ preview.name }}</strong>
      <p class="muted">
        包含 {{ preview.counts.plans }} 个计划版本 · {{ preview.counts.days }} 天记录 · {{ preview.counts.focus }} 次专注 ·
        {{ preview.counts.categories }} 个分类<template v-if="preview.counts.milestones">
          · {{ preview.counts.milestones }} 个里程碑</template
        >
      </p>
      <p class="muted">确认后将覆盖当前账号在线学习数据；服务端会先自动保存一份回滚副本。</p>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="dialog-actions">
        <button type="button" class="btn ghost" :disabled="busy" @click="open = false">取消</button>
        <button type="button" class="btn danger" :disabled="busy" @click="emit('confirm')">
          <Upload :size="15" />确认覆盖导入
        </button>
      </div>
    </div>
  </GlassModal>
</template>
