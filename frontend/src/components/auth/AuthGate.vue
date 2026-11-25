<script setup lang="ts">
import { ref } from 'vue'
import { ArrowRight, Eye, EyeOff, LogOut, Terminal } from 'lucide-vue-next'
import { loginApi, logoutApi } from '@/api/auth'
import { clearSession, session, setSession } from '@/stores/session'
import AuthShowcase from './AuthShowcase.vue'
import PasswordForm from './PasswordForm.vue'
import TimepieceDial from './TimepieceDial.vue'

defineProps<{ initialized: boolean }>()
const emit = defineEmits<{ retry: [] }>()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const submitting = ref(false)
const problem = ref('')

async function login() {
  if (submitting.value) return
  submitting.value = true
  problem.value = ''
  try {
    setSession(await loginApi({ username: username.value, password: password.value }))
    password.value = ''
    showPassword.value = false
  } catch (e) {
    problem.value = (e as Error).message
  } finally {
    submitting.value = false
  }
}

async function logout() {
  problem.value = ''
  try {
    await logoutApi()
    clearSession()
  } catch (e) {
    problem.value = (e as Error).message
  }
}
</script>

<template>
  <main class="auth-stage">
    <div class="auth-ambient" aria-hidden="true"></div>

    <div class="auth-shell">
      <AuthShowcase />

      <section class="auth-card-col">
        <div class="auth-mobile-hero">
          <TimepieceDial size="compact" />
          <div class="mobile-hero-copy">
            <strong>拾刻学习</strong>
            <span>拾起每一刻专注</span>
          </div>
        </div>

        <div class="auth-card glass-card-solid">
          <template v-if="session?.user.must_change">
            <header class="auth-head">
              <span class="pill accent">首次登录安全提示</span>
              <h1>请设置你的新密码</h1>
              <p class="muted">账号 {{ session.user.username }} 需要先完成改密再继续使用。</p>
            </header>
            <PasswordForm />
            <button type="button" class="btn ghost full auth-secondary" @click="logout">
              <LogOut :size="16" />退出当前账号
            </button>
            <p v-if="problem" class="error-text" role="alert">{{ problem }}</p>
          </template>

          <template v-else-if="!initialized">
            <header class="auth-head">
              <span class="pill warning">等待初始化</span>
              <h1>初始化超级管理员</h1>
              <p class="muted">首次启动尚无管理员账号，请在终端后端目录执行以下命令创建：</p>
            </header>
            <div class="setup-cmd glass-inset">
              <Terminal :size="15" class="accent-text" />
              <code>uv run python -m study.cli init-admin</code>
            </div>
            <p class="muted setup-tip">如需体验带示例数据的演示环境，也可以执行 <code>uv run python -m study.cli seed-demo</code>。</p>
            <p v-if="problem" class="error-text" role="alert">{{ problem }}</p>
            <button type="button" class="btn primary lg full" @click="emit('retry')">
              重新检测初始化状态 <ArrowRight :size="16" />
            </button>
          </template>

          <template v-else>
            <header class="auth-head">
              <h1>欢迎回来</h1>
              <p class="muted">登录你的个人空间</p>
            </header>
            <form class="form-stack" @submit.prevent="login">
              <label class="field" for="login-username">
                <span class="field-label">用户名</span>
                <input
                  id="login-username"
                  v-model="username"
                  autocomplete="username"
                  required
                  maxlength="64"
                  placeholder="请输入用户名"
                />
              </label>
              <label class="field" for="login-password">
                <span class="field-label">密码</span>
                <span class="input-wrap">
                  <input
                    id="login-password"
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    autocomplete="current-password"
                    required
                    maxlength="256"
                    placeholder="请输入密码"
                  />
                  <button
                    type="button"
                    class="icon-btn sm input-suffix"
                    :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                    @click="showPassword = !showPassword"
                  >
                    <EyeOff v-if="showPassword" :size="16" />
                    <Eye v-else :size="16" />
                  </button>
                </span>
              </label>
              <p v-if="problem" class="error-text" role="alert">{{ problem }}</p>
              <button type="submit" class="btn primary lg full" :disabled="submitting">
                <span>{{ submitting ? '正在进入…' : '登录空间' }}</span>
                <ArrowRight :size="16" />
              </button>
            </form>
          </template>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.auth-stage {
  position: relative;
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 28px 24px;
  overflow: hidden;
}
.auth-ambient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(52% 46% at 24% 38%, var(--ambient-1), transparent 72%),
    radial-gradient(46% 42% at 82% 20%, var(--ambient-2), transparent 70%),
    radial-gradient(44% 40% at 62% 88%, var(--ambient-3), transparent 72%);
}
.auth-shell {
  position: relative;
  z-index: 1;
  width: min(100%, 940px);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 420px);
  gap: 44px;
  align-items: center;
}
.auth-card-col {
  width: 100%;
  min-width: 0;
}
.auth-mobile-hero {
  display: none;
}
.auth-card {
  position: relative;
  padding: 34px 32px;
  border-radius: var(--radius-xl);
  display: grid;
  gap: 24px;
  overflow: hidden;
}
.auth-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 16%;
  right: 16%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent-border), transparent);
  pointer-events: none;
}
.auth-head {
  display: grid;
  gap: 6px;
  justify-items: start;
}
.auth-head h1 {
  font-size: 24px;
  font-weight: 720;
  letter-spacing: -0.025em;
}
.auth-head p {
  font-size: 13px;
  line-height: 1.5;
}
.auth-secondary {
  margin-top: -8px;
}
.setup-cmd {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 14px;
  font-family: var(--font-mono);
  font-size: 12.5px;
  overflow-x: auto;
}
.setup-tip {
  font-size: 12px;
  line-height: 1.6;
}
.setup-tip code {
  font-family: var(--font-mono);
  font-size: 11.5px;
  padding: 2px 6px;
  border-radius: 6px;
  background: var(--surface-subtle);
}

