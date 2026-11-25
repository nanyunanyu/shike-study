<script setup lang="ts">
import { Bell, BellOff, CloudRain, Coffee, Radio, Volume2, VolumeX, Wind } from 'lucide-vue-next'
import { setSoundPreset, setSoundVolume, SOUND_OPTIONS, soundState, type SoundPreset } from '../utils/soundscape'

defineProps<{ compact?: boolean }>()

const icons: Record<SoundPreset, typeof VolumeX> = {
  off: VolumeX,
  rain: CloudRain,
  brown: Radio,
  wind: Wind,
  cafe: Coffee,
}
</script>

<template>
  <div class="ambient-mixer" :class="{ compact }">
    <div class="mixer-head">
      <div class="mixer-title">
        <Volume2 :size="15" class="accent-text" />
        <strong>专注环境音</strong>
        <span v-if="!compact" class="tertiary">Web Audio 实时合成 · 离线可用</span>
      </div>
      <button
        type="button"
        class="btn ghost sm"
        :class="{ 'accent-text': soundState.chimeEnabled }"
        @click="soundState.chimeEnabled = !soundState.chimeEnabled"
      >
        <Bell v-if="soundState.chimeEnabled" :size="14" />
        <BellOff v-else :size="14" />
        <span>{{ soundState.chimeEnabled ? '结束钵音开' : '结束静音' }}</span>
      </button>
    </div>

    <div class="sound-pills" role="group" aria-label="选择专注环境音">
      <button
        v-for="item in SOUND_OPTIONS"
        :key="item.id"
        type="button"
        class="sound-chip"
        :class="{ active: soundState.preset === item.id }"
        :aria-pressed="soundState.preset === item.id"
        @click="setSoundPreset(item.id)"
      >
        <component :is="icons[item.id]" :size="15" />
        <span>{{ item.label }}</span>
      </button>
    </div>

    <div v-if="soundState.preset !== 'off'" class="volume-row">
      <VolumeX :size="14" class="tertiary" />
      <input
        type="range"
        class="volume-slider"
        min="0.05"
        max="0.9"
        step="0.01"
        :value="soundState.volume"
        aria-label="环境音量"
        @input="setSoundVolume(Number(($event.target as HTMLInputElement).value))"
      />
      <Volume2 :size="14" class="accent-text" />
      <span class="tertiary tabular" style="min-width: 34px; text-align: right; font-size: 11.5px">
        {{ Math.round((soundState.volume / 0.9) * 100) }}%
      </span>
    </div>
  </div>
</template>

<style scoped>
.ambient-mixer {
  display: grid;
  gap: 12px;
}
.mixer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}
.mixer-title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
}
.mixer-title span {
  font-size: 11.5px;
}
.sound-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}
.sound-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 13px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border);
  background: var(--surface-subtle);
  color: var(--ink-secondary);
  font-size: 12.5px;
  font-weight: 560;
  transition: background 0.18s, color 0.18s, border-color 0.18s, transform 0.15s;
}
.sound-chip:hover {
  background: var(--surface-hover);
  color: var(--ink);
}
.sound-chip.active {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent);
  font-weight: 640;
}
.volume-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.volume-slider {
  flex: 1;
  accent-color: var(--accent);
  cursor: pointer;
}
.compact .sound-chip {
  padding: 5px 11px;
  font-size: 12px;
}
@media (max-width: 640px) {
  .sound-pills {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
  }
  .sound-chip {
    justify-content: center;
    padding: 6px 8px;
    font-size: 12px;
  }
}
</style>
