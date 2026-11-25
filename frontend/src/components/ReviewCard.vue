<script setup lang="ts">
import { Plus, Save, Sparkles, Star, X } from 'lucide-vue-next'
import { MOODS, REVIEW_ISSUES } from '../state'
import type { Mood, Review } from '../types'

const props = defineProps<{ readonly?: boolean; busy?: boolean }>()
const data = defineModel<Review>({ required: true })
defineEmits<{ save: [] }>()

function setMood(mood: Mood) {
  if (props.readonly || props.busy) return
  data.value = { ...data.value, mood: data.value.mood === mood ? null : mood }
}

function setScore(score: number) {
  if (props.readonly || props.busy) return
  data.value = { ...data.value, focus_score: data.value.focus_score === score ? null : score }
}

function toggleIssue(issue: string) {
  if (props.readonly || props.busy) return
  const exists = data.value.issues.includes(issue)
  const next = exists ? data.value.issues.filter(item => item !== issue) : [...data.value.issues, issue]
  data.value = { ...data.value, issues: next }
}

function updateItem(field: 'effective' | 'priorities', index: number, value: string) {
  const next = [...data.value[field]]
  next[index] = value
  data.value = { ...data.value, [field]: next }
}

function addItem(field: 'effective' | 'priorities') {
  if (data.value[field].length >= 12) return
  data.value = { ...data.value, [field]: [...data.value[field], ''] }
}

function removeItem(field: 'effective' | 'priorities', index: number) {
  const next = data.value[field].filter((_, i) => i !== index)
  data.value = { ...data.value, [field]: next.length ? next : [''] }
}
</script>

<template>
  <form class="review-form" @submit.prevent="$emit('save')">
    <!-- Mood & Focus Score -->
    <div class="review-block">
      <div class="block-head">
        <span class="field-label">今日状态</span>
        <span v-if="data.mood" class="accent-text mood-hint">
          {{ MOODS.find(m => m.id === data.mood)?.label }}
        </span>
      </div>
      <div class="mood-grid" role="group" aria-label="今日学习状态">
        <button
          v-for="item in MOODS"
          :key="item.id"
          type="button"
          class="mood-chip"
          :class="{ active: data.mood === item.id }"
          :style="{ '--tone': item.tone }"
          :disabled="readonly || busy"
          :aria-pressed="data.mood === item.id"
          @click="setMood(item.id)"
        >
          <span class="mood-glyph">{{ item.glyph }}</span>
          <span class="mood-full">{{ item.label }}</span>
          <span class="mood-short">{{ item.short }}</span>
        </button>
      </div>
    </div>

    <div class="review-block score-row">
      <span class="field-label">专注度评分</span>
      <div class="score-stars" role="group" aria-label="专注度评分 1 到 5 分">
        <button
          v-for="n in 5"
          :key="n"
          type="button"
          class="star-btn"
          :class="{ filled: (data.focus_score ?? 0) >= n }"
          :disabled="readonly || busy"
          :aria-label="`${n} 分`"
          @click="setScore(n)"
        >
          <Star :size="17" :fill="(data.focus_score ?? 0) >= n ? 'currentColor' : 'none'" />
        </button>
        <small class="muted tabular">{{ data.focus_score ? `${data.focus_score} / 5` : '未评分' }}</small>
      </div>
    </div>

    <!-- Effective takeaways -->
    <div class="review-block">
      <div class="block-head">
        <span class="field-label">最有效的学习收获</span>
        <button v-if="!readonly" type="button" class="btn ghost sm" :disabled="busy" @click="addItem('effective')">
          <Plus :size="13" />添加
        </button>
      </div>
      <div class="line-list">
        <div v-for="(item, idx) in data.effective" :key="`eff-${idx}`" class="line-row">
          <span class="line-num tabular">{{ idx + 1 }}</span>
          <input
            :value="item"
            :readonly="readonly"
            :disabled="busy"
            maxlength="2000"
            placeholder="记录今天最扎实的一点收获…"
            @input="updateItem('effective', idx, ($event.target as HTMLInputElement).value)"
          />
          <button
            v-if="!readonly && data.effective.length > 1"
            type="button"
            class="icon-btn sm"
            aria-label="删除此条"
            @click="removeItem('effective', idx)"
          >
            <X :size="14" />
          </button>
        </div>
      </div>
    </div>

    <!-- Issue Pills -->
    <div class="review-block">
      <span class="field-label">今日阻力标签</span>
      <div class="issue-pills" role="group" aria-label="今日问题">
        <button
          v-for="issue in REVIEW_ISSUES"
          :key="issue"
          type="button"
          class="issue-pill"
          :class="{ active: data.issues.includes(issue) }"
          :disabled="readonly || busy"
          :aria-pressed="data.issues.includes(issue)"
          @click="toggleIssue(issue)"
        >
          {{ issue }}
        </button>
      </div>
      <input
        v-if="data.issues.includes('其他') || data.other"
        v-model="data.other"
        :readonly="readonly"
        :disabled="busy"
        maxlength="2000"
        placeholder="补充说明其他干扰因素…"
      />
    </div>

    <!-- Priorities -->
    <div class="review-block">
      <div class="block-head">
        <span class="field-label">明日优先解决</span>
        <button v-if="!readonly" type="button" class="btn ghost sm" :disabled="busy" @click="addItem('priorities')">
          <Plus :size="13" />添加
        </button>
      </div>
      <div class="line-list">
        <div v-for="(item, idx) in data.priorities" :key="`pri-${idx}`" class="line-row">
          <span class="line-num tabular">{{ idx + 1 }}</span>
          <input
            :value="item"
            :readonly="readonly"
            :disabled="busy"
            maxlength="2000"
            placeholder="明天最想先攻克的事项…"
            @input="updateItem('priorities', idx, ($event.target as HTMLInputElement).value)"
          />
          <button
            v-if="!readonly && data.priorities.length > 1"
            type="button"
            class="icon-btn sm"
            aria-label="删除此条"
            @click="removeItem('priorities', idx)"
          >
            <X :size="14" />
          </button>
        </div>
      </div>
    </div>

    <!-- Adjustment & Reflection -->
    <label class="field">
      <span class="field-label">明日策略微调</span>
      <textarea
        v-model="data.adjustment"
        :readonly="readonly"
        :disabled="busy"
        rows="2"
        maxlength="2000"
        placeholder="例如：午后先用 15 分钟快速进入状态…"
      />
    </label>

    <label class="field">
      <span class="field-label"><Sparkles :size="12" class="accent-text" /> 今日手账随笔</span>
      <textarea
        v-model="data.reflection"
        :readonly="readonly"
        :disabled="busy"
        rows="3"
        maxlength="2000"
        placeholder="写一句给今天自己的记录，将收录至「复盘手账」与分享海报…"
      />
    </label>

    <button v-if="!readonly" type="submit" class="btn primary full" :disabled="busy">
      <Save :size="15" />{{ busy ? '正在保存…' : '保存今日复盘' }}
    </button>
  </form>
