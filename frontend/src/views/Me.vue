<script setup lang="ts">
import { computed, ref, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { Download, Globe, KeyRound, LogOut, Settings2, Shield, Upload } from 'lucide-vue-next'
import { logoutApi } from '@/api/auth'
import { commitBackupApi, exportBackupApi, previewBackupApi } from '@/api/backup'
import PasswordForm from '@/components/auth/PasswordForm.vue'
import AppearanceSection from '@/components/me/AppearanceSection.vue'
import BackupImportModal from '@/components/me/BackupImportModal.vue'
import TimerSettings from '@/components/timer/TimerSettings.vue'
import GlassModal from '@/components/ui/GlassModal.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { usePreferencesActions } from '@/composables/usePreferencesActions'
import { bumpLearningRevision, clearSession, preferences, session, today, updatePreferences } from '@/stores/session'
import { notify } from '@/stores/ui'
import type { Appearance, BackupCounts, Palette, Preferences } from '@/types'
import { downloadJson, readJsonFile } from '@/utils/file'

const router = useRouter()
const { saving: savingPrefs, savePreferences } = usePreferencesActions()

const actionBusy = ref(false)
const busy = computed(() => actionBusy.value || savingPrefs.value)
const passwordOpen = ref(false)
const settingOpen = ref(false)
const importOpen = ref(false)
const draft = ref<Preferences>({ ...preferences.value })
const picker = ref<HTMLInputElement | null>(null)
const preview = shallowRef<{ token: string; counts: BackupCounts; backup: unknown; name: string } | null>(null)
const importError = ref('')

async function saveTimerPrefs() {
  if (await savePreferences(draft.value, '偏好设置已保存')) settingOpen.value = false
}

function chooseAppearance(appearance: Appearance) {
  void savePreferences({ ...preferences.value, appearance })
}

function choosePalette(palette: Palette) {
  void savePreferences({ ...preferences.value, palette })
}

async function download() {
  actionBusy.value = true
  try {
    const data = await exportBackupApi()
    downloadJson(`shike-study-${today.value}.json`, data)
    notify('学习数据已导出为 JSON')
  } catch (e) {
    notify((e as Error).message, true)
  } finally {
    actionBusy.value = false
  }
}

async function readBackup(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  actionBusy.value = true
  importError.value = ''
  preview.value = null
  try {
    const backup = await readJsonFile(file)
    const result = await previewBackupApi(backup)
    preview.value = { ...result, backup, name: file.name }
    importOpen.value = true
  } catch (e) {
    notify((e as Error).message, true)
  } finally {
    actionBusy.value = false
  }
}

async function restore() {
  const value = preview.value
  if (!value) return
  actionBusy.value = true
  importError.value = ''
  try {
    const result = await commitBackupApi(value.token, value.backup)
    updatePreferences(result.preferences)
    bumpLearningRevision()
    importOpen.value = false
    preview.value = null
    notify('账号学习数据已成功恢复')
  } catch (e) {
    importError.value = (e as Error).message
  } finally {
    actionBusy.value = false
  }
}

async function logout() {
  actionBusy.value = true
  try {
    await logoutApi()
    clearSession()
    await router.replace({ name: 'today' })
  } catch (e) {
    notify((e as Error).message, true)
  } finally {
    actionBusy.value = false
  }
}
</script>

<template>
  <div class="page me-page">
    <PageHeader eyebrow="PREFERENCES & ACCOUNT" title="个人空间" subtitle="定制你的视觉氛围、专注目标与数据备份" />

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
      <AppearanceSection
        :appearance="preferences.appearance"
        :palette="preferences.palette"
        :busy="busy"
        @choose-appearance="chooseAppearance"
        @choose-palette="choosePalette"
      />

      <div class="me-side">
        <section class="me-card glass-card">
          <header class="section-title"><Settings2 :size="18" /><h2>专注与目标偏好</h2></header>
          <div class="setting-row compact">
            <div>
              <strong>番茄钟与每日目标</strong>
              <p class="muted tabular">
                专注 {{ preferences.focus_minutes }}m · 休息 {{ preferences.break_minutes }}m · 每日目标
                {{ Math.round((preferences.daily_focus_goal_minutes / 60) * 10) / 10 }}h
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
          <button type="button" class="btn danger-ghost pill" :disabled="busy" @click="logout">
            <LogOut :size="15" />退出当前账号
          </button>
        </div>
      </div>
    </div>

    <GlassModal v-model="passwordOpen" title="修改账号密码">
      <PasswordForm @saved="passwordOpen = false" />
    </GlassModal>

    <GlassModal v-model="settingOpen" title="专注与目标设置" :busy="busy">
      <TimerSettings v-model="draft" :busy="busy" @save="saveTimerPrefs" />
    </GlassModal>

    <BackupImportModal v-model="importOpen" :preview="preview" :busy="busy" :error="importError" @confirm="restore" />
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
  .setting-row {
    gap: 10px;
    padding: 10px 0;
  }
  .setting-row strong {
    font-size: 13.5px;
  }
  .logout-bar {
    justify-content: flex-start;
  }
  .logout-bar .btn {
    background: var(--danger-soft);
    padding: 0 18px;
  }
}
</style>
