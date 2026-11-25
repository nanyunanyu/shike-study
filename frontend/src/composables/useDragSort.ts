import { computed, onMounted, onUnmounted, ref, type Ref } from 'vue'

interface DragGesture {
  id: string
  pointer: number
  handle: HTMLElement
  row: HTMLElement
  startX: number
  startY: number
  offsetX: number
  offsetY: number
  x: number
  y: number
}

export function useDragSort<T extends { id: string }>(
  items: Ref<T[]>,
  options: {
    itemAttr: string
    datasetKey: string
    ghostClass: string
    onMove: (from: number, to: number) => void
  },
) {
  const dragged = ref<string | null>(null)
  const hover = ref<string | null>(null)
  const dragIndex = computed(() => items.value.findIndex(item => item.id === dragged.value))

  let gesture: DragGesture | null = null
  let ghost: HTMLElement | null = null
  let scrollFrame = 0

  const selector = `[${options.itemAttr}]`

  function makeGhost(row: HTMLElement) {
    const { width, height } = row.getBoundingClientRect()
    const preview = row.cloneNode(true) as HTMLElement
    preview.removeAttribute(options.itemAttr)
    preview.classList.add(options.ghostClass)
    preview.setAttribute('aria-hidden', 'true')
    preview.style.width = `${width}px`
    preview.style.height = `${height}px`
    document.body.append(preview)
    return preview
  }

  function idAt(x: number, y: number) {
    return document.elementFromPoint(x, y)?.closest<HTMLElement>(selector)?.dataset[options.datasetKey] ?? null
  }

  function scrollNearEdge() {
    scrollFrame = 0
    if (!gesture || !ghost) return
    const { x, y } = gesture
    const step = y < 56 ? -10 : y > window.innerHeight - 64 ? 10 : 0
    if (!step) return
    const before = window.scrollY
    window.scrollBy(0, step)
    if (window.scrollY === before) return
    hover.value = idAt(x, y)
    scrollFrame = requestAnimationFrame(scrollNearEdge)
  }

  function startDrag(event: PointerEvent, id: string) {
    if (!event.isPrimary || event.button !== 0 || gesture) return
    const { pointerId, clientX, clientY } = event
    const handle = event.currentTarget as HTMLElement
    const row = handle.closest<HTMLElement>(selector)
    if (!row) return
    const { left, top } = row.getBoundingClientRect()
    handle.setPointerCapture(pointerId)
    gesture = {
      id,
      pointer: pointerId,
      handle,
      row,
      startX: clientX,
      startY: clientY,
      offsetX: clientX - left,
      offsetY: clientY - top,
      x: clientX,
      y: clientY,
    }
  }

  function trackDrag(event: PointerEvent) {
    if (gesture?.pointer !== event.pointerId) return
    if (!ghost) {
      if (Math.hypot(event.clientX - gesture.startX, event.clientY - gesture.startY) < 6) return
      ghost = makeGhost(gesture.row)
      dragged.value = gesture.id
    }
    gesture.x = event.clientX
    gesture.y = event.clientY
    ghost.style.transform = `translate3d(${gesture.x - gesture.offsetX}px, ${gesture.y - gesture.offsetY}px, 0)`
    hover.value = idAt(event.clientX, event.clientY)
    if (!scrollFrame) scrollFrame = requestAnimationFrame(scrollNearEdge)
  }

  function clearDrag() {
    const active = gesture
    gesture = null
    cancelAnimationFrame(scrollFrame)
    scrollFrame = 0
    ghost?.remove()
    ghost = null
    dragged.value = hover.value = null
    if (active?.handle.hasPointerCapture(active.pointer)) active.handle.releasePointerCapture(active.pointer)
  }

  function finishDrag(event: PointerEvent) {
    if (gesture?.pointer !== event.pointerId) return
    const target = event.type === 'pointerup' && ghost ? idAt(event.clientX, event.clientY) : null
    if (target) options.onMove(dragIndex.value, items.value.findIndex(item => item.id === target))
    clearDrag()
  }

  function cancelOnEscape(event: KeyboardEvent) {
    if (event.key === 'Escape' && gesture) clearDrag()
  }

  onMounted(() => {
    window.addEventListener('keydown', cancelOnEscape)
    window.addEventListener('blur', clearDrag)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', cancelOnEscape)
    window.removeEventListener('blur', clearDrag)
    clearDrag()
  })

  return { dragged, hover, dragIndex, startDrag, trackDrag, finishDrag, clearDrag }
}
