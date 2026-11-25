<script setup lang="ts">
defineProps<{ compact?: boolean }>()
</script>

<template>
  <div class="brand-mark" :class="{ compact }">
    <span class="brand-emblem" aria-hidden="true">
      <svg viewBox="0 0 32 32" width="20" height="20" fill="none">
        <circle cx="16" cy="16" r="10.5" stroke="rgba(255,255,255,0.34)" stroke-width="2.4" />
        <path d="M16 5.5 A10.5 10.5 0 1 1 6.9 21.2" stroke="#ffffff" stroke-width="2.6" stroke-linecap="round" />
        <path d="M16 10.5 V16 L20.2 18.6" stroke="#ffffff" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </span>
    <span class="brand-copy">
      <strong>拾刻学习</strong>
      <small v-if="!compact">Shike Studio</small>
    </span>
  </div>
</template>

<style scoped>
.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  min-width: 0;
}
.brand-emblem {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  flex: none;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  box-shadow: 0 6px 16px -6px var(--accent), inset 0 1px 0 rgba(255, 255, 255, 0.36);
}
.compact .brand-emblem {
  width: 32px;
  height: 32px;
  border-radius: 10px;
}
.brand-copy {
  display: grid;
  line-height: 1.15;
}
.brand-copy strong {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.compact .brand-copy strong {
  font-size: 15px;
}
.brand-copy small {
  margin-top: 2px;
  font-size: 10.5px;
  font-weight: 560;
  letter-spacing: 0.04em;
  color: var(--ink-tertiary);
  text-transform: uppercase;
}
</style>
