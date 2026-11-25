<script setup lang="ts">
import { nextTick, onUnmounted, ref } from 'vue'

const props = withDefaults(defineProps<{ align?: 'left' | 'right' }>(), { align: 'right' })

const open = ref(false)
const root = ref<HTMLElement | null>(null)
const menuRef = ref<HTMLElement | null>(null)
const style = ref<Record<string, string>>({})

function updatePosition() {
  if (!root.value) return
  const rect = root.value.getBoundingClientRect()
  const margin = 10
  const vw = window.innerWidth
  const vh = window.innerHeight
  const menuW = menuRef.value?.offsetWidth || 184
  const menuH = menuRef.value?.offsetHeight || 220

  const topBelow = rect.bottom + 6
  const topAbove = rect.top - 6 - menuH
  const fitsBelow = topBelow + menuH <= vh - margin
  const fitsAbove = topAbove >= margin
  const openUp = !fitsBelow && (fitsAbove || rect.top > vh - rect.bottom)
  const rawTop = openUp ? topAbove : topBelow
  const top = Math.min(Math.max(margin, rawTop), Math.max(margin, vh - menuH - margin))

  const rightAlignedLeft = rect.right - menuW
  const leftAlignedLeft = rect.left
  let rawLeft: number
  if (props.align === 'right') {
    rawLeft = rightAlignedLeft >= margin ? rightAlignedLeft : leftAlignedLeft
  } else {
    rawLeft = leftAlignedLeft + menuW <= vw - margin ? leftAlignedLeft : rightAlignedLeft
  }
  const left = Math.min(Math.max(margin, rawLeft), Math.max(margin, vw - menuW - margin))

  style.value = {
    position: 'fixed',
    zIndex: '130',
    top: `${Math.round(top)}px`,
    left: `${Math.round(left)}px`,
    transformOrigin: `${props.align === 'right' && rawLeft === rightAlignedLeft ? 'right' : 'left'} ${openUp ? 'bottom' : 'top'}`,
  }
}

async function toggle() {
  open.value = !open.value
  if (open.value) {
    updatePosition()
    document.addEventListener('pointerdown', onOutside, true)
    document.addEventListener('keydown', onEscape)
    window.addEventListener('scroll', close, true)
    window.addEventListener('resize', close)
    await nextTick()
    updatePosition()
    menuRef.value?.querySelector<HTMLButtonElement>('[role="menuitem"]')?.focus()
  } else {
    cleanup()
  }
}

function close() {
  if (!open.value) return
  open.value = false
  cleanup()
}

function cleanup() {
  document.removeEventListener('pointerdown', onOutside, true)
  document.removeEventListener('keydown', onEscape)
  window.removeEventListener('scroll', close, true)
  window.removeEventListener('resize', close)
}

function onOutside(event: PointerEvent) {
  const target = event.target as Node | null
  if (!target) return
  if (!root.value?.contains(target) && !menuRef.value?.contains(target)) close()
}

function onEscape(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault()
    close()
  }
}

function onMenuKey(event: KeyboardEvent) {
  if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  const items = [...(menuRef.value?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]') ?? [])]
  if (!items.length) return
  const idx = items.indexOf(document.activeElement as HTMLButtonElement)
  const next =
    event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? items.length - 1
        : (idx + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length
  items[next]?.focus()
}

onUnmounted(cleanup)
defineExpose({ close })
</script>

<template>
  <div ref="root" class="popover-anchor">
    <slot name="trigger" :open="open" :toggle="toggle" />
    <Teleport to="body">
      <Transition name="pop-fade">
        <div
          v-if="open"
          ref="menuRef"
          class="glass-popover glass-card-solid"
          role="menu"
          :style="style"
          @keydown="onMenuKey"
          @click="close"
        >
          <slot :close="close" />
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.popover-anchor {
  display: inline-flex;
}
.glass-popover {
  min-width: 176px;
  max-width: calc(100vw - 20px);
  padding: 5px;
  border-radius: var(--radius-md);
  display: grid;
  gap: 2px;
}
.glass-popover :deep(button) {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  min-height: 36px;
  padding: 0 11px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 540;
  color: var(--ink);
  text-align: left;
  transition: background 0.16s, color 0.16s;
}
.glass-popover :deep(button:hover),
.glass-popover :deep(button:focus-visible) {
  background: var(--accent-soft);
  color: var(--accent);
  outline: none;
}
.glass-popover :deep(button.danger-item) {
  color: var(--danger);
}
.glass-popover :deep(button.danger-item:hover),
.glass-popover :deep(button.danger-item:focus-visible) {
  background: var(--danger-soft);
  color: var(--danger);
}

.pop-fade-enter-active,
.pop-fade-leave-active {
  transition: opacity 0.15s var(--ease-out), transform 0.2s var(--ease-spring);
}
.pop-fade-enter-from,
.pop-fade-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-4px);
}
</style>
