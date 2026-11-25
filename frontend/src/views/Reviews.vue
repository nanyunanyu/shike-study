<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { BookMarked, CheckCircle2, Search, Share2, Sparkles, Star, Timer as TimerIcon } from 'lucide-vue-next'
import { api, duration, labelDate, learningRevision, MOODS, preferences, REVIEW_ISSUES, session } from '../state'
import type { Mood, ReviewTimelineItem, ReviewTimelinePage, Statistics } from '../types'
import ShareCardModal from '../components/ShareCardModal.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageSkeleton from '../components/ui/PageSkeleton.vue'

const items = ref<ReviewTimelineItem[]>([])
const summary = ref<ReviewTimelinePage['summary']>({ total_reviews: 0, avg_focus_score: null, mood_counts: {} })
const nextBefore = ref<string | null>(null)
const hasLoaded = ref(false)
const loading = ref(true)
const error = ref('')

const moodFilter = ref<Mood | ''>('')
const issueFilter = ref('')
const searchQuery = ref('')
const streak = ref(0)

const shareOpen = ref(false)
const shareTarget = ref<ReviewTimelineItem | null>(null)

let serial = 0
let searchDebounce = 0

async function load(append = false) {
  const version = ++serial
  loading.value = true
  error.value = ''
  const params = new URLSearchParams({ limit: '20' })
  if (moodFilter.value) params.set('mood', moodFilter.value)
  if (issueFilter.value) params.set('issue', issueFilter.value)
  if (searchQuery.value.trim()) params.set('q', searchQuery.value.trim())
  if (append && nextBefore.value) params.set('before', nextBefore.value)
  try {
    const [page, statsData] = await Promise.all([
      api<ReviewTimelinePage>(`/reviews?${params}`),
      append ? Promise.resolve(null) : api<Statistics>('/statistics').catch(() => null),
    ])
    if (version !== serial) return
    items.value = append ? [...items.value, ...page.items] : page.items
    nextBefore.value = page.next_before
    summary.value = page.summary
    if (statsData) streak.value = statsData.streak
    hasLoaded.value = true
  } catch (e) {
    if (version === serial) error.value = (e as Error).message
  } finally {
    if (version === serial) loading.value = false
  }
}

watch([moodFilter, issueFilter, learningRevision], () => {
  void load(false)
}, { immediate: true })

watch(searchQuery, () => {
  window.clearTimeout(searchDebounce)
  searchDebounce = window.setTimeout(() => void load(false), 260)
})

const topMood = computed(() => {
  const entries = Object.entries(summary.value.mood_counts)
  if (!entries.length) return null
  entries.sort((a, b) => b[1] - a[1])
  return MOODS.find(m => m.id === entries[0]![0]) ?? null
})

function moodInfo(id: Mood | null) {
  return MOODS.find(m => m.id === id) ?? null
}

function openShare(entry: ReviewTimelineItem) {
  shareTarget.value = entry
  shareOpen.value = true
}

const sharePayload = computed(() =>
  shareTarget.value && session.value
    ? {
        date: shareTarget.value.date,
        username: session.value.user.username,
        completed: shareTarget.value.completed,
        total: shareTarget.value.total,
        focusSeconds: shareTarget.value.focus_seconds,
        goalMinutes: preferences.value.daily_focus_goal_minutes,
        streak: streak.value,
        checked: !!shareTarget.value.checked_at,
        mood: shareTarget.value.review.mood,
        focusScore: shareTarget.value.review.focus_score,
        takeaways: shareTarget.value.review.effective,
        reflection: shareTarget.value.review.reflection || shareTarget.value.review.adjustment,
      }
    : null,
)
</script>

