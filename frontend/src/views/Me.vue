<script setup lang="ts">
import { ref, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { Check, Download, Globe, KeyRound, LogOut, Monitor, Moon, Palette as PaletteIcon, Settings2, Shield, Sun, Upload } from 'lucide-vue-next'
import { api, clearSession, learningRevision, notify, PALETTES, preferences, session, today, updatePreferences } from '../state'
import type { Appearance, BackupCounts, Palette, Preferences } from '../types'
import PasswordForm from '../components/PasswordForm.vue'
import TimerSettings from '../components/TimerSettings.vue'
import GlassModal from '../components/ui/GlassModal.vue'
import PageHeader from '../components/ui/PageHeader.vue'

const router = useRouter()
const busy = ref(false)
const passwordOpen = ref(false)
const settingOpen = ref(false)
const importOpen = ref(false)
const draft = ref<Preferences>({ ...preferences.value })
const picker = ref<HTMLInputElement | null>(null)
const preview = shallowRef<{ token: string; counts: BackupCounts; backup: unknown; name: string } | null>(null)
const importError = ref('')

const appearances: ReadonlyArray<{ id: Appearance; label: string; icon: typeof Sun }> = [
  { id: 'light', label: '浅色通透', icon: Sun },
  { id: 'dark', label: '午夜深色', icon: Moon },
  { id: 'system', label: '跟随系统', icon: Monitor },
]

async function saveSettings(value: Preferences, showMessage = true) {
  busy.value = true
  try {
    updatePreferences(await api<Preferences>('/preferences', 'PUT', value))
    settingOpen.value = false
    if (showMessage) notify('偏好设置已保存')
    return true
  } catch (e) {
    notify((e as Error).message, true)
    return false
  } finally {
    busy.value = false
  }
}

function chooseAppearance(appearance: Appearance) {
  void saveSettings({ ...preferences.value, appearance }, false)
}

function choosePalette(palette: Palette) {
  void saveSettings({ ...preferences.value, palette }, false)
}

async function download() {
  busy.value = true
  try {
    const data = await api<unknown>('/backup')
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `shike-study-${today.value}.json`
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
    notify('学习数据已导出为 JSON')
  } catch (e) {
    notify((e as Error).message, true)
  } finally {
    busy.value = false
  }
}

async function readBackup(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (file.size > 15 * 1024 * 1024) {
    notify('备份文件不能超过 15 MiB', true)
    return
  }
  busy.value = true
  importError.value = ''
  preview.value = null
  try {
    let backup: unknown
    try {
      backup = JSON.parse(await file.text())
    } catch {
      throw new Error('无法解析为有效的 JSON 文件')
    }
    const result = await api<{ token: string; counts: BackupCounts }>('/backup/preview', 'POST', backup)
    preview.value = { ...result, backup, name: file.name }
    importOpen.value = true
  } catch (e) {
    notify((e as Error).message, true)
  } finally {
    busy.value = false
  }
}

async function restore() {
  const value = preview.value
  if (!value) return
  busy.value = true
  importError.value = ''
  try {
    const result = await api<{ preferences: Preferences }>('/backup', 'PUT', { token: value.token, backup: value.backup })
    updatePreferences(result.preferences)
    learningRevision.value++
    importOpen.value = false
    preview.value = null
    notify('账号学习数据已成功恢复')
  } catch (e) {
    importError.value = (e as Error).message
  } finally {
    busy.value = false
  }
}

async function logout() {
  busy.value = true
  try {
    await api('/auth/logout', 'POST')
    clearSession()
    await router.replace({ name: 'today' })
  } catch (e) {
    notify((e as Error).message, true)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page me-page">
    <PageHeader eyebrow="PREFERENCES & ACCOUNT" title="个人空间" subtitle="定制你的视觉氛围、专注目标与数据备份" />

    <!-- Identity Banner -->
    <section class="profile-banner glass-card">
      <span class="avatar-circle big-avatar">{{ session?.user.username.slice(0, 1).toUpperCase() }}</span>
      <div class="profile-copy">
        <h2>{{ session?.user.username }}</h2>
        <span class="pill accent">{{ session?.user.role === 'admin' ? '超级管理员' : '学习账号' }}</span>
      </div>
      <div class="profile-tz glass-inset">
        <Globe :size="15" class="accent-text" />
        <div>
          <small class="tertiary">学习时区</small>
          <strong>{{ session?.timezone }}</strong>
        </div>
      </div>
    </section>

    <div class="me-bento">
      <!-- Appearance & Palette Card -->
      <section class="me-card glass-card">
        <header class="section-title"><PaletteIcon :size="18" /><h2>外观与通透配色</h2></header>

        <div class="appearance-block">
          <div>
            <strong>界面明暗模式</strong>
            <p class="muted">切换浅色通透画布或午夜深色玻璃模式</p>
          </div>
          <div class="segmented" role="group" aria-label="明暗模式">
            <button
              v-for="item in appearances"
              :key="item.id"
              type="button"
              :aria-pressed="preferences.appearance === item.id"
              :disabled="busy"
              @click="chooseAppearance(item.id)"
            >
              <component :is="item.icon" :size="14" />{{ item.label }}
            </button>
          </div>
        </div>

        <div class="palette-block">
          <span class="field-label">主题氛围色</span>
          <div class="palette-grid" role="group" aria-label="主题氛围色">
            <button
              v-for="item in PALETTES"
              :key="item.id"
              type="button"
              class="palette-card"
              :class="{ active: preferences.palette === item.id }"
              :disabled="busy"
              @click="choosePalette(item.id)"
            >
              <span class="swatch-orb" :style="{ background: `linear-gradient(135deg, ${item.swatch}, ${item.swatch2})` }">
                <Check v-if="preferences.palette === item.id" :size="13" color="#fff" :stroke-width="3" />
              </span>
              <span class="palette-meta">
                <strong>{{ item.label }}</strong>
                <small class="tertiary">{{ item.desc }}</small>
              </span>
            </button>
          </div>
        </div>
      </section>

      <!-- Focus & Data Column -->
      <div class="me-side">
        <section class="me-card glass-card">
          <header class="section-title"><Settings2 :size="18" /><h2>专注与目标偏好</h2></header>
          <div class="setting-row compact">
            <div>
              <strong>番茄钟与每日目标</strong>
              <p class="muted tabular">
                专注 {{ preferences.focus_minutes }}m · 休息 {{ preferences.break_minutes }}m · 每日目标 {{ Math.round(preferences.daily_focus_goal_minutes / 60 * 10) / 10 }}h
              </p>
            </div>
            <button type="button" class="btn secondary sm" :disabled="busy" @click="draft = { ...preferences }; settingOpen = true">
              调整
            </button>
          </div>
        </section>

        <section class="me-card glass-card">
          <header class="section-title"><Shield :size="18" /><h2>数据备份与安全</h2></header>
          <div class="setting-row compact">
            <div>
              <strong>导出个人学习数据</strong>
              <p class="muted">包含全部计划、打卡、复盘、专注与里程碑（JSON）</p>
            </div>
            <button type="button" class="btn secondary sm" :disabled="busy" @click="download">
              <Download :size="14" />导出
            </button>
          </div>
          <div class="setting-row compact">
            <div>
              <strong>导入并恢复备份</strong>
              <p class="muted">兼容原版 v1 及新版 v2 备份，覆盖前服务端自动留存回滚副本</p>
            </div>
            <button type="button" class="btn secondary sm" :disabled="busy" @click="picker?.click()">
              <Upload :size="14" />导入
            </button>
            <input ref="picker" type="file" accept=".json,application/json" hidden @change="readBackup" />
          </div>
          <div class="setting-row compact">
            <div>
              <strong>修改登录密码</strong>
              <p class="muted">修改后会自动注销其他设备上的会话</p>
            </div>
            <button type="button" class="btn secondary sm" :disabled="busy" @click="passwordOpen = true">
              <KeyRound :size="14" />改密
            </button>
          </div>
        </section>

        <div class="logout-bar">
          <button type="button" class="btn danger-ghost" :disabled="busy" @click="logout">
            <LogOut :size="15" />退出当前账号
          </button>
        </div>
      </div>
    </div>

    <GlassModal v-model="passwordOpen" title="修改账号密码">
      <PasswordForm @saved="passwordOpen = false" />
    </GlassModal>

    <GlassModal v-model="settingOpen" title="专注与目标设置" :busy="busy">
      <TimerSettings v-model="draft" :busy="busy" @save="saveSettings(draft)" />
    </GlassModal>

    <GlassModal v-model="importOpen" title="确认导入并覆盖学习数据" :busy="busy">
      <div v-if="preview" class="form-stack">
        <strong class="break-text">{{ preview.name }}</strong>
        <p class="muted">
          包含 {{ preview.counts.plans }} 个计划版本 · {{ preview.counts.days }} 天记录 · {{ preview.counts.focus }} 次专注 · {{ preview.counts.categories }} 个分类<template v-if="preview.counts.milestones"> · {{ preview.counts.milestones }} 个里程碑</template>
        </p>
        <p class="muted">确认后将覆盖当前账号在线学习数据；服务端会先自动保存一份回滚副本。</p>
        <p v-if="importError" class="error-text" role="alert">{{ importError }}</p>
        <div class="dialog-actions">
          <button type="button" class="btn ghost" :disabled="busy" @click="importOpen = false">取消</button>
          <button type="button" class="btn danger" :disabled="busy" @click="restore"><Upload :size="15" />确认覆盖导入</button>
        </div>
      </div>
    </GlassModal>
  </div>
</template>

<style scoped>
.me-page {
  max-width: 1120px;
}
.profile-banner {
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 20px;
  background:
    radial-gradient(60% 120% at 100% 0%, var(--accent-soft), transparent 68%),
    var(--surface-glass);
}
.big-avatar {
  width: 54px;
  height: 54px;
  font-size: 21px;
}
.profile-copy {
  display: grid;
  gap: 6px;
  justify-items: start;
  flex: 1;
}
.profile-copy h2 {
  font-size: 20px;
  font-weight: 720;
  letter-spacing: -0.02em;
}
.profile-tz {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
}
.profile-tz small {
  display: block;
  font-size: 11px;
}
.profile-tz strong {
  font-size: 13px;
}

.me-bento {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}
.me-side {
  display: grid;
  gap: 18px;
}
.me-card {
  padding: 20px 22px;
  display: grid;
  gap: 16px;
}
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}
.setting-row > div {
  flex: 1;
  min-width: 0;
}
.setting-row > .btn,
.setting-row > .segmented {
  flex: none;
}
.setting-row:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}
.setting-row strong {
  display: block;
  font-size: 14px;
  font-weight: 620;
}
.setting-row p {
  margin-top: 2px;
  font-size: 12px;
}
.appearance-block {
  display: grid;
  gap: 10px;
  justify-items: start;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}
.appearance-block strong {
  display: block;
  font-size: 14px;
  font-weight: 620;
}
.appearance-block p {
  margin-top: 2px;
  font-size: 12px;
}
.palette-block {
  display: grid;
  gap: 10px;
}
.palette-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(145px, 1fr));
  gap: 10px;
}
.palette-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 12px;
  border-radius: 14px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  text-align: left;
  transition: background 0.16s, border-color 0.16s, transform 0.16s;
}
.palette-card:hover {
  background: var(--surface-solid);
}
.palette-card.active {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}
.swatch-orb {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  flex: none;
  display: grid;
  place-items: center;
  box-shadow: 0 3px 10px -2px rgba(0, 0, 0, 0.25);
}
.palette-meta {
  display: grid;
  line-height: 1.25;
}
.palette-meta strong {
  font-size: 13px;
  font-weight: 630;
}
.palette-meta small {
  font-size: 11px;
}
.logout-bar {
  display: flex;
  justify-content: flex-start;
}

@media (max-width: 900px) {
  .me-bento {
    grid-template-columns: 1fr;
    gap: 14px;
  }
}
@media (max-width: 768px) {
  .profile-banner {
    padding: 14px;
    gap: 12px;
    margin-bottom: 14px;
  }
  .big-avatar {
    width: 44px;
    height: 44px;
    font-size: 17px;
  }
  .profile-copy h2 {
    font-size: 17px;
  }
  .profile-tz {
    width: 100%;
    padding: 8px 12px;
  }
  .me-side {
    gap: 14px;
  }
  .me-card {
    padding: 15px 14px;
    gap: 12px;
  }
  .appearance-block .segmented {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .palette-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .palette-card {
    padding: 9px 10px;
    gap: 8px;
    border-radius: 12px;
  }
  .swatch-orb {
    width: 22px;
    height: 22px;
  }
  .setting-row {
    gap: 10px;
    padding: 10px 0;
  }
  .setting-row strong {
    font-size: 13.5px;
  }
  .logout-bar .btn {
    width: 100%;
    background: var(--danger-soft);
  }
}
</style>
