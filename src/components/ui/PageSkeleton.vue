<script setup lang="ts">
export type SkeletonLayout =
  | 'session'
  | 'today'
  | 'timer'
  | 'plan'
  | 'reviews'
  | 'reviews-cards'
  | 'stats'
  | 'admin-overview'
  | 'accounts'
  | 'dispatches'
  | 'inspection-day'
  | 'inspection-plan'

withDefaults(defineProps<{ layout?: SkeletonLayout }>(), { layout: 'today' })
</script>

<template>
  <div class="page-skeleton" :data-layout="layout" aria-busy="true">
    <span class="sr-only" role="status">正在加载页面内容</span>

    <!-- Session Boot -->
    <div v-if="layout === 'session'" class="sk-session" aria-hidden="true">
      <span class="sk-box sk-emblem"></span>
      <span class="sk-box" style="width: 120px; height: 18px"></span>
      <span class="sk-box" style="width: 190px; height: 12px"></span>
    </div>

    <!-- Today -->
    <div v-else-if="layout === 'today'" class="sk-stack" aria-hidden="true">
      <div class="glass-card sk-hero">
        <div class="sk-hero-left">
          <div class="sk-row">
            <span class="sk-box sk-pill" style="width: 96px"></span>
            <span class="sk-box sk-pill" style="width: 148px"></span>
          </div>
          <span class="sk-box" style="width: 156px; height: 36px; border-radius: 10px"></span>
          <div class="sk-row">
            <span class="sk-box sk-btn" style="width: 142px"></span>
            <span class="sk-box sk-btn" style="width: 112px"></span>
          </div>
        </div>
        <div class="sk-hero-rings">
          <span class="sk-ring"></span>
          <span class="sk-ring"></span>
        </div>
      </div>

      <div class="sk-today-grid">
        <div class="glass-card sk-panel">
          <div class="sk-between">
            <span class="sk-box sk-h2"></span>
            <span class="sk-box sk-pill" style="width: 82px; height: 28px"></span>
          </div>
          <div class="sk-row">
            <span class="sk-box" style="width: 128px; height: 30px; border-radius: 10px"></span>
            <span class="sk-box" style="width: 156px; height: 30px; border-radius: 10px"></span>
          </div>
          <div v-for="i in 5" :key="i" class="sk-task-row">
            <span class="sk-box" style="width: 38px; height: 14px"></span>
            <span class="sk-box sk-dot"></span>
            <div class="sk-task-body">
              <span class="sk-box" :style="{ width: i % 2 ? '68%' : '52%', height: '14px' }"></span>
              <span class="sk-box sk-pill" style="width: 64px; height: 18px"></span>
            </div>
          </div>
        </div>

        <div class="sk-stack">
          <div class="glass-card sk-panel">
            <div class="sk-between">
              <span class="sk-box sk-h2"></span>
              <span class="sk-box sk-pill" style="width: 48px"></span>
            </div>
            <span class="sk-box" style="width: 130px; height: 28px"></span>
            <span class="sk-box" style="width: 100%; height: 7px; border-radius: 99px"></span>
            <span class="sk-box sk-btn" style="width: 100%"></span>
          </div>
          <div class="glass-card sk-panel">
            <span class="sk-box sk-h2"></span>
            <div class="sk-5-grid">
              <span v-for="n in 5" :key="n" class="sk-box" style="height: 48px; border-radius: 12px"></span>
            </div>
            <span class="sk-box" style="width: 100%; height: 42px; border-radius: 12px"></span>
            <span class="sk-box" style="width: 100%; height: 74px; border-radius: 12px"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Timer -->
    <div v-else-if="layout === 'timer'" class="sk-timer-grid" aria-hidden="true">
      <div class="glass-card sk-panel sk-timer-main">
        <div class="sk-between" style="width: 100%">
          <span class="sk-box" style="width: 210px; height: 34px; border-radius: 12px"></span>
          <span class="sk-box sk-pill" style="width: 72px; height: 24px"></span>
        </div>
        <span class="sk-dial-ring"></span>
        <div class="sk-row" style="justify-content: center">
          <span v-for="n in 4" :key="n" class="sk-box sk-pill" style="width: 74px; height: 28px"></span>
        </div>
        <span class="sk-box sk-btn" style="width: 180px; height: 42px"></span>
      </div>
      <div class="sk-stack">
        <div class="glass-card sk-panel">
          <span class="sk-box sk-h2"></span>
          <span class="sk-box" style="width: 82%; height: 12px"></span>
          <span class="sk-box" style="width: 100%; height: 40px; border-radius: 12px"></span>
        </div>
        <div class="glass-card sk-panel">
          <span class="sk-box sk-h2"></span>
          <div class="sk-row">
            <span v-for="n in 4" :key="n" class="sk-box sk-pill" style="width: 66px; height: 28px"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Plan -->
    <div v-else-if="layout === 'plan'" class="glass-card sk-panel" aria-hidden="true">
      <div class="sk-between">
        <span class="sk-box sk-btn" style="width: 108px"></span>
        <div class="sk-row">
          <span class="sk-box" style="width: 76px; height: 30px; border-radius: 10px"></span>
          <span class="sk-box" style="width: 76px; height: 30px; border-radius: 10px"></span>
          <span class="sk-box" style="width: 76px; height: 30px; border-radius: 10px"></span>
        </div>
      </div>
      <div v-for="i in 6" :key="i" class="sk-plan-row">
        <span class="sk-box" style="width: 48px; height: 14px"></span>
        <span class="sk-box" :style="{ width: i % 2 ? '64%' : '48%', height: '14px' }"></span>
        <span class="sk-box sk-pill" style="width: 64px"></span>
      </div>
    </div>

    <!-- Reviews -->
    <div v-else-if="layout === 'reviews'" class="sk-stack" aria-hidden="true">
      <div class="sk-3-grid">
        <div v-for="i in 3" :key="i" class="glass-card sk-panel" style="gap: 8px">
          <span class="sk-box" style="width: 72px; height: 12px"></span>
          <span class="sk-box" style="width: 90px; height: 26px"></span>
        </div>
      </div>
      <div class="glass-card sk-panel" style="gap: 10px">
        <span class="sk-box" style="width: 100%; height: 36px; border-radius: 12px"></span>
        <div class="sk-row">
          <span v-for="i in 5" :key="i" class="sk-box sk-pill" style="width: 70px; height: 26px"></span>
        </div>
      </div>
      <div class="sk-2-grid">
        <div v-for="i in 4" :key="i" class="glass-card sk-panel">
          <div class="sk-between">
            <span class="sk-box sk-h2"></span>
            <span class="sk-box sk-pill" style="width: 62px"></span>
          </div>
          <span class="sk-box" style="width: 100%; height: 54px; border-radius: 12px"></span>
          <span class="sk-box" style="width: 78%; height: 12px"></span>
          <span class="sk-box" style="width: 60%; height: 12px"></span>
        </div>
      </div>
    </div>

    <!-- Reviews Cards Only (subsequent filter reloads) -->
    <div v-else-if="layout === 'reviews-cards'" class="sk-2-grid" aria-hidden="true">
      <div v-for="i in 4" :key="i" class="glass-card sk-panel">
        <div class="sk-between">
          <span class="sk-box sk-h2"></span>
          <span class="sk-box sk-pill" style="width: 62px"></span>
        </div>
        <span class="sk-box" style="width: 100%; height: 54px; border-radius: 12px"></span>
        <span class="sk-box" style="width: 78%; height: 12px"></span>
        <span class="sk-box" style="width: 60%; height: 12px"></span>
      </div>
    </div>

    <!-- Stats -->
    <div v-else-if="layout === 'stats'" class="sk-stack" aria-hidden="true">
      <div class="glass-card sk-panel">
        <div class="sk-between">
          <span class="sk-box sk-h2"></span>
          <span class="sk-box" style="width: 148px; height: 32px; border-radius: 10px"></span>
        </div>
        <div class="sk-3-grid">
          <div v-for="i in 3" :key="i" class="glass-inset sk-kpi-box">
            <span class="sk-box" style="width: 76px; height: 12px"></span>
            <span class="sk-box" style="width: 112px; height: 28px"></span>
            <span class="sk-box" style="width: 92px; height: 11px"></span>
          </div>
        </div>
      </div>

      <div class="sk-stats-split">
        <div class="glass-card sk-panel">
          <div class="sk-between">
            <span class="sk-box sk-h2"></span>
            <span class="sk-box" style="width: 124px; height: 30px; border-radius: 10px"></span>
          </div>
          <div class="sk-bars">
            <span v-for="(h, idx) in [62, 48, 78, 54, 86, 40, 70]" :key="idx" class="sk-box sk-bar" :style="{ height: `${h}%` }"></span>
          </div>
        </div>
        <div class="glass-card sk-panel">
          <span class="sk-box sk-h2"></span>
          <div v-for="i in 4" :key="i" class="sk-stack" style="gap: 6px">
            <div class="sk-between">
              <span class="sk-box sk-pill" style="width: 68px"></span>
              <span class="sk-box" style="width: 58px; height: 12px"></span>
            </div>
            <span class="sk-box" style="width: 100%; height: 6px; border-radius: 99px"></span>
          </div>
        </div>
      </div>

      <div class="glass-card sk-panel">
        <div class="sk-between">
          <span class="sk-box sk-h2"></span>
          <span class="sk-box" style="width: 126px; height: 30px; border-radius: 10px"></span>
        </div>
        <div class="sk-heat-mask"></div>
      </div>
    </div>

    <!-- Admin Overview -->
    <div v-else-if="layout === 'admin-overview'" class="sk-stack" aria-hidden="true">
      <div class="sk-today-grid">
        <div class="glass-card sk-panel">
          <span class="sk-box sk-h2"></span>
          <span class="sk-box" style="width: 140px; height: 36px"></span>
          <span class="sk-box" style="width: 100%; height: 8px; border-radius: 99px"></span>
        </div>
        <div class="sk-stack">
          <div v-for="i in 2" :key="i" class="glass-card sk-panel" style="flex-direction: row; align-items: center; display: flex; gap: 12px">
            <span class="sk-box" style="width: 40px; height: 40px; border-radius: 12px; flex: none"></span>
            <div class="sk-stack" style="gap: 6px; flex: 1">
              <span class="sk-box" style="width: 72px; height: 11px"></span>
              <span class="sk-box" style="width: 108px; height: 22px"></span>
            </div>
          </div>
        </div>
      </div>
      <div class="glass-card sk-panel">
        <span class="sk-box sk-h2"></span>
        <div v-for="i in 5" :key="i" class="sk-plan-row">
          <span class="sk-box" style="width: 54px; height: 13px"></span>
          <span class="sk-box" style="width: 100%; height: 7px; border-radius: 99px"></span>
          <span class="sk-box" style="width: 68px; height: 13px"></span>
        </div>
      </div>
    </div>

    <!-- Accounts / Dispatches / Drawer Inspection -->
    <div v-else class="sk-stack" aria-hidden="true">
      <div v-for="i in 5" :key="i" class="sk-list-card">
        <span class="sk-box sk-avatar"></span>
        <div class="sk-stack" style="gap: 6px; flex: 1">
          <span class="sk-box" :style="{ width: i % 2 ? '46%' : '62%', height: '14px' }"></span>
          <span class="sk-box" style="width: 32%; height: 11px"></span>
        </div>
        <span class="sk-box sk-pill" style="width: 64px"></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-skeleton {
  min-width: 0;
  pointer-events: none;
}
.sk-stack {
  display: grid;
  gap: 16px;
}
.sk-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.sk-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.sk-panel {
  padding: 20px;
  display: grid;
  gap: 14px;
}
.sk-box {
  display: block;
  border-radius: 8px;
  background: linear-gradient(
    90deg,
    var(--surface-subtle) 15%,
    var(--surface-hover) 50%,
    var(--surface-subtle) 85%
  );
  background-size: 220% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
.sk-h2 {
  width: 112px;
  height: 18px;
}
.sk-pill {
  height: 22px;
  border-radius: var(--radius-pill);
}
.sk-btn {
  height: 38px;
  border-radius: var(--radius-pill);
}
.sk-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex: none;
}
.sk-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  flex: none;
}
.sk-emblem {
  width: 44px;
  height: 44px;
  border-radius: 14px;
}
.sk-session {
  display: grid;
  justify-items: center;
  gap: 12px;
}

