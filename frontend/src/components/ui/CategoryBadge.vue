<script setup lang="ts">
defineProps<{ id: string; name: string }>()
</script>

<template>
  <span class="cat-badge" :data-category="id">
    <i aria-hidden="true"></i>
    <span>{{ name }}</span>
  </span>
</template>

<style scoped>
.cat-badge {
  --dot: var(--accent);
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 100%;
  flex-shrink: 0;
  padding: 2.5px 9px;
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--dot) 11%, var(--surface-solid));
  border: 1px solid color-mix(in srgb, var(--dot) 20%, transparent);
  color: var(--ink);
  font-size: 11.5px;
  font-weight: 560;
  line-height: 1.35;
  white-space: nowrap;
}
.cat-badge span {
  min-width: 0;
  max-width: 10.5em;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cat-badge i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex: none;
  background: var(--dot);
}
.cat-badge[data-category='lecture'] { --dot: #3b82f6; }
.cat-badge[data-category='memory'] { --dot: #8b5cf6; }
.cat-badge[data-category='practice'] { --dot: #f59e0b; }
.cat-badge[data-category='review'] { --dot: #10b981; }
.cat-badge[data-category='routine'] { --dot: #64748b; }
</style>
