<script setup lang="ts">
import { CheckCircle2, Clock3, Sparkles } from 'lucide-vue-next'
import BrandMark from '@/components/ui/BrandMark.vue'
import ProgressRing from '@/components/ui/ProgressRing.vue'
</script>

<template>
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
</template>

<style scoped>
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
@media (max-width: 900px) {
  .auth-showcase {
    display: none;
  }
}
</style>
