<script setup lang="ts">
import { Check, Palette as PaletteIcon } from 'lucide-vue-next'
import { APPEARANCES, PALETTES } from '@/constants/theme'
import type { Appearance, Palette } from '@/types'

defineProps<{
  appearance: Appearance
  palette: Palette
  busy: boolean
}>()

const emit = defineEmits<{
  chooseAppearance: [appearance: Appearance]
  choosePalette: [palette: Palette]
}>()
</script>

<template>
  <section class="me-card glass-card">
    <header class="section-title"><PaletteIcon :size="18" /><h2>外观与通透配色</h2></header>

    <div class="appearance-block">
      <div>
        <strong>界面明暗模式</strong>
        <p class="muted">切换浅色通透画布或午夜深色玻璃模式</p>
      </div>
      <div class="segmented" role="group" aria-label="明暗模式">
        <button
          v-for="item in APPEARANCES"
          :key="item.id"
          type="button"
          :aria-pressed="appearance === item.id"
          :disabled="busy"
          @click="emit('chooseAppearance', item.id)"
        >
          <component :is="item.icon" :size="14" />{{ item.label }}
        </button>
      </div>
    </div>

    <div class="palette-block">
      <span class="field-label">主题氛围色</span>
      <div class="palette-grid" role="group" aria-label="主题氛围色">
        <button
          v-for="item in PALETTES"
          :key="item.id"
          type="button"
          class="palette-card"
          :class="{ active: palette === item.id }"
          :disabled="busy"
          @click="emit('choosePalette', item.id)"
        >
          <span class="swatch-orb" :style="{ background: `linear-gradient(135deg, ${item.swatch}, ${item.swatch2})` }">
            <Check v-if="palette === item.id" :size="13" color="#fff" :stroke-width="3" />
          </span>
          <span class="palette-meta">
            <strong>{{ item.label }}</strong>
            <small class="tertiary">{{ item.desc }}</small>
          </span>
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.me-card {
  padding: 20px 22px;
  display: grid;
  gap: 16px;
}
.appearance-block {
  display: grid;
  gap: 10px;
  justify-items: start;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}
.appearance-block strong {
  display: block;
  font-size: 14px;
  font-weight: 620;
}
.appearance-block p {
  margin-top: 2px;
  font-size: 12px;
}
.palette-block {
  display: grid;
  gap: 10px;
}
.palette-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(145px, 1fr));
  gap: 10px;
}
.palette-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 12px;
  border-radius: 14px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  text-align: left;
  transition: background 0.16s, border-color 0.16s, transform 0.16s;
}
.palette-card:hover {
  background: var(--surface-solid);
}
.palette-card.active {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}
.swatch-orb {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  flex: none;
  display: grid;
  place-items: center;
  box-shadow: 0 3px 10px -2px rgba(0, 0, 0, 0.25);
}
.palette-meta {
  display: grid;
  line-height: 1.25;
}
.palette-meta strong {
  font-size: 13px;
  font-weight: 630;
}
.palette-meta small {
  font-size: 11px;
}
@media (max-width: 768px) {
  .me-card {
    padding: 15px 14px;
    gap: 12px;
  }
  .appearance-block .segmented {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .palette-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .palette-card {
    padding: 9px 10px;
    gap: 8px;
    border-radius: 12px;
  }
  .swatch-orb {
    width: 22px;
    height: 22px;
  }
}
</style>
