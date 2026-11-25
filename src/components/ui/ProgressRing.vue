<script setup lang="ts">
import { computed, useId } from 'vue'

const props = withDefaults(
  defineProps<{
    progress: number | null
    size?: number
    stroke?: number
    tone?: 'accent' | 'secondary'
    ticks?: boolean
  }>(),
  { size: 112, stroke: 8, tone: 'accent', ticks: false },
)

const gradId = useId()
const radius = computed(() => (props.size - props.stroke) / 2 - (props.ticks ? 9 : 2))
const circumference = computed(() => 2 * Math.PI * radius.value)
const clamped = computed(() => (props.progress == null ? 0 : Math.max(0, Math.min(1, props.progress))))
const dashOffset = computed(() => circumference.value * (1 - clamped.value))
const tickAngles = Array.from({ length: 60 }, (_, idx) => idx * 6)
</script>

<template>
  <svg
    class="progress-ring"
    :width="size"
    :height="size"
    :viewBox="`0 0 ${size} ${size}`"
    aria-hidden="true"
  >
    <defs>
      <linearGradient :id="gradId" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" :stop-color="tone === 'accent' ? 'var(--accent)' : 'var(--accent-2)'" />
        <stop offset="100%" :stop-color="tone === 'accent' ? 'var(--accent-2)' : 'var(--accent)'" />
      </linearGradient>
    </defs>
    <g v-if="ticks" class="ring-ticks">
      <line
        v-for="angle in tickAngles"
        :key="angle"
        :x1="size / 2"
        :y1="angle % 30 === 0 ? 1.5 : 3.5"
        :x2="size / 2"
        :y2="angle % 30 === 0 ? 7.5 : 6.5"
        :stroke-width="angle % 30 === 0 ? 1.6 : 1"
        :opacity="angle % 30 === 0 ? 0.55 : 0.28"
        :transform="`rotate(${angle} ${size / 2} ${size / 2})`"
      />
    </g>
    <circle
      class="ring-track"
      :cx="size / 2"
      :cy="size / 2"
      :r="radius"
      :stroke-width="stroke"
    />
    <circle
      v-if="progress !== null"
      class="ring-value"
      :cx="size / 2"
      :cy="size / 2"
      :r="radius"
      :stroke="`url(#${gradId})`"
      :stroke-width="stroke"
      :stroke-dasharray="circumference"
      :stroke-dashoffset="dashOffset"
      :transform="`rotate(-90 ${size / 2} ${size / 2})`"
    />
  </svg>
</template>

<style scoped>
.progress-ring {
  display: block;
  overflow: visible;
}
.ring-ticks line {
  stroke: var(--ink-tertiary);
  stroke-linecap: round;
}
.ring-track {
  fill: none;
  stroke: var(--surface-hover);
}
.ring-value {
  fill: none;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.55s var(--ease-spring);
  filter: drop-shadow(0 2px 6px color-mix(in srgb, var(--accent) 26%, transparent));
}
</style>
