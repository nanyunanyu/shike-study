<script setup lang="ts">
import BrandMark from '@/components/ui/BrandMark.vue'
import TimepieceDial from './TimepieceDial.vue'
</script>

<template>
  <section class="auth-showcase" aria-hidden="true">
    <div class="showcase-brand">
      <BrandMark />
    </div>

    <div class="showcase-visual">
      <TimepieceDial size="hero" />
    </div>

    <p class="showcase-motto">拾起每一刻专注</p>
  </section>
</template>

<style scoped>
.auth-showcase {
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 36px;
  padding: 28px 16px;
  text-align: center;
}

.showcase-brand {
  display: flex;
  justify-content: center;
}

.showcase-visual {
  padding: 6px 0;
}

.showcase-motto {
  font-size: clamp(22px, 2.2vw, 28px);
  font-weight: 660;
  letter-spacing: 0.06em;
  line-height: 1.35;
  color: var(--ink);
  opacity: 0.9;
}

@media (max-width: 900px) {
  .auth-showcase {
    display: none;
  }
}
</style>
