<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { BookMarked, Sparkles, Star } from 'lucide-vue-next'
import { fetchReviewsTimeline, fetchStatistics } from '@/api/stats'
import ReviewFilterBar from '@/components/reviews/ReviewFilterBar.vue'
import ReviewJournalCard from '@/components/reviews/ReviewJournalCard.vue'
import ShareCardModal from '@/components/share/ShareCardModal.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PageSkeleton from '@/components/ui/PageSkeleton.vue'
import { MOODS } from '@/constants/study'
import { learningRevision, preferences, session } from '@/stores/session'
import type { Mood, ReviewTimelineItem, ReviewTimelinePage } from '@/types'
import { buildSharePayloadFromReview } from '@/utils/sharePayload'

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
  try {
    const [page, statsData] = await Promise.all([
      fetchReviewsTimeline({
        mood: moodFilter.value,
        issue: issueFilter.value,
        q: searchQuery.value,
        before: append ? nextBefore.value : null,
      }),
      append ? Promise.resolve(null) : fetchStatistics().catch(() => null),
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

watch(
  [moodFilter, issueFilter, learningRevision],
  () => {
    void load(false)
  },
  { immediate: true },
)

watch(searchQuery, () => {
  window.clearTimeout(searchDebounce)
  searchDebounce = window.setTimeout(() => void load(false), 260)
})

onUnmounted(() => {
  window.clearTimeout(searchDebounce)
})

const topMood = computed(() => {
  const entries = Object.entries(summary.value.mood_counts)
  if (!entries.length) return null
  entries.sort((a, b) => b[1] - a[1])
  return MOODS.find(m => m.id === entries[0]![0]) ?? null
})

function openShare(entry: ReviewTimelineItem) {
  shareTarget.value = entry
  shareOpen.value = true
}

const sharePayload = computed(() =>
  shareTarget.value && session.value
    ? buildSharePayloadFromReview({
        entry: shareTarget.value,
        username: session.value.user.username,
        goalMinutes: preferences.value.daily_focus_goal_minutes,
        streak: streak.value,
      })
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

      <ReviewFilterBar v-model:search="searchQuery" v-model:issue="issueFilter" v-model:mood="moodFilter" />

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
        <ReviewJournalCard v-for="entry in items" :key="entry.date" :entry="entry" @share="openShare" />
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
}
</style>
