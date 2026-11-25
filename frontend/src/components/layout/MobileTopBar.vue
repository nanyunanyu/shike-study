<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { Bell } from 'lucide-vue-next'
import BrandMark from '@/components/ui/BrandMark.vue'
import { session } from '@/stores/session'
import { timer, timerSeconds } from '@/stores/timer'
import { timerText } from '@/utils/date'

defineProps<{ unread: number }>()
const emit = defineEmits<{ openInbox: [] }>()
const route = useRoute()

const el = ref<HTMLElement | null>(null)
defineExpose({ el })
</script>

<template>
  <header v-if="session" ref="el" class="mobile-bar">
    <RouterLink :to="{ name: 'today' }" aria-label="拾刻学习">
      <BrandMark compact />
    </RouterLink>
    <div class="mobile-bar-right">
      <RouterLink
        v-if="timer && route.name !== 'timer'"
        :to="{ name: 'timer' }"
        class="mobile-live-timer tabular"
        aria-label="查看进行中的专注计时"
      >
        <span class="live-dot" :class="{ paused: timer.running_since === null }"></span>
        <span>{{ timerText(timerSeconds) }}</span>
      </RouterLink>
      <button
        v-if="session.user.role === 'user'"
        type="button"
        class="icon-btn mobile-bell"
        aria-label="消息中心"
        @click="emit('openInbox')"
      >
        <Bell :size="18" />
        <span v-if="unread" class="mobile-badge tabular">{{ unread > 99 ? '99+' : unread }}</span>
      </button>
      <RouterLink :to="{ name: 'me' }" class="avatar-circle mobile-avatar" aria-label="我的账号">
        {{ session.user.username.slice(0, 1).toUpperCase() }}
      </RouterLink>
    </div>
  </header>
</template>

<style scoped>
.mobile-bar {
  display: none;
}

@media (max-width: 768px) {
  .mobile-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 40;
    padding: max(8px, env(safe-area-inset-top)) 14px 8px;
    background: var(--surface-glass);
    backdrop-filter: blur(22px) saturate(175%);
    -webkit-backdrop-filter: blur(22px) saturate(175%);
    border-bottom: 1px solid var(--border);
  }
  .mobile-bar-right {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .mobile-live-timer {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: var(--radius-pill);
    background: var(--accent-soft);
    border: 1px solid var(--accent-border);
    color: var(--accent);
    font-size: 12px;
    font-weight: 660;
  }
  .live-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse-soft 1.6s infinite;
  }
  .live-dot.paused {
    animation: none;
    opacity: 0.45;
  }
  .mobile-bell {
    position: relative;
  }
  .mobile-badge {
    position: absolute;
    top: 2px;
    right: 2px;
    min-width: 15px;
    height: 15px;
    padding: 0 3.5px;
    border-radius: var(--radius-pill);
    background: var(--accent);
    color: var(--on-accent);
    font-size: 9.5px;
    font-weight: 700;
    display: grid;
    place-items: center;
  }
  .mobile-avatar {
    width: 30px;
    height: 30px;
    font-size: 12.5px;
  }
}
</style>
