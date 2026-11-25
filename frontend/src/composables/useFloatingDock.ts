import { computed, nextTick, onMounted, onUnmounted, ref, watch, type Ref } from 'vue'

type Point = { x: number; y: number }
type Dock = { edge: 'left' | 'right'; height: number }
type Gesture = { id: number; start: Point; origin: Point }

const clamp = (value: number, max: number) => Math.min(Math.max(value, 0), max)

export function useFloatingDock(options: {
  storageKey: string
  open: Ref<boolean>
  layer: Ref<HTMLElement | null>
  trigger: Ref<HTMLButtonElement | null>
  panel: Ref<HTMLElement | null>
  topBar: () => HTMLElement | null
  bottomNav: () => HTMLElement | null
  routePath: () => string
}) {
  const open = options.open
  const settling = ref(false)
  const gap = 10
  const dragThreshold = 6
  const bounds = ref({ width: 0, height: 0, compact: false })
  const panelSize = ref({ width: 0, height: 0 })
  const size = computed(() => (bounds.value.compact ? 44 : 48))
  const drag = ref<Point | null>(null)

  let gesture: Gesture | null = null
  let ignorePointerClick = false
  let resize: ResizeObserver | undefined

  function loadDock(): Dock {
    try {
      const saved = JSON.parse(window.localStorage.getItem(options.storageKey) ?? 'null')
      if ((saved?.edge === 'left' || saved?.edge === 'right') && Number.isFinite(saved.height)) {
        return { edge: saved.edge, height: clamp(saved.height, 1) }
      }
    } catch {
      /* ignore */
    }
    return { edge: 'right', height: 0.78 }
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
    const w = Math.min(width, compact ? 226 : 236)
    const h = panelSize.value.height || (compact ? 242 : 254)
    const leftEdge = dock.value.edge === 'left'
    const beside = width >= w + s + gap
    const orbCenterY = y + s / 2

    if (beside) {
      const panelLeft = leftEdge ? x + s + gap : x - w - gap
      const clampedTop = clamp(orbCenterY - h / 2, Math.max(0, height - h))
      const originY = clamp(orbCenterY - clampedTop, h)
      return {
        width: `${w}px`,
        left: `${panelLeft}px`,
        top: `${clampedTop}px`,
        transformOrigin: `${leftEdge ? '0px' : `${w}px`} ${Math.round(originY)}px`,
      }
    }

    const panelLeft = leftEdge ? 0 : Math.max(0, width - w)
    const spaceAbove = y - gap
    const spaceBelow = height - (y + s + gap)
    const placeAbove = spaceAbove >= h || spaceAbove > spaceBelow
    const panelTop = placeAbove
      ? clamp(y - gap - h, Math.max(0, height - h))
      : clamp(y + s + gap, Math.max(0, height - h))

    return {
      width: `${w}px`,
      left: `${panelLeft}px`,
      top: `${panelTop}px`,
      transformOrigin: `${leftEdge ? '24px' : `${w - 24}px`} ${placeAbove ? '100%' : '0%'}`,
    }
  })

  function measurePanel() {
    const el = options.panel.value
    if (!el) return
    const width = el.offsetWidth
    const height = el.offsetHeight
    if (width > 0 && height > 0 && (width !== panelSize.value.width || height !== panelSize.value.height)) {
      panelSize.value = { width, height }
    }
  }

  function measure() {
    const frame = options.layer.value
    if (!frame) return
    const topRect = options.topBar()?.getBoundingClientRect()
    const navRect = options.bottomNav()?.getBoundingClientRect()
    const topOffset = topRect && topRect.height > 0 ? Math.max(0, Math.ceil(topRect.bottom)) : 0
    const bottomOffset = navRect && navRect.height > 0 ? Math.max(0, Math.ceil(window.innerHeight - navRect.top)) : 0
    frame.style.setProperty('--clock-top-offset', `${topOffset}px`)
    frame.style.setProperty('--clock-bottom-offset', `${bottomOffset}px`)
    const width = frame.clientWidth
    const height = frame.clientHeight
    const compact = bottomOffset > 0 || window.innerWidth <= 768
    measurePanel()
    if (width === bounds.value.width && height === bounds.value.height && compact === bounds.value.compact) return
    settling.value = false
    bounds.value = { width, height, compact }
  }

  watch(
    [options.topBar, options.bottomNav],
    ([top, nav], [prevTop, prevNav]) => {
      if (prevTop) resize?.unobserve(prevTop)
      if (prevNav) resize?.unobserve(prevNav)
      if (top) resize?.observe(top)
      if (nav) resize?.observe(nav)
      measure()
    },
    { flush: 'post' },
  )

  watch(
    options.panel,
    (el, prev) => {
      if (prev) resize?.unobserve(prev)
      if (el) {
        resize?.observe(el)
        measurePanel()
      }
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
    if (ignorePointerClick && event.detail > 0) {
      ignorePointerClick = false
      return
    }
    open.value = !open.value
  }

  function onOutside(event: PointerEvent) {
    if (!open.value) return
    const target = event.target
    if (target instanceof Element && target.closest('[data-floating-clock-trigger]')) return
    if (target instanceof Node && !options.layer.value?.contains(target)) open.value = false
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
    const top = options.topBar()
    if (top) resize.observe(top)
    const nav = options.bottomNav()
    if (nav) resize.observe(nav)
    window.addEventListener('resize', measure)
    document.addEventListener('pointerdown', onOutside, true)
    document.addEventListener('keydown', onEscape)
  })

  onUnmounted(() => {
    open.value = false
    resize?.disconnect()
    window.removeEventListener('resize', measure)
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
