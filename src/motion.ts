import { onUnmounted, ref } from 'vue'

export function useMotionCue<T>(durationMs: number) {
  const cue = ref<T | null>(null)
  let handle = 0

  function clear() {
    window.clearTimeout(handle)
    cue.value = null
  }

  function play(value: T) {
    clear()
    cue.value = value
    handle = window.setTimeout(() => {
      cue.value = null
    }, durationMs)
  }

  onUnmounted(clear)
  return { cue, play, clear }
}
