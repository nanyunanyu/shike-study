<script setup lang="ts">
import { ref } from 'vue'
import type { NavItem } from './AppSidebar.vue'

defineProps<{ navItems: NavItem[] }>()

const el = ref<HTMLElement | null>(null)
defineExpose({ el })
</script>

<template>
  <nav ref="el" class="mobile-dock glass-card-solid" aria-label="移动导航">
    <RouterLink v-for="item in navItems" :key="item.name" :to="{ name: item.name }" class="dock-item">
      <component :is="item.icon" :size="19" :stroke-width="1.9" />
      <span>{{ item.label }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.mobile-dock {
  display: none;
}

@media (max-width: 768px) {
  .mobile-dock {
    display: flex;
    align-items: center;
    position: fixed;
    left: 8px;
    right: 8px;
    bottom: max(8px, env(safe-area-inset-bottom));
    z-index: 50;
    padding: 4px 3px;
    border-radius: 20px;
    gap: 1px;
  }
  .dock-item {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    min-height: 44px;
    padding: 3px 1px;
    border-radius: 14px;
    color: var(--ink-secondary);
    font-size: 9.5px;
    font-weight: 560;
    white-space: nowrap;
    transition: background 0.18s, color 0.18s;
  }
  .dock-item :deep(svg) {
    width: 16px;
    height: 16px;
  }
  .dock-item.router-link-exact-active {
    background: var(--accent-soft);
    color: var(--accent);
    font-weight: 650;
  }
}
</style>
