<script setup lang="ts">
import { computed } from 'vue'
import { ArrowRight, CalendarCheck, Clock3, Mail } from 'lucide-vue-next'
import type { AdminOverview } from '@/types'
import { duration } from '@/utils/date'

const props = defineProps<{ snapshot: AdminOverview }>()

const checkinPercent = computed(() =>
  props.snapshot.active_accounts ? Math.round((props.snapshot.checked_today / props.snapshot.active_accounts) * 100) : 0,
)
const maxChecked = computed(() => Math.max(1, ...props.snapshot.trend.map(day => day.checked)))
const maxFocus = computed(() => Math.max(1, ...props.snapshot.trend.map(day => day.focus_seconds)))
</script>

<template>
  <div class="admin-overview">
    <div class="admin-top-bento">
      <section class="glass-card attendance-card">
        <div class="section-head">
          <div class="section-title"><CalendarCheck :size="18" /><h2>今日打卡率</h2></div>
          <span class="tertiary tabular">{{ snapshot.date }}</span>
        </div>
        <p class="attendance-val tabular">
          <strong>{{ snapshot.checked_today }}</strong>
          <span class="muted">/ {{ snapshot.active_accounts }} 位已启用学习者</span>
        </p>
        <div class="att-bar-wrap">
          <div class="att-track"><span :style="{ width: `${checkinPercent}%` }"></span></div>
          <strong class="tabular">{{ snapshot.active_accounts ? `${checkinPercent}%` : '—' }}</strong>
        </div>
        <RouterLink
          v-if="snapshot.active_accounts > 0"
          class="att-link"
          :to="{ name: 'admin', query: { section: 'accounts', active: 'enabled', checkin: 'unchecked' } }"
        >
          查看今日未打卡 · {{ snapshot.active_accounts - snapshot.checked_today }} 人 <ArrowRight :size="14" />
        </RouterLink>
      </section>

      <div class="admin-side-metrics">
        <section class="glass-card metric-tile">
          <span class="metric-icon"><Clock3 :size="18" /></span>
          <div>
            <small class="muted">今日全员专注</small>
            <strong class="tabular">{{ duration(snapshot.focus_seconds) }}</strong>
          </div>
        </section>
        <RouterLink to="/admin?section=messages&status=pending" class="glass-card metric-tile link-tile">
          <span class="metric-icon"><Mail :size="18" /></span>
          <div>
            <small class="muted">待发定时消息</small>
            <strong class="tabular">{{ snapshot.pending_dispatches }} 批</strong>
          </div>
          <ArrowRight :size="16" class="tertiary" style="margin-left: auto" />
        </RouterLink>
      </div>
    </div>

    <section class="glass-card trend-panel">
      <div class="section-head">
        <h2>最近 7 天动态</h2>
        <span class="tertiary" style="font-size: 12px">统计范围：已启用学习账号</span>
      </div>
      <div class="week-rows">
        <div
          v-for="day in snapshot.trend"
          :key="day.date"
          class="week-row"
          :class="{ today: day.date === snapshot.date }"
        >
          <div class="week-date tabular">
            <strong>{{ day.date.slice(5).replace('-', '/') }}</strong>
            <span v-if="day.date === snapshot.date" class="pill accent">今天</span>
          </div>
          <div class="week-meter">
            <span class="meter-bar"><i :style="{ width: `${(day.checked / maxChecked) * 100}%` }"></i></span>
            <span class="meter-text tabular">{{ day.checked }} 人打卡</span>
          </div>
          <div class="week-meter">
            <span class="meter-bar alt"><i :style="{ width: `${(day.focus_seconds / maxFocus) * 100}%` }"></i></span>
            <span class="meter-text tabular">{{ duration(day.focus_seconds) }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.admin-overview {
  display: grid;
  gap: 18px;
}
.admin-top-bento {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(260px, 1fr);
  gap: 18px;
}
.attendance-card {
  padding: 22px 24px;
  display: grid;
  gap: 14px;
}
.attendance-val strong {
  font-size: 38px;
  font-weight: 760;
  letter-spacing: -0.04em;
  margin-right: 8px;
}
.att-bar-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}
.att-track {
  flex: 1;
  height: 8px;
  border-radius: var(--radius-pill);
  background: var(--surface-subtle);
  overflow: hidden;
}
.att-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
}
.att-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 590;
  color: var(--accent);
}
.admin-side-metrics {
  display: grid;
  gap: 14px;
}
.metric-tile {
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.link-tile:hover {
  border-color: var(--accent-border);
}
.metric-icon {
  width: 42px;
  height: 42px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  flex: none;
  background: var(--accent-soft);
  color: var(--accent);
}
.metric-tile small {
  display: block;
  font-size: 12px;
}
.metric-tile strong {
  font-size: 22px;
  font-weight: 740;
  letter-spacing: -0.025em;
}
.trend-panel {
  padding: 20px 22px;
  display: grid;
  gap: 16px;
}
.trend-panel h2 {
  font-size: 16px;
  font-weight: 680;
}
.week-rows {
  display: grid;
  gap: 8px;
}
.week-row {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr) minmax(0, 1fr);
  align-items: center;
  gap: 16px;
  padding: 11px 14px;
  border-radius: 14px;
  background: var(--surface-subtle);
}
.week-row.today {
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
}
.week-date {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
}
.week-meter {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.meter-bar {
  flex: 1;
  height: 7px;
  border-radius: var(--radius-pill);
  background: var(--surface-hover);
  overflow: hidden;
}
.meter-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
}
.meter-bar.alt i {
  background: var(--accent-2);
}
.meter-text {
  font-size: 12.5px;
  font-weight: 560;
  white-space: nowrap;
  min-width: 96px;
  text-align: right;
}

@media (max-width: 820px) {
  .admin-top-bento {
    grid-template-columns: 1fr;
    gap: 14px;
  }
  .week-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}
@media (max-width: 768px) {
  .admin-overview {
    gap: 14px;
  }
  .attendance-card,
  .trend-panel {
    padding: 15px 14px;
    gap: 12px;
  }
  .attendance-val strong {
    font-size: 30px;
  }
  .admin-side-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .metric-tile {
    padding: 13px 12px;
    gap: 10px;
  }
  .metric-icon {
    width: 34px;
    height: 34px;
    border-radius: 10px;
  }
  .metric-tile strong {
    font-size: 16px;
  }
  .week-row {
    padding: 10px 12px;
  }
  .meter-text {
    min-width: 78px;
    font-size: 12px;
  }
}
</style>
