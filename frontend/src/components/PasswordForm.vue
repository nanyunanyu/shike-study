<script setup lang="ts">
import { ref } from 'vue'
import { Eye, EyeOff, KeyRound } from 'lucide-vue-next'
import { api, notify, setSession } from '../state'
import type { Session } from '../types'

const emit = defineEmits<{ saved: [] }>()
const current = ref('')
const next = ref('')
const confirm = ref('')
const show = ref(false)
const busy = ref(false)
const error = ref('')

async function submit() {
  if (busy.value) return
  if (next.value !== confirm.value) {
    error.value = '两次输入的新密码不一致'
    return
  }
  busy.value = true
  error.value = ''
  try {
    const updated = await api<Session>('/auth/password', 'POST', { current: current.value, password: next.value })
    setSession(updated)
    current.value = next.value = confirm.value = ''
    notify('密码已更新')
    emit('saved')
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <form class="form-stack" @submit.prevent="submit">
    <label class="field">
      <span class="field-label">当前密码</span>
      <span class="input-wrap">
        <input v-model="current" :type="show ? 'text' : 'password'" autocomplete="current-password" required maxlength="256" placeholder="输入当前密码" />
        <button type="button" class="icon-btn sm input-suffix" :aria-label="show ? '隐藏密码' : '显示密码'" @click="show = !show">
          <EyeOff v-if="show" :size="16" /><Eye v-else :size="16" />
        </button>
      </span>
    </label>
    <label class="field">
      <span class="field-label">新密码</span>
      <input v-model="next" :type="show ? 'text' : 'password'" autocomplete="new-password" required minlength="6" maxlength="256" placeholder="至少 6 位字符" />
    </label>
    <label class="field">
      <span class="field-label">确认新密码</span>
      <input v-model="confirm" :type="show ? 'text' : 'password'" autocomplete="new-password" required minlength="6" maxlength="256" placeholder="再次输入新密码" />
    </label>
    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    <div class="dialog-actions">
      <button class="btn primary full" :disabled="busy">
        <KeyRound :size="16" />{{ busy ? '正在保存…' : '保存新密码' }}
      </button>
    </div>
  </form>
</template>