</template>

<style scoped>
.review-form {
  display: grid;
  gap: 16px;
}
.review-block {
  display: grid;
  gap: 8px;
}
.block-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.mood-hint {
  font-size: 12px;
  font-weight: 600;
}
.mood-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 6px;
}
.mood-chip {
  display: grid;
  justify-items: center;
  gap: 3px;
  padding: 8px 4px;
  border-radius: 12px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  font-size: 11px;
  font-weight: 540;
  color: var(--ink-secondary);
  transition: background 0.18s, border-color 0.18s, color 0.18s, transform 0.15s;
}
.mood-chip:hover:not(:disabled) {
  background: var(--surface-hover);
  color: var(--ink);
}
.mood-chip.active {
  background: color-mix(in srgb, var(--tone) 14%, var(--surface-solid));
  border-color: color-mix(in srgb, var(--tone) 38%, transparent);
  color: var(--tone);
  font-weight: 640;
}
.mood-glyph {
  font-size: 15px;
  line-height: 1;
}
.mood-short {
  display: none;
}
.score-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  border-radius: 12px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
}
.score-stars {
  display: flex;
  align-items: center;
  gap: 4px;
}
.score-stars small {
  margin-left: 6px;
  font-size: 12px;
}
.star-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: var(--ink-tertiary);
  transition: color 0.16s, transform 0.16s var(--ease-spring), background 0.16s;
}
.star-btn:hover:not(:disabled) {
  background: var(--surface-hover);
  transform: scale(1.1);
}
.star-btn.filled {
  color: var(--accent);
}
.line-list {
  display: grid;
  gap: 6px;
}
.line-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.line-row input {
  min-height: 36px;
  padding: 6px 10px;
  font-size: 13px;
}
.line-num {
  width: 18px;
  text-align: center;
  font-size: 11px;
  font-weight: 640;
  color: var(--ink-tertiary);
  flex: none;
}
.issue-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.issue-pill {
  padding: 5px 11px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border);
  background: var(--surface-subtle);
  color: var(--ink-secondary);
  font-size: 12px;
  font-weight: 540;
  transition: background 0.16s, color 0.16s, border-color 0.16s;
}
.issue-pill:hover:not(:disabled) {
  background: var(--surface-hover);
  color: var(--ink);
}
.issue-pill.active {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent);
  font-weight: 620;
}
@media (max-width: 520px) {
  .mood-grid {
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 5px;
  }
  .mood-chip {
    padding: 7px 2px;
    border-radius: 10px;
    font-size: 10.5px;
  }
  .mood-full {
    display: none;
  }
  .mood-short {
    display: inline;
  }
}
</style>