<template>
  <div class="page reviews-page">
    <PageHeader eyebrow="REFLECTION JOURNAL" title="复盘手账" subtitle="按时间线回溯每日沉淀、心境变化与学习方法迭代" />

    <p v-if="error && !hasLoaded" class="error-text" role="alert">
      {{ error }} <button type="button" class="btn ghost sm" @click="load(false)">重试</button>
    </p>
    <PageSkeleton v-else-if="!hasLoaded && loading" layout="reviews" />

    <template v-else>
      <!-- Summary Bento Strip -->
      <section class="summary-strip">
        <div class="glass-card stat-tile">
          <span class="tile-label"><BookMarked :size="14" class="accent-text" />累计复盘</span>
          <strong class="tabular">{{ summary.total_reviews }} <small class="muted">篇</small></strong>
        </div>
        <div class="glass-card stat-tile">
          <span class="tile-label"><Star :size="14" class="accent-text" />平均专注度</span>
          <strong class="tabular">{{ summary.avg_focus_score ?? '—' }} <small v-if="summary.avg_focus_score" class="muted">/ 5.0</small></strong>
        </div>
        <div class="glass-card stat-tile">
          <span class="tile-label"><Sparkles :size="14" class="accent-text" />常见心境</span>
          <strong>{{ topMood ? `${topMood.glyph} ${topMood.label}` : '暂无记录' }}</strong>
        </div>
      </section>

      <!-- Filter Bar -->
      <section class="filter-bar glass-card">
        <div class="filter-top-row">
          <label class="search-box">
            <Search :size="15" class="tertiary" />
            <input v-model="searchQuery" type="search" class="bare-input" placeholder="检索收获、随笔、明日优先或日期…" />
          </label>
          <select v-model="issueFilter" class="issue-select" aria-label="按阻力标签筛选">
            <option value="">全部阻力标签</option>
            <option v-for="iss in REVIEW_ISSUES" :key="iss" :value="iss">{{ iss }}</option>
          </select>
        </div>

        <div class="mood-filters" role="group" aria-label="按心情筛选">
          <button type="button" class="filter-chip" :class="{ active: moodFilter === '' }" @click="moodFilter = ''">全部心境</button>
          <button
            v-for="m in MOODS"
            :key="m.id"
            type="button"
            class="filter-chip"
            :class="{ active: moodFilter === m.id }"
            @click="moodFilter = moodFilter === m.id ? '' : m.id"
          >
            {{ m.glyph }} {{ m.label }}
          </button>
        </div>
      </section>

      <p v-if="error" class="error-text" role="alert">
        {{ error }} <button type="button" class="btn ghost sm" @click="load(false)">重试</button>
      </p>
      <PageSkeleton v-else-if="loading && !items.length" layout="reviews-cards" />

      <div v-else-if="!items.length" class="glass-card empty-journal">
        <BookMarked :size="28" class="tertiary" />
        <h3>{{ moodFilter || issueFilter || searchQuery ? '没有符合筛选条件的复盘记录' : '尚未留下复盘手账' }}</h3>
        <p class="muted">在「今日」页面填写状态、收获或随笔并保存后，会自动收录在这里。</p>
      </div>

      <div v-else class="journal-grid">
        <article v-for="entry in items" :key="entry.date" class="journal-card glass-card">
          <header class="journal-head">
            <div>
              <h3>{{ labelDate(entry.date, 'long') }}</h3>
              <span class="tertiary tabular">{{ entry.date }}</span>
            </div>
            <div class="journal-head-right">
              <span v-if="entry.checked_at" class="pill success"><CheckCircle2 :size="12" />已打卡</span>
              <button type="button" class="icon-btn sm" title="生成当日打卡海报" @click="openShare(entry)">
                <Share2 :size="15" />
              </button>
            </div>
          </header>

          <div class="journal-metrics">
            <span class="pill tabular">完成 {{ entry.completed }}/{{ entry.total }}</span>
            <span class="pill tabular"><TimerIcon :size="12" />{{ duration(entry.focus_seconds) }}</span>
            <span v-if="moodInfo(entry.review.mood)" class="pill accent">
              {{ moodInfo(entry.review.mood)?.glyph }} {{ moodInfo(entry.review.mood)?.label }}
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
      </div>

      <div v-if="nextBefore" class="load-more">
        <button type="button" class="btn secondary pill" :disabled="loading" @click="load(true)">
          {{ loading ? '正在加载…' : '加载更早复盘' }}
        </button>
      </div>
    </template>

    <ShareCardModal v-model="shareOpen" :payload="sharePayload" />
  </div>
</template>

<style scoped>
.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}
.stat-tile {
  padding: 18px 20px;
  display: grid;
  gap: 8px;
}
.tile-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 590;
  color: var(--ink-secondary);
}
.stat-tile strong {
  font-size: 24px;
  font-weight: 740;
  letter-spacing: -0.025em;
}
.stat-tile strong small {
  font-size: 13px;
  font-weight: 560;
}

.filter-bar {
  padding: 14px 16px;
  display: grid;
  gap: 11px;
  margin-bottom: 20px;
}
.filter-top-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.search-box {
  flex: 1 1 260px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 13px;
  min-height: 38px;
  border-radius: 12px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
}
.search-box input {
  width: 100%;
  border: 0;
  background: transparent;
  outline: none;
  font-size: 13px;
}
.mood-filters {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.filter-chip {
  padding: 6px 11px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border);
  background: var(--surface-subtle);
  color: var(--ink-secondary);
  font-size: 12px;
  font-weight: 550;
  transition: background 0.16s, color 0.16s, border-color 0.16s;
}
.filter-chip.active {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent);
  font-weight: 630;
}
.issue-select {
  width: auto;
  min-width: 136px;
  min-height: 38px;
}

.empty-journal {
  padding: 56px 24px;
  display: grid;
  justify-items: center;
  gap: 10px;
  text-align: center;
}
.journal-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}
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
.load-more {
  margin-top: 22px;
  display: flex;
  justify-content: center;
}

@media (max-width: 860px) {
  .journal-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}
@media (max-width: 768px) {
  .summary-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 12px;
  }
  .stat-tile {
    padding: 12px 10px;
    gap: 5px;
  }
  .tile-label {
    font-size: 10.5px;
    gap: 4px;
  }
  .stat-tile strong {
    font-size: 16px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .stat-tile strong small {
    font-size: 11px;
  }
  .filter-bar {
    padding: 12px;
    gap: 9px;
    margin-bottom: 14px;
  }
  .filter-top-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 114px;
    gap: 8px;
  }
  .issue-select {
    min-width: 0;
    width: 100%;
    padding: 6px 8px;
    font-size: 12px;
  }
  .mood-filters {
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: 2px;
  }
  .mood-filters::-webkit-scrollbar {
    display: none;
  }
  .filter-chip {
    flex: none;
    padding: 5px 10px;
    font-size: 11.5px;
  }
  .journal-card {
    padding: 15px 14px;
    gap: 10px;
  }
  .journal-head h3 {
    font-size: 15px;
  }
}
</style>
