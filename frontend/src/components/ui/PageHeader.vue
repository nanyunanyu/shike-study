<script setup lang="ts">
defineProps<{ title: string; subtitle?: string; eyebrow?: string }>()
</script>

<template>
  <header class="page-header">
    <div class="page-header-copy">
      <span v-if="eyebrow" class="page-eyebrow">{{ eyebrow }}</span>
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="muted">{{ subtitle }}</p>
    </div>
    <div class="page-header-actions">
      <slot />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px 20px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}
.page-header-copy {
  min-width: 0;
}
.page-eyebrow {
  display: inline-block;
  margin-bottom: 4px;
  font-size: 11.5px;
  font-weight: 640;
  letter-spacing: 0.04em;
  color: var(--accent);
}
.page-header h1 {
  font-size: 28px;
  font-weight: 720;
  line-height: 1.18;
  letter-spacing: -0.03em;
}
.page-header p {
  margin-top: 5px;
  font-size: 13.5px;
}
.page-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.page-header-actions:empty {
  display: none;
}
@media (max-width: 768px) {
  .page-header {
    align-items: stretch;
    gap: 10px;
    margin-bottom: 14px;
  }
  .page-eyebrow {
    font-size: 10.5px;
    margin-bottom: 2px;
  }
  .page-header h1 {
    font-size: 21px;
  }
  .page-header p {
    margin-top: 3px;
    font-size: 12px;
  }
  .page-header-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
