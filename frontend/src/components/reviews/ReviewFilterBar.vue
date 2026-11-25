<script setup lang="ts">
import { Search } from 'lucide-vue-next'
import { MOODS, REVIEW_ISSUES } from '@/constants/study'
import type { Mood } from '@/types'

const searchQuery = defineModel<string>('search', { required: true })
const issueFilter = defineModel<string>('issue', { required: true })
const moodFilter = defineModel<Mood | ''>('mood', { required: true })
</script>

<template>
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
</template>

<style scoped>
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
@media (max-width: 768px) {
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
}
</style>
