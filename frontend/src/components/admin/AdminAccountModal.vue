<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { createAdminUserApi, deleteAdminUserApi, resetAdminUserPasswordApi, setAdminUserActiveApi } from '@/api/admin'
import GlassModal from '@/components/ui/GlassModal.vue'
import { notify } from '@/stores/ui'
import type { User } from '@/types'

export type AccountActionMode = 'create' | 'reset' | 'active' | 'delete'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{
  mode: AccountActionMode
  target: User | null
}>()

const emit = defineEmits<{ done: [created: boolean] }>()

const busy = ref(false)
const formError = ref('')
const username = ref('')
const password = ref('')
const mustChange = ref(true)
const confirmation = ref('')

const title = computed(
  () =>
    ({
      create: '创建学习账号',
      reset: '重置账号密码',
      active: props.target?.active ? '停用账号' : '启用账号',
      delete: '删除账号',
    })[props.mode],
)

watch([open, () => props.mode, () => props.target], ([isOpen]) => {
  if (!isOpen) return
  formError.value = ''
  username.value = ''
  password.value = ''
  confirmation.value = ''
  mustChange.value = true
})

async function submit() {
  if (busy.value) return
  busy.value = true
  formError.value = ''
  const user = props.target
  try {
    if (props.mode === 'create') {
      await createAdminUserApi({ username: username.value, password: password.value, must_change: mustChange.value })
    } else if (props.mode === 'reset' && user) {
      await resetAdminUserPasswordApi(user.id, { password: password.value, must_change: mustChange.value })
    } else if (props.mode === 'active' && user) {
      await setAdminUserActiveApi(user.id, !user.active)
    } else if (props.mode === 'delete' && user && confirmation.value === user.username) {
      await deleteAdminUserApi(user.id)
    }
    notify(`${title.value}成功`)
    open.value = false
    password.value = ''
    emit('done', props.mode === 'create')
  } catch (e) {
    formError.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <GlassModal v-model="open" :title="title" :busy="busy">
    <form class="form-stack" @submit.prevent="submit">
      <template v-if="mode === 'create' || mode === 'reset'">
        <label v-if="mode === 'create'" class="field">
          <span class="field-label">用户名</span>
          <input
            v-model="username"
            required
            minlength="3"
            maxlength="32"
            pattern="[A-Za-z0-9][A-Za-z0-9_.\-]{2,31}"
            placeholder="3-32 位字母/数字"
          />
        </label>
        <p v-else class="muted">目标账号：<strong>{{ target?.username }}</strong></p>
        <label class="field">
          <span class="field-label">{{ mode === 'create' ? '初始密码' : '新密码' }}</span>
          <input v-model="password" type="password" required minlength="6" maxlength="256" placeholder="至少 6 位" />
        </label>
        <label class="switch-row glass-inset" style="padding: 8px 14px">
          <span>下次登录必须修改密码</span>
          <input v-model="mustChange" type="checkbox" role="switch" />
        </label>
      </template>

      <template v-if="mode === 'active'">
        <p>确认{{ target?.active ? '停用' : '启用' }}账号 <strong>{{ target?.username }}</strong>？</p>
        <p v-if="target?.active" class="muted">停用后该账号的现有登录会话将立即失效。</p>
      </template>

      <template v-if="mode === 'delete'">
        <p>将永久删除账号及其所有在线学习数据。请输入 <strong>{{ target?.username }}</strong> 以确认：</p>
        <input v-model="confirmation" required autocomplete="off" />
      </template>

      <p v-if="formError" class="error-text" role="alert">{{ formError }}</p>
      <div class="dialog-actions">
        <button type="button" class="btn ghost" :disabled="busy" @click="open = false">取消</button>
        <button
          type="submit"
          class="btn"
          :class="mode === 'delete' ? 'danger' : 'primary'"
          :disabled="busy || (mode === 'delete' && confirmation !== target?.username)"
        >
          {{ title }}
        </button>
      </div>
    </form>
  </GlassModal>
</template>
