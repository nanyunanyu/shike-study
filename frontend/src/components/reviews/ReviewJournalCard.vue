<script setup lang="ts">
import { CheckCircle2, Share2, Timer as TimerIcon } from 'lucide-vue-next'
import { moodMeta } from '@/constants/study'
import type { ReviewTimelineItem } from '@/types'
import { duration, labelDate } from '@/utils/date'

defineProps<{ entry: ReviewTimelineItem }>()
const emit = defineEmits<{ share: [entry: ReviewTimelineItem] }>()
</script>

<template>
  <article class="journal-card glass-card">
    <header class="journal-head">
      <div>
        <h3>{{ labelDate(entry.date, 'long') }}</h3>
        <span class="tertiary tabular">{{ entry.date }}</span>
      </div>
      <div class="journal-head-right">
        <span v-if="entry.checked_at" class="pill success"><CheckCircle2 :size="12" />已打卡</span>
        <button type="button" class="icon-btn sm" title="生成当日打卡海报" @click="emit('share', entry)">
          <Share2 :size="15" />
        </button>
      </div>
    </header>

    <div class="journal-metrics">
      <span class="pill tabular">完成 {{ entry.completed }}/{{ entry.total }}</span>
      <span class="pill tabular"><TimerIcon :size="12" />{{ duration(entry.focus_seconds) }}</span>
      <span v-if="moodMeta(entry.review.mood)" class="pill accent">
        {{ moodMeta(entry.review.mood)?.glyph }} {{ moodMeta(entry.review.mood)?.label }}
      </span>
      <span v-if="entry.review.focus_score" class="pill tabular">
        ★ {{ entry.review.focus_score }}.0
      </span>
    </div>

    <blockquote v-if="entry.review.reflection" class="journal-quote">
      {{ entry.review.reflection }}
    </blockquote>

    <div v-if="entry.review.effective.some(t => t.trim())" class="journal-section">
      <small class="field-label">有效收获</small>
      <ul class="bullet-list">
        <li v-for="(line, i) in entry.review.effective.filter(t => t.trim())" :key="i">{{ line }}</li>
      </ul>
    </div>

    <div v-if="entry.review.issues.length || entry.review.other" class="journal-tags">
      <span v-for="iss in entry.review.issues" :key="iss" class="pill warning">{{ iss }}</span>
      <span v-if="entry.review.other" class="muted" style="font-size: 12px">{{ entry.review.other }}</span>
    </div>

    <div v-if="entry.review.priorities.some(t => t.trim())" class="journal-section">
      <small class="field-label">次日优先</small>
      <ul class="bullet-list subtle">
        <li v-for="(line, i) in entry.review.priorities.filter(t => t.trim())" :key="i">{{ line }}</li>
      </ul>
    </div>

    <p v-if="entry.review.adjustment" class="journal-adjust muted">
      <strong>策略微调：</strong>{{ entry.review.adjustment }}
    </p>
  </article>
</template>

<style scoped>
.journal-card {
  padding: 20px 22px;
  display: grid;
  gap: 13px;
  align-content: start;
}
.journal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.journal-head h3 {
  font-size: 16px;
  font-weight: 680;
  letter-spacing: -0.015em;
}
.journal-head span {
  font-size: 12px;
}
.journal-head-right {
  display: flex;
  align-items: center;
  gap: 6px;
}
.journal-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.journal-quote {
  margin: 0;
  padding: 12px 14px;
  border-left: 3px solid var(--accent);
  border-radius: 0 12px 12px 0;
  background: var(--surface-subtle);
  font-size: 13.5px;
  line-height: 1.6;
  color: var(--ink);
}
.journal-section {
  display: grid;
  gap: 6px;
}
.bullet-list {
  display: grid;
  gap: 5px;
  padding-left: 16px;
  list-style: disc;
  font-size: 13px;
  line-height: 1.5;
}
.bullet-list.subtle {
  color: var(--ink-secondary);
}
.journal-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.journal-adjust {
  font-size: 12.5px;
  line-height: 1.55;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}
@media (max-width: 768px) {
  .journal-card {
    padding: 15px 14px;
    gap: 10px;
  }
  .journal-head h3 {
    font-size: 15px;
  }
}
</style>
