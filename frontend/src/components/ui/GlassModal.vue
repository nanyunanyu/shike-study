<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue'
import { X } from 'lucide-vue-next'
import { activeDialogs } from '@/stores/ui'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title: string
    subtitle?: string
    busy?: boolean
    drawer?: boolean
    wide?: boolean
    centered?: boolean
  }>(),
  { busy: false, drawer: false, wide: false, centered: false },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'after-leave': []
}>()

const panelRef = ref<HTMLElement | null>(null)
let counted = false

function close() {
  if (!props.busy) emit('update:modelValue', false)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.modelValue) {
    event.preventDefault()
    close()
  }
}

watch(
  () => props.modelValue,
  async open => {
    if (open && !counted) {
      counted = true
      activeDialogs.value++
      window.addEventListener('keydown', onKeydown)
      await nextTick()
      panelRef.value?.focus({ preventScroll: true })
    } else if (!open && counted) {
      counted = false
      activeDialogs.value = Math.max(0, activeDialogs.value - 1)
      window.removeEventListener('keydown', onKeydown)
    }
  },
  { immediate: true },
)

onUnmounted(() => {
  if (counted) {
    counted = false
    activeDialogs.value = Math.max(0, activeDialogs.value - 1)
    window.removeEventListener('keydown', onKeydown)
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition :name="drawer ? 'sheet-slide' : 'modal-zoom'" @after-leave="emit('after-leave')">
      <div
        v-if="modelValue"
        class="glass-overlay"
        :class="{ 'is-drawer': drawer, 'is-centered': centered }"
        role="presentation"
        @click.self="close"
      >
        <section
          ref="panelRef"
          class="glass-dialog glass-card-solid"
          :class="{ drawer, wide }"
          role="dialog"
          aria-modal="true"
          :aria-label="title"
          tabindex="-1"
        >
          <div v-if="drawer" class="sheet-grabber" aria-hidden="true"><span></span></div>
          <header class="glass-dialog-head">
            <div class="glass-dialog-titles">
              <h2>{{ title }}</h2>
              <p v-if="subtitle" class="muted">{{ subtitle }}</p>
            </div>
            <button
              class="icon-btn"
              type="button"
              :disabled="busy"
              aria-label="关闭窗口"
              title="关闭"
              @click="close"
            >
              <X :size="18" />
            </button>
          </header>
          <div class="glass-dialog-body">
            <slot />
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.glass-overlay {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: grid;
  place-items: center;
  padding: 20px;
  background: var(--backdrop-scrim);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
.glass-overlay.is-drawer {
  display: flex;
  justify-content: flex-end;
  align-items: stretch;
  padding: 12px;
}
.glass-dialog {
  width: min(100%, 480px);
  max-height: calc(100dvh - 40px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  outline: none;
  border-radius: var(--radius-xl);
}
.glass-dialog.wide {
  width: min(100%, 640px);
}
.glass-dialog.drawer {
  width: min(100%, 560px);
  max-height: 100%;
  height: 100%;
  border-radius: var(--radius-xl);
}
.sheet-grabber {
  display: none;
}
.glass-dialog-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 20px 22px 14px;
  border-bottom: 1px solid var(--border);
}
.glass-dialog-titles {
  min-width: 0;
}
.glass-dialog-head h2 {
  font-size: 17px;
  font-weight: 680;
  letter-spacing: -0.02em;
  overflow-wrap: anywhere;
}
.glass-dialog-head p {
  margin-top: 3px;
  font-size: 12.5px;
}
.glass-dialog-body {
  padding: 18px 22px 22px;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.modal-zoom-enter-active,
.modal-zoom-leave-active {
  transition: opacity 0.2s var(--ease-out);
}
.modal-zoom-enter-active .glass-dialog,
.modal-zoom-leave-active .glass-dialog {
  transition: transform 0.26s var(--ease-spring), opacity 0.2s var(--ease-out);
}
.modal-zoom-enter-from,
.modal-zoom-leave-to {
  opacity: 0;
}
.modal-zoom-enter-from .glass-dialog,
.modal-zoom-leave-to .glass-dialog {
  opacity: 0;
  transform: scale(0.95) translateY(8px);
}

.sheet-slide-enter-active,
.sheet-slide-leave-active {
  transition: opacity 0.22s var(--ease-out);
}
.sheet-slide-enter-active .glass-dialog,
.sheet-slide-leave-active .glass-dialog {
  transition: transform 0.3s var(--ease-spring);
}
.sheet-slide-enter-from,
.sheet-slide-leave-to {
  opacity: 0;
}
.sheet-slide-enter-from .glass-dialog,
.sheet-slide-leave-to .glass-dialog {
  transform: translateX(36px);
}

@media (max-width: 768px) {
  .glass-overlay {
    padding: 12px 10px max(10px, env(safe-area-inset-bottom));
    align-items: end;
  }
  .glass-overlay.is-centered {
    align-items: center;
    justify-items: center;
    padding: max(20px, env(safe-area-inset-top)) 14px max(20px, env(safe-area-inset-bottom));
  }
  .glass-overlay.is-drawer {
    align-items: flex-end;
    justify-content: center;
    padding: 12px 10px max(10px, env(safe-area-inset-bottom));
  }
  .glass-dialog {
    max-height: calc(100dvh - 24px);
    border-radius: 22px;
  }
  .glass-overlay.is-centered .glass-dialog {
    width: min(100%, 480px);
    max-height: min(78dvh, calc(100dvh - 48px));
    border-radius: 22px;
  }
  .glass-dialog.drawer {
    width: min(100%, 520px);
    height: auto;
    min-height: min(280px, 38dvh);
    max-height: 74dvh;
    border-radius: 24px;
  }
  .sheet-grabber {
    display: flex;
    justify-content: center;
    padding: 10px 0 2px;
    flex: none;
  }
  .sheet-grabber span {
    width: 36px;
    height: 4px;
    border-radius: var(--radius-pill);
    background: var(--border-strong);
  }
  .glass-dialog.drawer .glass-dialog-head {
    padding: 10px 18px 12px;
  }
  .glass-dialog.drawer .glass-dialog-body {
    padding: 14px 18px 18px;
  }
  .sheet-slide-enter-from .glass-dialog,
  .sheet-slide-leave-to .glass-dialog {
    transform: translateY(36px);
  }
}
</style>
