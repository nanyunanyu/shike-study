<script setup lang="ts">
import { CheckCircle2, Flag, Share2, Sparkles } from 'lucide-vue-next'
import ProgressRing from '@/components/ui/ProgressRing.vue'
import type { Milestone } from '@/types'
import type { CelebrationOrigin } from '@/utils/celebrationEngine'

defineProps<{
  complete: number
  total: number
  percent: number
  rate: number
  focusRatio: number
  editable: boolean
  checked: boolean
  busy: boolean
  currentStreak: number
  pinnedMilestones: Milestone[]
  justChecked?: boolean
}>()

const emit = defineEmits<{
  checkIn: [origin: CelebrationOrigin]
  share: []
}>()

function onCheckInClick(event: MouseEvent) {
  const target = event.currentTarget as HTMLElement | null
  const rect = target?.getBoundingClientRect()
  const origin: CelebrationOrigin =
    rect && (rect.width > 0 || rect.height > 0)
      ? { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }
      : { x: window.innerWidth / 2, y: window.innerHeight * 0.42 }
  emit('checkIn', origin)
}
</script>

<template>
  <section class="hero-card glass-card">
    <div class="hero-left">
      <div class="hero-badges">
        <span class="pill accent"><Sparkles :size="12" />连续打卡 {{ currentStreak }} 天</span>
        <RouterLink
          v-for="ms in pinnedMilestones"
          :key="ms.id"
          :to="{ name: 'stats' }"
          class="pill milestone-pill"
          :title="ms.note || ms.target_date"
        >
          <Flag :size="12" class="accent-text" />
          <span>{{ ms.title }}</span>
          <strong class="tabular">{{ ms.days_left >= 0 ? `还剩 ${ms.days_left} 天` : `已过 ${-ms.days_left} 天` }}</strong>
        </RouterLink>
      </div>

      <div class="hero-headline">
        <strong class="hero-big tabular">{{ complete }}<span> / {{ total }}</span></strong>
        <span class="muted">项日程任务已完成</span>
      </div>

      <div class="hero-actions">
        <button
          v-if="editable"
          type="button"
          class="btn lg pill checkin-btn"
          :class="[checked ? 'tinted' : 'primary', { 'is-celebrating': justChecked }]"
          :disabled="busy"
          :title="checked ? '点击可取消今日打卡' : '完成今日打卡'"
          @click="onCheckInClick"
        >
          <CheckCircle2 :size="17" class="checkin-icon" />
          <span>{{ checked ? '今日已打卡' : '完成今日打卡' }}</span>
        </button>
        <span v-else-if="checked" class="pill success" style="padding: 7px 12px; font-size: 12.5px">
          <CheckCircle2 :size="14" />当日已打卡
        </span>
        <button
          type="button"
          class="btn secondary lg share-btn"
          aria-label="分享海报"
          title="分享海报"
          @click="emit('share')"
        >
          <Share2 :size="16" />
        </button>
      </div>
    </div>

    <div class="hero-rings">
      <div class="ring-card glass-inset">
        <div class="ring-visual">
          <ProgressRing :progress="rate" :size="96" :stroke="8" />
          <div class="ring-center">
            <strong class="tabular">{{ total ? `${percent}%` : '—' }}</strong>
            <small class="tertiary">任务率</small>
          </div>
        </div>
      </div>

      <div class="ring-card glass-inset">
        <div class="ring-visual">
          <ProgressRing :progress="focusRatio" :size="96" :stroke="8" tone="secondary" />
          <div class="ring-center">
            <strong class="tabular">{{ Math.round(focusRatio * 100) }}%</strong>
            <small class="tertiary">专注目标</small>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero-card {
  position: relative;
  overflow: hidden;
  padding: 26px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 22px;
  background:
    radial-gradient(60% 120% at 100% 0%, var(--accent-soft), transparent 68%),
    var(--surface-glass);
}
.hero-left {
  display: grid;
  gap: 14px;
  min-width: 0;
}
.hero-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.milestone-pill {
  transition: background 0.16s, border-color 0.16s;
}
.milestone-pill:hover {
  background: var(--surface-solid);
  border-color: var(--accent-border);
}
.milestone-pill strong {
  color: var(--accent);
}
.hero-headline {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}
.hero-big {
  font-size: 40px;
  font-weight: 760;
  line-height: 1;
  letter-spacing: -0.04em;
}
.hero-big span {
  font-size: 22px;
  font-weight: 560;
  color: var(--ink-tertiary);
}
.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.share-btn {
  width: 44px;
  height: 44px;
  min-height: 44px;
  padding: 0;
  border-radius: 50%;
  flex: none;
}
.checkin-btn.is-celebrating {
  animation: checkin-btn-pulse 0.54s var(--ease-spring);
}
.checkin-btn.is-celebrating .checkin-icon {
  animation: check-pop 0.44s var(--ease-spring);
}
@keyframes checkin-btn-pulse {
  0% {
    box-shadow: 0 0 0 0 var(--accent-ring);
  }
  45% {
    transform: scale(1.035);
    box-shadow: 0 0 0 10px transparent;
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 transparent;
  }
}
.hero-rings {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: none;
}
.ring-card {
  padding: 14px;
  border-radius: 20px;
}
.ring-visual {
  position: relative;
  display: grid;
  place-items: center;
}
.ring-center {
  position: absolute;
  text-align: center;
  line-height: 1.15;
}
.ring-center strong {
  display: block;
  font-size: 20px;
  font-weight: 740;
  letter-spacing: -0.03em;
}
.ring-center small {
  display: block;
  margin-top: 2px;
  font-size: 10.5px;
}

@media (max-width: 980px) {
  .hero-card {
    flex-direction: column;
    align-items: stretch;
    padding: 20px;
  }
  .hero-rings {
    justify-content: flex-start;
  }
}
@media (max-width: 768px) {
  .hero-card {
    padding: 15px 14px;
    gap: 14px;
    margin-bottom: 14px;
  }
  .hero-left {
    gap: 11px;
  }
  .hero-badges {
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: 2px;
  }
  .hero-badges::-webkit-scrollbar {
    display: none;
  }
  .hero-big {
    font-size: 30px;
  }
  .hero-big span {
    font-size: 17px;
  }
  .hero-headline {
    gap: 7px;
    font-size: 12.5px;
  }
  .hero-actions {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }
  .share-btn {
    width: 38px;
    height: 38px;
    min-height: 38px;
  }
  .hero-rings {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .ring-card {
    padding: 10px;
    border-radius: 14px;
    display: grid;
    place-items: center;
  }
  .ring-visual :deep(.progress-ring) {
    width: 68px;
    height: 68px;
  }
  .ring-center strong {
    font-size: 15px;
  }
  .ring-center small {
    font-size: 9.5px;
  }
}
</style>