.sk-hero {
  padding: 24px 26px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}
.sk-hero-left {
  display: grid;
  gap: 14px;
  flex: 1;
}
.sk-hero-rings {
  display: flex;
  gap: 14px;
}
.sk-ring {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  border: 8px solid var(--surface-hover);
  flex: none;
}
.sk-dial-ring {
  width: 228px;
  height: 228px;
  border-radius: 50%;
  border: 9px solid var(--surface-hover);
  margin: 12px auto;
}
.sk-today-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.48fr) minmax(290px, 360px);
  gap: 18px;
  align-items: start;
}
.sk-timer-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.9fr);
  gap: 18px;
  align-items: start;
}
.sk-timer-main {
  justify-items: center;
}
.sk-stats-split {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(0, 1fr);
  gap: 18px;
}
.sk-3-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.sk-2-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.sk-5-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 6px;
}
.sk-task-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--surface-subtle);
}
.sk-task-body {
  flex: 1;
  display: grid;
  gap: 7px;
}
.sk-plan-row {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--surface-subtle);
}
.sk-list-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  border-radius: 14px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
}
.sk-kpi-box {
  padding: 16px;
  display: grid;
  gap: 8px;
}
.sk-bars {
  height: 158px;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  align-items: end;
  gap: 12px;
  padding: 8px 8px 0;
  border-bottom: 1px solid var(--border);
}
.sk-bar {
  width: 100%;
  border-radius: 8px 8px 3px 3px;
}
.sk-heat-mask {
  height: 104px;
  border-radius: 10px;
  background: linear-gradient(
    90deg,
    var(--surface-subtle) 15%,
    var(--surface-hover) 50%,
    var(--surface-subtle) 85%
  );
  background-size: 220% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  -webkit-mask:
    repeating-linear-gradient(to right, #000 0 11px, transparent 11px 15px),
    repeating-linear-gradient(to bottom, #000 0 11px, transparent 11px 15px);
  -webkit-mask-composite: source-in;
  mask:
    repeating-linear-gradient(to right, #000 0 11px, transparent 11px 15px),
    repeating-linear-gradient(to bottom, #000 0 11px, transparent 11px 15px);
  mask-composite: intersect;
}

@media (max-width: 960px) {
  .sk-today-grid,
  .sk-timer-grid,
  .sk-stats-split,
  .sk-2-grid {
    grid-template-columns: 1fr;
  }
  .sk-hero {
    flex-direction: column;
    align-items: stretch;
  }
}
@media (max-width: 768px) {
  .sk-panel,
  .sk-hero {
    padding: 15px 14px;
  }
  .sk-ring {
    width: 68px;
    height: 68px;
    border-width: 6px;
  }
  .sk-dial-ring {
    width: 190px;
    height: 190px;
  }
  .sk-3-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
