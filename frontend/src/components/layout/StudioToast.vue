<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { CheckCircle2, X } from 'lucide-vue-next'
import { toast } from '@/stores/ui'

const visible = ref(false)
let timerHandle = 0

watch(
  () => toast.version,
  () => {
    visible.value = true
    window.clearTimeout(timerHandle)
    timerHandle = window.setTimeout(() => {
      visible.value = false
    }, 3800)
  },
)

function hide() {
  visible.value = false
}

onUnmounted(() => {
  window.clearTimeout(timerHandle)
})

defineExpose({ hide })
</script>

<template>
  <Teleport to="body">
    <Transition name="toast-slide">
      <div
        v-if="visible"
        class="studio-toast glass-card-solid"
        :class="{ 'is-error': toast.error }"
        :role="toast.error ? 'alert' : 'status'"
      >
        <CheckCircle2 v-if="!toast.error" :size="17" class="accent-text" />
        <span>{{ toast.message }}</span>
        <button type="button" class="icon-btn sm" aria-label="关闭提示" @click="visible = false">
          <X :size="14" />
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.studio-toast {
  position: fixed;
  left: 50%;
  bottom: 24px;
  transform: translateX(-50%);
  z-index: 200;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px 8px 16px;
  border-radius: var(--radius-pill);
  font-size: 13px;
  font-weight: 560;
  max-width: calc(100vw - 28px);
}

.studio-toast.is-error {
  color: var(--danger);
  border-color: color-mix(in srgb, var(--danger) 30%, transparent);
}

@media (max-width: 768px) {
  .studio-toast {
    bottom: calc(68px + env(safe-area-inset-bottom));
  }
}
</style>
