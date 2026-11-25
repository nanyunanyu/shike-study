import { onMounted, onUnmounted, ref, type Ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

export function useUnsavedGuard(dirty: Ref<boolean>, onBeforeCheck?: () => void) {
  const leaveOpen = ref(false)
  let pending: { promise: Promise<boolean>; resolve: (leave: boolean) => void } | null = null

  function resolveLeave(leave: boolean) {
    const active = pending
    pending = null
    leaveOpen.value = false
    active?.resolve(leave)
  }

  function handleBeforeUnload(event: BeforeUnloadEvent) {
    if (dirty.value) {
      event.preventDefault()
      event.returnValue = ''
    }
  }

  onMounted(() => {
    window.addEventListener('beforeunload', handleBeforeUnload)
  })

  onUnmounted(() => {
    window.removeEventListener('beforeunload', handleBeforeUnload)
    resolveLeave(false)
  })

  onBeforeRouteLeave(() => {
    onBeforeCheck?.()
    if (!dirty.value) return true
    if (!pending) {
      let resolve!: (leave: boolean) => void
      const promise = new Promise<boolean>(finish => {
        resolve = finish
      })
      pending = { promise, resolve }
      leaveOpen.value = true
    }
    return pending.promise
  })

  return { leaveOpen, resolveLeave }
}
