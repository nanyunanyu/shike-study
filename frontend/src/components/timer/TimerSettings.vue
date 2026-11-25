<script setup lang="ts">
import { Save } from 'lucide-vue-next'
import type { Preferences } from '@/types'

const model = defineModel<Preferences>({ required: true })
defineProps<{ busy?: boolean }>()
defineEmits<{ save: [] }>()
</script>

<template>
  <form class="form-stack" @submit.prevent="$emit('save')">
    <div class="field-grid-3">
      <label class="field">
        <span class="field-label">番茄专注 (分)</span>
        <input v-model.number="model.focus_minutes" type="number" min="1" max="180" required />
      </label>
      <label class="field">
        <span class="field-label">番茄休息 (分)</span>
        <input v-model.number="model.break_minutes" type="number" min="1" max="120" required />
      </label>
      <label class="field">
        <span class="field-label">默认倒计时 (分)</span>
        <input v-model.number="model.countdown_minutes" type="number" min="1" max="720" required />
      </label>
    </div>

    <label class="field">
      <span class="field-label">每日专注目标 (分钟)</span>
      <input v-model.number="model.daily_focus_goal_minutes" type="number" min="15" max="1440" step="15" required />
      <small class="tertiary">约 {{ Math.round((model.daily_focus_goal_minutes / 60) * 10) / 10 }} 小时 / 天，用于今日进度环与侧栏目标条</small>
    </label>

    <label class="switch-row glass-inset" style="padding: 8px 14px">
      <span>番茄专注完成后自动进入休息</span>
      <input v-model="model.auto_break" type="checkbox" role="switch" />
    </label>

    <div class="dialog-actions">
      <button type="submit" class="btn primary full" :disabled="busy">
        <Save :size="15" />{{ busy ? '保存中…' : '保存计时偏好' }}
      </button>
    </div>
  </form>
</template>