@media (max-width: 900px) {
  .auth-stage {
    padding: max(28px, env(safe-area-inset-top)) 16px max(28px, env(safe-area-inset-bottom));
    align-content: center;
  }
  .auth-ambient {
    background:
      radial-gradient(88% 42% at 50% 8%, var(--accent-soft-strong), transparent 72%),
      radial-gradient(64% 38% at 18% 24%, var(--ambient-1), transparent 70%),
      radial-gradient(64% 38% at 86% 84%, var(--ambient-2), transparent 72%);
  }
  .auth-shell {
    grid-template-columns: minmax(0, 410px);
    justify-content: center;
    gap: 0;
  }
  .auth-mobile-hero {
    display: grid;
    justify-items: center;
    gap: 14px;
    margin-bottom: 24px;
    padding-top: 8px;
    text-align: center;
  }
  .mobile-hero-copy {
    display: grid;
    gap: 4px;
  }
  .mobile-hero-copy strong {
    font-size: 22px;
    font-weight: 740;
    letter-spacing: -0.02em;
    color: var(--ink);
  }
  .mobile-hero-copy span {
    font-size: 12.5px;
    letter-spacing: 0.08em;
    color: var(--ink-secondary);
  }
  .auth-card {
    padding: 24px 20px 26px;
    gap: 20px;
    border-radius: 24px;
    background:
      radial-gradient(120% 70% at 50% 0%, var(--accent-soft), transparent 58%),
      var(--surface-glass-strong);
    box-shadow:
      var(--specular),
      0 22px 48px -18px rgba(15, 23, 42, 0.2);
  }
  .auth-head h1 {
    font-size: 20px;
  }
  .auth-head p {
    font-size: 12.5px;
  }
  .auth-card :deep(input:not([type='checkbox']):not([type='radio'])) {
    min-height: 44px;
    font-size: 14px;
  }
  .auth-card :deep(.btn.lg) {
    min-height: 46px;
    font-size: 14.5px;
    border-radius: 14px;
  }
}
</style>
