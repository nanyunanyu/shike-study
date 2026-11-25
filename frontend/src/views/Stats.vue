<script setup lang="ts">
import { ref, watch } from 'vue'
import { api, learningRevision, today } from '../state'
import type { Milestone, Statistics } from '../types'
import MilestonePanel from '../components/MilestonePanel.vue'
import StudyReport from '../components/StudyReport.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PageSkeleton from '../components/ui/PageSkeleton.vue'

const stats = ref<Statistics | null>(null)
const milestones = ref<Milestone[]>([])
const error = ref('')
let revision = 0

async function load() {
  const id = ++revision
  error.value = ''
  try {
    const [statsData, msData] = await Promise.all([api<Statistics>('/statistics'), api<Milestone[]>('/milestones')])
    if (id === revision) {
      stats.value = statsData
      milestones.value = msData
    }
  } catch (e) {
    if (id === revision) error.value = (e as Error).message
  }
}

watch([learningRevision, today], load, { immediate: true })
</script>

<template>
  <div class="page stats-page">
    <PageHeader eyebrow="INSIGHTS & MILESTONES" title="学习统计" subtitle="数据趋势、长期热力足迹、考试倒计时与成就徽章" />

    <p v-if="error" class="error-text" role="alert">
      {{ error }} <button type="button" class="btn ghost sm" @click="load">重试</button>
    </p>

    <div v-if="stats" class="stats-stack">
      <StudyReport :data="stats" />
      <MilestonePanel :milestones="milestones" @changed="load" />
    </div>
    <PageSkeleton v-else-if="!error" layout="stats" />
  </div>
</template>

<style scoped>
.stats-stack {
  display: grid;
  gap: 20px;
}
</style>
