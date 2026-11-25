<script setup lang="ts">
import { computed } from 'vue'
import {
  Award,
  BookOpen,
  CheckCircle2,
  Clock3,
  Crown,
  Feather,
  Flag,
  Flame,
  Hourglass,
  Medal,
  PenLine,
  Sparkles,
  Target,
  Timer,
  Trophy,
  Zap,
} from 'lucide-vue-next'
import type { Achievement } from '@/types'

const props = defineProps<{ achievements: Achievement[] }>()

const iconMap: Record<string, typeof Award> = {
  sparkles: Sparkles,
  flame: Flame,
  zap: Zap,
  crown: Crown,
  medal: Medal,
  clock: Clock3,
  hourglass: Hourglass,
  book: BookOpen,
  trophy: Trophy,
  timer: Timer,
  target: Target,
  'check-circle': CheckCircle2,
  pen: PenLine,
  feather: Feather,
  flag: Flag,
}

const unlockedCount = computed(() => props.achievements.filter(a => a.unlocked).length)
</script>

<template>
  <section class="badge-panel glass-card">
    <header class="section-head">
      <div class="section-title">
        <Award :size="18" />
        <h2>学习成就徽章</h2>
      </div>
      <span class="pill accent tabular">已点亮 {{ unlockedCount }} / {{ achievements.length }}</span>
    </header>

    <div class="badge-grid">
      <article v-for="item in achievements" :key="item.id" class="badge-card" :class="{ unlocked: item.unlocked }">
        <div class="badge-medal">
          <component :is="iconMap[item.icon] ?? Award" :size="20" />
        </div>
        <div class="badge-copy">
          <strong>{{ item.title }}</strong>
          <small class="muted">{{ item.description }}</small>
          <div class="badge-meter">
            <div class="meter-track">
              <span :style="{ width: `${Math.min(100, Math.round((item.progress / Math.max(1, item.target)) * 100))}%` }"></span>
            </div>
            <span class="meter-num tabular">{{ item.progress }}/{{ item.target }}{{ item.unit }}</span>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.badge-panel {
  padding: 20px 22px;
  display: grid;
  gap: 16px;
}
.badge-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
@media (max-width: 960px) {
  .badge-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
.badge-card {
  padding: 14px;
  border-radius: 16px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 12px;
  opacity: 0.72;
  transition: transform 0.2s var(--ease-spring), border-color 0.2s, opacity 0.2s;
}
.badge-card.unlocked {
  opacity: 1;
  background:
    radial-gradient(80% 90% at 0% 0%, var(--accent-soft), transparent 72%),
    var(--surface-solid);
  border-color: var(--accent-border);
}
.badge-card.unlocked:hover {
  transform: translateY(-2px);
}
.badge-medal {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  flex: none;
  display: grid;
  place-items: center;
  background: var(--surface-hover);
  color: var(--ink-tertiary);
}
.badge-card.unlocked .badge-medal {
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: var(--on-accent);
  box-shadow: 0 8px 18px -8px var(--accent);
}
.badge-copy {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 3px;
}
.badge-copy strong {
  font-size: 13.5px;
  font-weight: 660;
}
.badge-copy small {
  font-size: 11.5px;
}
.badge-meter {
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.meter-track {
  flex: 1;
  height: 5px;
  border-radius: var(--radius-pill);
  background: var(--surface-hover);
  overflow: hidden;
}
.meter-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
}
.meter-num {
  font-size: 10.5px;
  color: var(--ink-tertiary);
  white-space: nowrap;
}
@media (max-width: 768px) {
  .badge-panel {
    padding: 15px 14px;
    gap: 12px;
  }
  .badge-grid {
    grid-template-columns: 1fr;
    gap: 9px;
  }
  .badge-card {
    padding: 11px 12px;
    gap: 11px;
    border-radius: 14px;
  }
  .badge-medal {
    width: 38px;
    height: 38px;
    border-radius: 11px;
  }
}
</style>
