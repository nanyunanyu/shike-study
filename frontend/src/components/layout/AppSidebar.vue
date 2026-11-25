<script setup lang="ts">
import { computed, type Component } from 'vue'
import { Bell } from 'lucide-vue-next'
import BrandMark from '@/components/ui/BrandMark.vue'
import { preferences, session, todayFocusSeconds } from '@/stores/session'
import { duration } from '@/utils/date'

export interface NavItem {
  name: string
  label: string
  icon: Component
}

defineProps<{
  navItems: NavItem[]
  unread: number
}>()

const emit = defineEmits<{ openInbox: [] }>()

const goalRatio = computed(() =>
  Math.min(100, Math.round((todayFocusSeconds.value / Math.max(60, preferences.value.daily_focus_goal_minutes * 60)) * 100)),
)
</script>

<template>
  <aside v-if="session" class="glass-sidebar glass-card" aria-label="侧边导航栏">
    <RouterLink :to="{ name: 'today' }" class="sidebar-brand" aria-label="拾刻学习">
      <BrandMark />
    </RouterLink>

    <nav class="sidebar-nav" aria-label="主导航">
      <RouterLink
        v-for="item in navItems"
        :key="item.name"
        :to="{ name: item.name }"
        class="nav-pill"
        :class="{ 'is-admin': item.name === 'admin' }"
      >
        <component :is="item.icon" :size="18" :stroke-width="1.9" />
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="sidebar-foot">
      <div class="mini-goal glass-inset">
        <div class="mini-goal-head">
          <span>今日专注目标</span>
          <strong class="tabular">{{ goalRatio }}%</strong>
        </div>
        <div class="mini-goal-track">
          <span :style="{ width: `${goalRatio}%` }"></span>
        </div>
        <small class="tertiary tabular">
          {{ duration(todayFocusSeconds) }} / {{ Math.round((preferences.daily_focus_goal_minutes / 60) * 10) / 10 }} 小时
        </small>
      </div>

      <button v-if="session.user.role === 'user'" type="button" class="bell-row" @click="emit('openInbox')">
        <Bell :size="17" />
        <span>消息中心</span>
        <span v-if="unread" class="unread-badge tabular">{{ unread > 99 ? '99+' : unread }}</span>
      </button>

      <RouterLink :to="{ name: 'me' }" class="account-pill">
        <span class="avatar-circle">{{ session.user.username.slice(0, 1).toUpperCase() }}</span>
        <span class="account-meta">
          <strong>{{ session.user.username }}</strong>
          <small>{{ session.user.role === 'admin' ? '超级管理员' : '学习者' }}</small>
        </span>
      </RouterLink>
    </div>
  </aside>
</template>

<style scoped>
.glass-sidebar {
  position: fixed;
  top: var(--sidebar-gap);
  left: var(--sidebar-gap);
  bottom: var(--sidebar-gap);
  width: var(--sidebar-w);
  z-index: 40;
  padding: 20px 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  border-radius: 24px;
}

.sidebar-brand {
  padding: 2px 6px;
}

.sidebar-nav {
  display: grid;
  gap: 4px;
}

.nav-pill {
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 42px;
  padding: 0 13px;
  border-radius: 13px;
  color: var(--ink-secondary);
  font-size: 13.5px;
  font-weight: 560;
  transition: background 0.18s var(--ease-out), color 0.18s, transform 0.15s;
}

.nav-pill:hover {
  background: var(--surface-hover);
  color: var(--ink);
}

.nav-pill.router-link-exact-active {
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 640;
  box-shadow: inset 0 0 0 1px var(--accent-border);
}

.nav-pill.is-admin {
  margin-top: 10px;
  position: relative;
}

.nav-pill.is-admin::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 10px;
  right: 10px;
  height: 1px;
  background: var(--border);
}

.sidebar-foot {
  margin-top: auto;
  display: grid;
  gap: 10px;
}

.mini-goal {
  padding: 11px 12px;
  display: grid;
  gap: 7px;
  border-radius: 14px;
}

.mini-goal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11.5px;
  color: var(--ink-secondary);
}

.mini-goal-head strong {
  color: var(--accent);
  font-weight: 680;
}

.mini-goal-track {
  height: 5px;
  border-radius: var(--radius-pill);
  background: var(--surface-hover);
  overflow: hidden;
}

.mini-goal-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  transition: width 0.5s var(--ease-spring);
}

.mini-goal small {
  font-size: 11px;
}

.bell-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 38px;
  padding: 0 12px;
  border-radius: 12px;
  color: var(--ink-secondary);
  font-size: 13px;
  font-weight: 560;
  transition: background 0.16s, color 0.16s;
}

.bell-row:hover {
  background: var(--surface-hover);
  color: var(--ink);
}

.unread-badge {
  margin-left: auto;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: var(--radius-pill);
  background: var(--accent);
  color: var(--on-accent);
  font-size: 11px;
  font-weight: 700;
  display: grid;
  place-items: center;
}

.account-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--surface-subtle);
  transition: background 0.18s, border-color 0.18s;
}

.account-pill:hover {
  background: var(--surface-hover);
  border-color: var(--border-strong);
}

.account-meta {
  min-width: 0;
  display: grid;
  line-height: 1.2;
}

.account-meta strong {
  font-size: 13px;
  font-weight: 630;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-meta small {
  margin-top: 2px;
  font-size: 11px;
  color: var(--ink-tertiary);
}

@media (max-width: 768px) {
  .glass-sidebar {
    display: none;
  }
}
</style>
