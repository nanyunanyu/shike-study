<script setup lang="ts">
import { ArrowRight, CheckCircle2, Clock3, Eye, EyeOff, LogOut, Sparkles, Terminal } from 'lucide-vue-next'
import { ref } from 'vue'
import BrandMark from './ui/BrandMark.vue'
import ProgressRing from './ui/ProgressRing.vue'
import PasswordForm from './PasswordForm.vue'
import { api, clearSession, session, setSession } from '../state'
import type { Session } from '../types'

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
    setSession(await api<Session>('/auth/login', 'POST', { username: username.value, password: password.value }))
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
    await api('/auth/logout', 'POST')
    clearSession()
  } catch (e) {
    problem.value = (e as Error).message
  }
}
</script>

<template>
  <main class="auth-stage">
    <div class="auth-shell">
      <!-- Left: Serene Apple/Craft frosted visual showcase -->
      <section class="auth-showcase" aria-hidden="true">
        <div class="showcase-top">
          <BrandMark />
        </div>

        <div class="showcase-center">
          <p class="showcase-kicker"><Sparkles :size="14" />安静而克制的个人学习空间</p>
          <h2>拾起每一刻专注，<br />让进步清晰可见。</h2>
          <p class="showcase-lead">
            以时间轴理顺一日节奏，在无干扰专注剧场与柔润环境音中进入心流，用复盘手账记录每一次细微成长。
          </p>

          <!-- Decorative floating glass preview cards -->
          <div class="preview-stack">
            <div class="preview-hero glass-card">
              <div class="preview-ring-box">
                <ProgressRing :progress="0.78" :size="76" :stroke="6.5" />
                <span class="preview-ring-num tabular">78%</span>
              </div>
              <div class="preview-hero-copy">
                <span class="pill accent">连续打卡 14 天</span>
                <strong>今日专注 3 小时 15 分钟</strong>
                <small class="muted">18 / 23 项学习任务已完成</small>
              </div>
            </div>

            <div class="preview-row">
              <div class="preview-mini glass-card">
                <span class="mini-dot"></span>
                <div>
                  <strong>08:35 · 专题网课精听</strong>
                  <small class="muted">进行中 · 沉浸专注 45 分钟</small>
                </div>
                <Clock3 :size="15" class="accent-text" />
              </div>
              <div class="preview-mini glass-card">
                <CheckCircle2 :size="16" class="success-icon" />
                <div>
                  <strong>晨背古诗文与核心词组</strong>
                  <small class="muted">已完成 · 收获笔记已归档</small>
                </div>
              </div>
            </div>
          </div>
        </div>

        <footer class="showcase-foot">
          <span>本地数据主权 · 每日自动快照 · 跨端轻透体验</span>
        </footer>
      </section>

      <!-- Right: Clean frosted auth card -->
      <section class="auth-card-col">
        <div class="auth-mobile-brand">
          <BrandMark />
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
              <p class="muted">首次启动尚无管理员账号，请在终端项目目录执行以下命令创建：</p>
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
              <p class="muted">登录你的拾刻学习账号，延续今日专注节奏。</p>
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
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 24px;
}
.auth-shell {
  width: min(100%, 1080px);
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 440px);
  gap: 32px;
  align-items: center;
}
.auth-showcase {
  display: grid;
  gap: 32px;
  padding: 24px 12px;
}
.showcase-kicker {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 620;
  width: fit-content;
}
.showcase-center {
  display: grid;
  gap: 16px;
}
.showcase-center h2 {
  font-size: clamp(28px, 3.2vw, 38px);
  font-weight: 740;
  line-height: 1.22;
  letter-spacing: -0.03em;
}
.showcase-lead {
  max-width: 48ch;
  font-size: 14.5px;
  line-height: 1.7;
  color: var(--ink-secondary);
}
.preview-stack {
  display: grid;
  gap: 12px;
  margin-top: 8px;
}
.preview-hero {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 18px 20px;
}
.preview-ring-box {
  position: relative;
  display: grid;
  place-items: center;
  flex: none;
}
.preview-ring-num {
  position: absolute;
  font-size: 17px;
  font-weight: 720;
  letter-spacing: -0.02em;
}
.preview-hero-copy {
  display: grid;
  gap: 5px;
  justify-items: start;
}
.preview-hero-copy strong {
  font-size: 16px;
  font-weight: 680;
  letter-spacing: -0.015em;
}
.preview-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.preview-mini {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 14px 15px;
  border-radius: var(--radius-md);
}
.preview-mini > div {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 2px;
}
.preview-mini strong {
  font-size: 12.5px;
  font-weight: 620;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.preview-mini small {
  font-size: 11px;
}
.mini-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-soft);
  flex: none;
}
.success-icon {
  color: var(--success);
}
.showcase-foot {
  font-size: 12px;
  color: var(--ink-tertiary);
}
.auth-mobile-brand {
  display: none;
  justify-content: center;
  margin-bottom: 18px;
}
.auth-card {
  padding: 32px 30px;
  border-radius: var(--radius-xl);
  display: grid;
  gap: 22px;
}
.auth-head {
  display: grid;
  gap: 8px;
  justify-items: start;
}
.auth-head h1 {
  font-size: 24px;
  font-weight: 720;
  letter-spacing: -0.025em;
}
.auth-head p {
  font-size: 13.5px;
  line-height: 1.55;
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
    padding: 16px 14px;
  }
  .auth-shell {
    grid-template-columns: minmax(0, 420px);
    justify-content: center;
  }
  .auth-showcase {
    display: none;
  }
  .auth-mobile-brand {
    display: flex;
    margin-bottom: 14px;
  }
  .auth-card {
    padding: 22px 18px;
    gap: 18px;
    border-radius: 20px;
  }
  .auth-head h1 {
    font-size: 21px;
  }
  .auth-head p {
    font-size: 12.5px;
  }
}
</style>
