<script setup lang="ts">
import { ref, watch } from 'vue'
import { inspectUserDayApi, inspectUserPlanApi, inspectUserStatisticsApi } from '@/api/admin'
import ReviewCard from '@/components/reviews/ReviewCard.vue'
import StudyReport from '@/components/stats/StudyReport.vue'
import CategoryBadge from '@/components/ui/CategoryBadge.vue'
import GlassModal from '@/components/ui/GlassModal.vue'
import PageSkeleton from '@/components/ui/PageSkeleton.vue'
import { today } from '@/stores/session'
import type { Day, Plan, Statistics, User } from '@/types'
import { duration } from '@/utils/date'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{ user: User | null }>()

const tab = ref<'day' | 'plan' | 'statistics'>('day')
const date = ref(today.value)
const day = ref<Day | null>(null)
const plan = ref<Plan | null>(null)
const stats = ref<Statistics | null>(null)
const error = ref('')

watch(open, isOpen => {
  if (isOpen) {
    tab.value = 'day'
    date.value = today.value
  }
})

watch([open, () => props.user, tab, date], async (_, _old, cleanup) => {
  if (!open.value || !props.user || (tab.value === 'day' && !date.value)) return
  let valid = true
  cleanup(() => {
    valid = false
  })
  day.value = plan.value = stats.value = null
  error.value = ''
  const uid = props.user.id
  try {
    if (tab.value === 'day') {
      const value = await inspectUserDayApi(uid, date.value)
      if (valid) day.value = value
    } else if (tab.value === 'plan') {
      const value = await inspectUserPlanApi(uid)
      if (valid) plan.value = value
    } else {
      const value = await inspectUserStatisticsApi(uid)
      if (valid) stats.value = value
    }
  } catch (e) {
    if (valid) error.value = (e as Error).message
  }
})
</script>

<template>
  <GlassModal v-model="open" :title="`${user?.username ?? ''} · 只读查看`" drawer>
    <div class="form-stack">
      <div class="section-head">
        <div class="segmented">
          <button type="button" :aria-pressed="tab === 'day'" @click="tab = 'day'">日记录</button>
          <button type="button" :aria-pressed="tab === 'plan'" @click="tab = 'plan'">计划</button>
          <button type="button" :aria-pressed="tab === 'statistics'" @click="tab = 'statistics'">统计</button>
        </div>
        <input v-if="tab === 'day'" v-model="date" :max="today" type="date" style="width: auto" />
      </div>

      <p v-if="error" class="error-text" role="alert">{{ error }}</p>

      <template v-else-if="tab === 'day' && day">
        <div v-if="!day.exists && day.date !== today" class="empty-box compact">当天无记录</div>
        <template v-else>
          <div class="inspect-pills">
            <span class="pill" :class="{ success: !!day.checked_at }">{{ day.checked_at ? '已打卡' : '未打卡' }}</span>
            <span class="pill tabular">专注 {{ duration(day.focus_seconds) }}</span>
          </div>
          <ul class="inspect-list">
            <li v-for="item in day.tasks" :key="item.id">
              <span>{{ (item.override ?? item).start }} · {{ item.title }}</span>
              <span class="pill" :class="{ accent: item.done }">{{ item.done ? '已完成' : '未完成' }}</span>
            </li>
          </ul>
          <h3 style="font-size: 14px; margin-top: 6px">每日复盘</h3>
          <ReviewCard v-model="day.review" readonly />
        </template>
      </template>

      <template v-else-if="tab === 'plan' && plan">
        <p class="muted">当前计划版本 · {{ plan.current.date }}</p>
        <ul class="inspect-list">
          <li v-for="item in plan.current.tasks" :key="item.id">
            <span>{{ item.start }} · {{ item.title }}</span>
            <CategoryBadge :id="item.category" :name="item.category_name" />
          </li>
        </ul>
      </template>

      <StudyReport
        v-else-if="tab === 'statistics' && stats && user"
        :data="stats"
        :load-range="(start, end) => inspectUserStatisticsApi(user!.id, { start, end })"
        compact
      />
      <PageSkeleton v-else :layout="tab === 'statistics' ? 'stats' : tab === 'day' ? 'inspection-day' : 'inspection-plan'" />
    </div>
  </GlassModal>
</template>

<style scoped>
.inspect-pills {
  display: flex;
  gap: 8px;
}
.inspect-list {
  display: grid;
  gap: 6px;
  max-height: 260px;
  overflow-y: auto;
}
.inspect-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 11px;
  border-radius: 11px;
  background: var(--surface-subtle);
  font-size: 12.5px;
}
</style>
