import { computed, nextTick, onMounted, onUnmounted, ref, watch, type Ref } from 'vue'

type Point = { x: number; y: number }
type Dock = { edge: 'left' | 'right'; height: number }
type Gesture = { id: number; start: Point; origin: Point }

const clamp = (value: number, max: number) => Math.min(Math.max(value, 0), max)

export function useFloatingDock(options: {
  storageKey: string
  layer: Ref<HTMLElement | null>
  trigger: Ref<HTMLButtonElement | null>
  bottomNav: () => HTMLElement | null
  routePath: () => string
  onOpenChange: (open: boolean) => void
}) {
  const open = ref(false)
  const settling = ref(false)
  const gap = 10
  const dragThreshold = 7
  const bounds = ref({ width: 0, height: 0, compact: false })
  const size = computed(() => (bounds.value.compact ? 42 : 48))
  const drag = ref<Point | null>(null)

  let gesture: Gesture | null = null
  let ignorePointerClick = false
  let resize: ResizeObserver | undefined

  watch(open, value => options.onOpenChange(value), { flush: 'sync' })

  function loadDock(): Dock {
    try {
      const saved = JSON.parse(window.localStorage.getItem(options.storageKey) ?? 'null')
      if ((saved?.edge === 'left' || saved?.edge === 'right') && Number.isFinite(saved.height)) {
        return { edge: saved.edge, height: clamp(saved.height, 1) }
      }
    } catch {
      /* ignore */
    }
    return { edge: 'right', height: 1 }
  }

  const dock = ref<Dock>(loadDock())
  const maxX = computed(() => Math.max(0, bounds.value.width - size.value))
  const maxY = computed(() => Math.max(0, bounds.value.height - size.value))
  const position = computed(() =>
    drag.value
      ? { x: clamp(drag.value.x, maxX.value), y: clamp(drag.value.y, maxY.value) }
      : { x: dock.value.edge === 'left' ? 0 : maxX.value, y: dock.value.height * maxY.value },
  )

  const panelPlacement = computed(() => {
    const { width, height, compact } = bounds.value
    const { x, y } = position.value
    const s = size.value
    const w = Math.min(width, compact ? 268 : 304)
    const left = dock.value.edge === 'left'
    const beside = width >= w + s + gap
    const above = beside ? y > maxY.value / 2 : y >= height - y - s
    return {
      width: `${w}px`,
      left: `${beside ? (left ? x + s + gap : x - w - gap) : left ? 0 : width - w}px`,
      top: above ? undefined : `${beside ? y : y + s + gap}px`,
      bottom: above ? `${height - y - (beside ? s : 0) + (beside ? 0 : gap)}px` : undefined,
    }
  })

  function measure() {
    const frame = options.layer.value
    if (!frame) return
    const navHeight = options.bottomNav()?.offsetHeight ?? 0
    frame.style.setProperty('--clock-nav-height', `${navHeight}px`)
    const width = frame.clientWidth
    const height = frame.clientHeight
    const compact = navHeight > 0
    if (width === bounds.value.width && height === bounds.value.height && compact === bounds.value.compact) return
    settling.value = false
    bounds.value = { width, height, compact }
  }

  watch(
    options.bottomNav,
    (nav, previous) => {
      if (previous) resize?.unobserve(previous)
      if (nav) resize?.observe(nav)
      measure()
    },
    { flush: 'post' },
  )

  function beginPointer(event: PointerEvent) {
    if (!event.isPrimary || event.button !== 0 || gesture || !options.trigger.value || !options.layer.value) return
    const frame = options.layer.value.getBoundingClientRect()
    const button = options.trigger.value.getBoundingClientRect()
    gesture = {
      id: event.pointerId,
      start: { x: event.clientX, y: event.clientY },
      origin: { x: button.left - frame.left, y: button.top - frame.top },
    }
    ignorePointerClick = false
    options.trigger.value.setPointerCapture(event.pointerId)
  }

  function movePointer(event: PointerEvent) {
    if (!gesture || event.pointerId !== gesture.id) return
    const dx = event.clientX - gesture.start.x
    const dy = event.clientY - gesture.start.y
    if (!drag.value && Math.hypot(dx, dy) < dragThreshold) return
    settling.value = false
    open.value = false
    drag.value = { x: gesture.origin.x + dx, y: gesture.origin.y + dy }
  }

  function clearPointer() {
    const id = gesture?.id
    gesture = null
    drag.value = null
    if (id != null && options.trigger.value?.hasPointerCapture(id)) options.trigger.value.releasePointerCapture(id)
  }

  function endPointer(event: PointerEvent) {
    if (gesture?.id !== event.pointerId) return
    movePointer(event)
    if (drag.value) {
      const { x, y } = position.value
      dock.value = { edge: x < maxX.value / 2 ? 'left' : 'right', height: maxY.value ? y / maxY.value : dock.value.height }
      settling.value = true
      ignorePointerClick = true
      try {
        window.localStorage.setItem(options.storageKey, JSON.stringify(dock.value))
      } catch {
        /* ignore */
      }
    }
    clearPointer()
  }

  function toggle(event: MouseEvent) {
    if (ignorePointerClick && event.detail > 0) return
    open.value = !open.value
  }

  function onOutside(event: PointerEvent) {
    if (open.value && event.target instanceof Node && !options.layer.value?.contains(event.target)) open.value = false
  }

  function onEscape(event: KeyboardEvent) {
    if (open.value && event.key === 'Escape') {
      event.preventDefault()
      open.value = false
      void nextTick(() => options.trigger.value?.focus({ preventScroll: true }))
    }
  }

  watch(options.routePath, () => {
    open.value = false
    clearPointer()
  })

  onMounted(() => {
    measure()
    resize = new ResizeObserver(measure)
    if (options.layer.value) resize.observe(options.layer.value)
    const nav = options.bottomNav()
    if (nav) resize.observe(nav)
    document.addEventListener('pointerdown', onOutside, true)
    document.addEventListener('keydown', onEscape)
  })

  onUnmounted(() => {
    if (open.value) options.onOpenChange(false)
    resize?.disconnect()
    document.removeEventListener('pointerdown', onOutside, true)
    document.removeEventListener('keydown', onEscape)
  })

  return {
    open,
    settling,
    bounds,
    size,
    drag,
    position,
    panelPlacement,
    beginPointer,
    movePointer,
    endPointer,
    clearPointer,
    toggle,
  }
}
