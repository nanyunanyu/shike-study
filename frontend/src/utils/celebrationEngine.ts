export type CheckInScene =
  | 'chronos-bloom'
  | 'aurora-ribbons'
  | 'starfall-prism'
  | 'lantern-fireflies'
  | 'celestial-fireworks'

export const CHECKIN_SCENES: readonly CheckInScene[] = [
  'chronos-bloom',
  'aurora-ribbons',
  'starfall-prism',
  'lantern-fireflies',
  'celestial-fireworks',
]

export interface CelebrationOrigin {
  x: number
  y: number
}

export interface CelebrationPlayerOptions {
  scene: CheckInScene
  origin: CelebrationOrigin
  milestone: boolean
  onComplete?: () => void
}

export interface CelebrationPlayer {
  fadeOut: () => void
  destroy: () => void
}

type RGB = [number, number, number]

interface ResolvedPalette {
  isDark: boolean
  accent: RGB
  accent2: RGB
  accentLight: RGB
  accentDeep: RGB
  success: RGB
  gold: RGB
  champagne: RGB
  pearl: RGB
  swatches: RGB[]
}

const MILESTONE_TITLES: Record<number, string> = {
  3: '三日成习',
  7: '七日连胜',
  14: '半月精进',
  21: '廿一养成',
  30: '满月恒心',
  50: '五十里程',
  100: '百日筑基',
  180: '半载沉淀',
  365: '周岁长明',
}

export function resolveStreakMilestone(streak: number): string | null {
  if (streak <= 0) return null
  if (MILESTONE_TITLES[streak]) return MILESTONE_TITLES[streak]
  if (streak > 100 && streak % 100 === 0) return `${streak} 日里程碑`
  return null
}

let sceneBag: CheckInScene[] = []
let lastScene: CheckInScene | null = null

export function chooseCheckInScene(): CheckInScene {
  if (!sceneBag.length) {
    sceneBag = [...CHECKIN_SCENES]
    for (let i = sceneBag.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[sceneBag[i], sceneBag[j]] = [sceneBag[j]!, sceneBag[i]!]
    }
    if (lastScene && sceneBag.length > 1 && sceneBag[sceneBag.length - 1] === lastScene) {
      ;[sceneBag[0], sceneBag[sceneBag.length - 1]] = [sceneBag[sceneBag.length - 1]!, sceneBag[0]!]
    }
  }
  const picked = sceneBag.pop() ?? CHECKIN_SCENES[0]!
  lastScene = picked
  return picked
}

function parseColor(raw: string, fallback: RGB): RGB {
  const value = raw.trim()
  if (!value) return fallback
  if (value.startsWith('#')) {
    const hex = value.slice(1)
    if (hex.length === 3) {
      return [
        parseInt(hex[0]! + hex[0]!, 16),
        parseInt(hex[1]! + hex[1]!, 16),
        parseInt(hex[2]! + hex[2]!, 16),
      ]
    }
    if (hex.length >= 6) {
      return [
        parseInt(hex.slice(0, 2), 16),
        parseInt(hex.slice(2, 4), 16),
        parseInt(hex.slice(4, 6), 16),
      ]
    }
  }
  const match = value.match(/rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)/i)
  if (match) {
    return [Number(match[1]), Number(match[2]), Number(match[3])]
  }
  return fallback
}

function mixRgb(a: RGB, b: RGB, t: number): RGB {
  return [
    Math.round(a[0] + (b[0] - a[0]) * t),
    Math.round(a[1] + (b[1] - a[1]) * t),
    Math.round(a[2] + (b[2] - a[2]) * t),
  ]
}

function rgba(rgb: RGB, alpha: number): string {
  const a = Math.max(0, Math.min(1, alpha))
  return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${a.toFixed(3)})`
}

function resolveCelebrationPalette(milestone: boolean): ResolvedPalette {
  const root = document.documentElement
  const style = getComputedStyle(root)
  const isDark = root.dataset.appearance === 'dark'

  const accent = parseColor(style.getPropertyValue('--accent'), isDark ? [96, 165, 250] : [37, 99, 235])
  const accent2 = parseColor(style.getPropertyValue('--accent-2'), isDark ? [56, 189, 248] : [14, 165, 233])
  const success = parseColor(style.getPropertyValue('--success'), isDark ? [52, 211, 153] : [5, 150, 105])
  const warning = parseColor(style.getPropertyValue('--warning'), isDark ? [251, 191, 36] : [217, 119, 6])

  const gold: RGB = isDark ? [251, 191, 36] : [234, 146, 20]
  const champagne: RGB = isDark ? [254, 240, 138] : [253, 210, 96]
  const pearl: RGB = isDark ? [248, 250, 252] : [255, 255, 255]
  const accentLight = mixRgb(accent, [255, 255, 255], isDark ? 0.36 : 0.24)
  const accentDeep = mixRgb(accent, [15, 23, 42], isDark ? 0.14 : 0.26)
  const accent2Light = mixRgb(accent2, [255, 255, 255], isDark ? 0.32 : 0.2)

  const swatches: RGB[] = milestone
    ? [gold, champagne, accent, accent2, accentLight, warning, pearl]
    : [accent, accent2, accentLight, accent2Light, success, gold, isDark ? pearl : accentDeep]

  return {
    isDark,
    accent,
    accent2,
    accentLight,
    accentDeep,
    success,
    gold,
    champagne,
    pearl,
    swatches,
  }
}

function rand(min: number, max: number): number {
  return min + Math.random() * (max - min)
}

function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]!
}

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v))
}

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - clamp01(t), 3)
}

function easeOutQuart(t: number): number {
  return 1 - Math.pow(1 - clamp01(t), 4)
}

function easeInOutSine(t: number): number {
  return -(Math.cos(Math.PI * clamp01(t)) - 1) / 2
}

// --- Primitive Entities ---

interface RingEntity {
  x: number
  y: number
  r0: number
  r1: number
  color: RGB
  lineWidth: number
  age: number
  life: number
  delay: number
  dashed?: boolean
  glow?: boolean
}

interface SparkEntity {
  x: number
  y: number
  vx: number
  vy: number
  ax: number
  ay: number
  drag: number
  size: number
  rotation: number
  vRot: number
  shape: 'star4' | 'diamond' | 'dot' | 'crescent' | 'shard'
  color: RGB
  secondary: RGB
  age: number
  life: number
  delay: number
  twinkleSpeed: number
  twinklePhase: number
  swayAmp: number
  swayFreq: number
  swayPhase: number
  glow: number
}

interface RibbonPoint {
  x: number
  y: number
}

interface RibbonEntity {
  x: number
  y: number
  vx: number
  vy: number
  gravity: number
  drag: number
  width: number
  colorFront: RGB
  colorBack: RGB
  twistPhase: number
  twistSpeed: number
  flutterAmp: number
  flutterFreq: number
  flutterPhase: number
  age: number
  life: number
  delay: number
  maxPoints: number
  points: RibbonPoint[]
  shedCooldown: number
}

interface TrailSparkEntity {
  x: number
  y: number
  vx: number
  vy: number
  gravity: number
  drag: number
  color: RGB
  core: RGB
  width: number
  age: number
  life: number
  delay: number
  history: RibbonPoint[]
  maxHistory: number
  crackle?: boolean
  crackled?: boolean
}

interface CometEntity {
  x0: number
  y0: number
  x1: number
  y1: number
  cx: number
  cy: number
  color: RGB
  age: number
  life: number
  delay: number
  history: RibbonPoint[]
  onArrive?: (x: number, y: number) => void
  arrived?: boolean
}

interface DialEntity {
  cx: number
  cy: number
  radius: number
  color: RGB
  accent2: RGB
  gold: RGB
  age: number
  life: number
  delay: number
  ticksEmitted: Set<number>
}

interface FireflyEntity {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  color: RGB
  age: number
  life: number
  delay: number
  driftFreq: number
  driftAmp: number
  driftPhase: number
  pulseSpeed: number
  bloomAt?: number
  bloomed?: boolean
  history: RibbonPoint[]
}

interface CausticWaveEntity {
  y: number
  height: number
  colorA: RGB
  colorB: RGB
  colorC: RGB
  age: number
  life: number
  delay: number
}

function drawFourPointStar(ctx: CanvasRenderingContext2D, r: number, innerRatio = 0.28) {
  const ir = r * innerRatio
  ctx.beginPath()
  for (let i = 0; i < 8; i++) {
    const rad = i % 2 === 0 ? r : ir
    const a = (i * Math.PI) / 4
    const px = Math.cos(a) * rad
    const py = Math.sin(a) * rad
    if (i === 0) ctx.moveTo(px, py)
    else ctx.lineTo(px, py)
  }
  ctx.closePath()
}

function drawDiamond(ctx: CanvasRenderingContext2D, r: number) {
  ctx.beginPath()
  ctx.moveTo(0, -r * 1.25)
  ctx.lineTo(r * 0.72, 0)
  ctx.lineTo(0, r * 1.25)
  ctx.lineTo(-r * 0.72, 0)
  ctx.closePath()
}

function drawCrescent(ctx: CanvasRenderingContext2D, r: number) {
  ctx.beginPath()
  ctx.arc(0, 0, r, 0.25 * Math.PI, 1.75 * Math.PI, false)
  ctx.arc(r * 0.42, 0, r * 0.78, 1.62 * Math.PI, 0.38 * Math.PI, true)
  ctx.closePath()
}

function drawPrismShard(ctx: CanvasRenderingContext2D, r: number) {
  ctx.beginPath()
  ctx.moveTo(0, -r * 1.35)
  ctx.lineTo(r * 0.85, -r * 0.15)
  ctx.lineTo(r * 0.3, r * 1.15)
  ctx.lineTo(-r * 0.78, r * 0.35)
  ctx.closePath()
}

export function createCelebrationPlayer(
  canvas: HTMLCanvasElement,
  options: CelebrationPlayerOptions,
): CelebrationPlayer {
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    options.onComplete?.()
    return { fadeOut: () => {}, destroy: () => {} }
  }

  let width = window.innerWidth
  let height = window.innerHeight
  let dpr = Math.min(window.devicePixelRatio || 1, 2)

  function syncSize() {
    width = window.innerWidth
    height = window.innerHeight
    dpr = Math.min(window.devicePixelRatio || 1, 2)
    canvas.width = Math.round(width * dpr)
    canvas.height = Math.round(height * dpr)
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`
    ctx!.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  syncSize()
  window.addEventListener('resize', syncSize)

  const palette = resolveCelebrationPalette(options.milestone)
  const isCompact = width < 768
  const density = (isCompact ? 0.68 : 1) * (options.milestone ? 1.32 : 1)
  const cx = width * 0.5
  const cy = height * (isCompact ? 0.36 : 0.4)
  const ox = Math.max(24, Math.min(width - 24, options.origin.x || cx))
  const oy = Math.max(24, Math.min(height - 24, options.origin.y || cy))

  const rings: RingEntity[] = []
  const sparks: SparkEntity[] = []
  const ribbons: RibbonEntity[] = []
  const trails: TrailSparkEntity[] = []
  const comets: CometEntity[] = []
  const dials: DialEntity[] = []
  const fireflies: FireflyEntity[] = []
  const caustics: CausticWaveEntity[] = []

  function addOriginPulse() {
    rings.push(
      {
        x: ox,
        y: oy,
        r0: 14,
        r1: isCompact ? 115 : 165,
        color: palette.accent,
        lineWidth: 2.4,
        age: 0,
        life: 0.62,
        delay: 0,
        glow: true,
      },
      {
        x: ox,
        y: oy,
        r0: 10,
        r1: isCompact ? 80 : 112,
        color: options.milestone ? palette.gold : palette.accent2,
        lineWidth: 1.5,
        age: 0,
        life: 0.52,
        delay: 0.08,
      },
    )

    const count = Math.round(14 * density)
    for (let i = 0; i < count; i++) {
      const a = (Math.PI * 2 * i) / count + rand(-0.18, 0.18)
      const spd = rand(110, 290)
      sparks.push({
        x: ox,
        y: oy,
        vx: Math.cos(a) * spd,
        vy: Math.sin(a) * spd - 35,
        ax: 0,
        ay: 140,
        drag: 2.3,
        size: rand(3.2, 6.2),
        rotation: rand(0, Math.PI * 2),
        vRot: rand(-4, 4),
        shape: i % 3 === 0 ? 'star4' : 'diamond',
        color: pick(palette.swatches),
        secondary: palette.pearl,
        age: 0,
        life: rand(0.65, 1.15),
        delay: rand(0, 0.06),
        twinkleSpeed: rand(6, 11),
        twinklePhase: rand(0, Math.PI * 2),
        swayAmp: 0,
        swayFreq: 0,
        swayPhase: 0,
        glow: 1,
      })
    }
  }

  function addMilestoneCrest() {
    if (!options.milestone) return
    const baseR = Math.min(width, height) * (isCompact ? 0.34 : 0.27)
    rings.push(
      {
        x: cx,
        y: cy,
        r0: 36,
        r1: baseR * 1.45,
        color: palette.gold,
        lineWidth: 2.6,
        age: 0,
        life: 1.1,
        delay: 0.44,
        glow: true,
      },
      {
        x: cx,
        y: cy,
        r0: 44,
        r1: baseR * 1.15,
        color: palette.champagne,
        lineWidth: 1.4,
        age: 0,
        life: 1.25,
        delay: 0.54,
        dashed: true,
      },
    )

    const count = Math.round(28 * (isCompact ? 0.72 : 1))
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + rand(-0.08, 0.08)
      const spd = rand(180, isCompact ? 340 : 460)
      sparks.push({
        x: cx + Math.cos(angle) * 26,
        y: cy + Math.sin(angle) * 26,
        vx: Math.cos(angle) * spd,
        vy: Math.sin(angle) * spd,
        ax: 0,
        ay: 68,
        drag: 1.85,
        size: rand(4.5, 8.5),
        rotation: rand(0, Math.PI * 2),
        vRot: rand(-3.5, 3.5),
        shape: i % 2 === 0 ? 'star4' : 'diamond',
        color: i % 3 === 0 ? palette.champagne : palette.gold,
        secondary: palette.pearl,
        age: 0,
        life: rand(1.3, 2.05),
        delay: 0.46 + rand(0, 0.14),
        twinkleSpeed: rand(7, 13),
        twinklePhase: rand(0, Math.PI * 2),
        swayAmp: rand(8, 20),
        swayFreq: rand(1.8, 3.2),
        swayPhase: rand(0, Math.PI * 2),
        glow: 1.2,
      })
    }
  }

  // --- Scene 1: 拾刻光轮 (Chronos Bloom) ---
  function setupChronosBloom() {
    addOriginPulse()
    const dialRadius = Math.min(width, height) * (isCompact ? 0.34 : 0.27)

    // Energy filaments racing from check-in button to optical center
    const filamentCount = 4
    for (let i = 0; i < filamentCount; i++) {
      const spread = (i - (filamentCount - 1) / 2) * (isCompact ? 48 : 92)
      comets.push({
        x0: ox,
        y0: oy,
        x1: cx,
        y1: cy,
        cx: (ox + cx) * 0.5 + spread,
        cy: Math.min(oy, cy) - rand(55, 135),
        color: i % 2 === 0 ? palette.accent : palette.accent2,
        age: 0,
        life: 0.34 + i * 0.035,
        delay: i * 0.025,
        history: [],
      })
    }

    dials.push({
      cx,
      cy,
      radius: dialRadius,
      color: palette.accent,
      accent2: palette.accent2,
      gold: options.milestone ? palette.gold : palette.accentLight,
      age: 0,
      life: 2.35,
      delay: 0.2,
      ticksEmitted: new Set(),
    })

    rings.push(
      {
        x: cx,
        y: cy,
        r0: dialRadius * 0.35,
        r1: dialRadius * 1.72,
        color: palette.accent2,
        lineWidth: 1.8,
        age: 0,
        life: 1.45,
        delay: 0.26,
        glow: true,
      },
      {
        x: cx,
        y: cy,
        r0: dialRadius * 0.55,
        r1: dialRadius * 1.35,
        color: palette.accent,
        lineWidth: 1.2,
        age: 0,
        life: 1.65,
        delay: 0.42,
        dashed: true,
      },
    )

    // Orbiting and rising stardust field across viewport
    const dustCount = Math.round(68 * density)
    for (let i = 0; i < dustCount; i++) {
      const a = rand(0, Math.PI * 2)
      const r = rand(dialRadius * 0.32, dialRadius * 1.15)
      const spd = rand(55, isCompact ? 185 : 275)
      sparks.push({
        x: cx + Math.cos(a) * r * 0.55,
        y: cy + Math.sin(a) * r * 0.55,
        vx: Math.cos(a) * spd - Math.sin(a) * 52,
        vy: Math.sin(a) * spd + Math.cos(a) * 52 - 30,
        ax: 0,
        ay: -18,
        drag: 1.5,
        size: rand(2.4, 7.2),
        rotation: rand(0, Math.PI * 2),
        vRot: rand(-2.8, 2.8),
        shape: i % 4 === 0 ? 'star4' : i % 4 === 1 ? 'diamond' : 'dot',
        color: pick(palette.swatches),
        secondary: palette.pearl,
        age: 0,
        life: rand(1.4, 2.45),
        delay: 0.28 + rand(0, 0.58),
        twinkleSpeed: rand(5, 10),
        twinklePhase: rand(0, Math.PI * 2),
        swayAmp: rand(12, 28),
        swayFreq: rand(1.4, 2.6),
        swayPhase: rand(0, Math.PI * 2),
        glow: 1,
      })
    }

    addMilestoneCrest()
  }

  // --- Scene 2: 流光彩缎 (Aurora Ribbons) ---
  function setupAuroraRibbons() {
    addOriginPulse()

    const totalRibbons = Math.round(36 * density)
    const launchers = [
      { x: width * 0.03, y: height * 0.92, angleMin: -1.16, angleMax: -0.42, power: 1.04 },
      { x: width * 0.97, y: height * 0.92, angleMin: -Math.PI + 0.42, angleMax: -Math.PI + 1.16, power: 1.04 },
      { x: ox, y: oy, angleMin: -Math.PI * 0.88, angleMax: -Math.PI * 0.12, power: 0.78 },
    ]

    const baseSpeed = Math.max(width, height) * (isCompact ? 1.02 : 0.94)
    for (let i = 0; i < totalRibbons; i++) {
      const launcher = i < totalRibbons * 0.4 ? launchers[0]! : i < totalRibbons * 0.8 ? launchers[1]! : launchers[2]!
      const angle = rand(launcher.angleMin, launcher.angleMax)
      const speed = baseSpeed * launcher.power * rand(0.72, 1.18)
      const front = i % 5 === 0 ? palette.gold : pick(palette.swatches)
      const back = mixRgb(front, palette.isDark ? palette.pearl : palette.accentDeep, palette.isDark ? 0.54 : 0.34)

      ribbons.push({
        x: launcher.x + rand(-18, 18),
        y: launcher.y + rand(-12, 12),
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        gravity: rand(240, 390),
        drag: rand(1.08, 1.55),
        width: rand(isCompact ? 7.5 : 9.5, isCompact ? 13 : 17),
        colorFront: front,
        colorBack: back,
        twistPhase: rand(0, Math.PI * 2),
        twistSpeed: rand(4.8, 9.4),
        flutterAmp: rand(34, 82),
        flutterFreq: rand(2.6, 5.1),
        flutterPhase: rand(0, Math.PI * 2),
        age: 0,
        life: rand(2.2, 3.0),
        delay: rand(0, 0.22),
        maxPoints: isCompact ? 14 : 18,
        points: [],
        shedCooldown: rand(0.06, 0.2),
      })
    }

    // Accent sweeping light rings from lower corners
    rings.push(
      {
        x: width * 0.05,
        y: height * 0.92,
        r0: 18,
        r1: Math.min(width, height) * 0.44,
        color: palette.accent,
        lineWidth: 2,
        age: 0,
        life: 0.95,
        delay: 0.02,
      },
      {
        x: width * 0.95,
        y: height * 0.92,
        r0: 18,
        r1: Math.min(width, height) * 0.44,
        color: palette.accent2,
        lineWidth: 2,
        age: 0,
        life: 0.95,
        delay: 0.08,
      },
    )

    addMilestoneCrest()
  }

  // --- Scene 3: 棱镜星瀑 (Starfall Prism) ---
  function setupStarfallPrism() {
    addOriginPulse()

    caustics.push(
      {
        y: height * 0.16,
        height: height * 0.42,
        colorA: palette.accent,
        colorB: palette.accent2,
        colorC: options.milestone ? palette.gold : palette.accentLight,
        age: 0,
        life: 1.55,
        delay: 0,
      },
      {
        y: height * 0.42,
        height: height * 0.36,
        colorA: palette.accent2,
        colorB: palette.gold,
        colorC: palette.accent,
        age: 0,
        life: 1.4,
        delay: 0.16,
      },
    )

    // Three depth layers: far, mid, near — immediate curtain across upper/mid viewport + trailing cascade
    const layers = [
      { count: Math.round(38 * density), size: [3.2, 5.4] as const, vy: [130, 225] as const, vx: [24, 62] as const, glow: 0.8 },
      { count: Math.round(48 * density), size: [5.6, 9.6] as const, vy: [210, 340] as const, vx: [42, 98] as const, glow: 1.05 },
      { count: Math.round(24 * density), size: [9.4, 15.2] as const, vy: [290, 450] as const, vx: [62, 132] as const, glow: 1.3 },
    ]

    layers.forEach((layer, layerIdx) => {
      for (let i = 0; i < layer.count; i++) {
        const earlyWave = i < layer.count * 0.52
        const startX = rand(-width * 0.08, width * 1.02)
        const startY = earlyWave ? rand(height * 0.02, height * 0.48) : rand(-height * 0.12, height * 0.18)
        const shapes: SparkEntity['shape'][] =
          layerIdx === 2 ? ['star4', 'shard'] : layerIdx === 1 ? ['star4', 'crescent', 'shard', 'diamond'] : ['star4', 'diamond']
        sparks.push({
          x: startX,
          y: startY,
          vx: rand(layer.vx[0], layer.vx[1]),
          vy: rand(layer.vy[0], layer.vy[1]),
          ax: 0,
          ay: 56,
          drag: 0.42,
          size: rand(layer.size[0], layer.size[1]),
          rotation: rand(0, Math.PI * 2),
          vRot: rand(-2.8, 2.8),
          shape: pick(shapes),
          color: i % 5 === 0 ? palette.gold : pick(palette.swatches),
          secondary: palette.isDark ? palette.pearl : palette.accentDeep,
          age: 0,
          life: rand(1.65, 2.55),
          delay: earlyWave ? rand(0, 0.16) : rand(0.18, 0.56),
          twinkleSpeed: rand(6, 12),
          twinklePhase: rand(0, Math.PI * 2),
          swayAmp: rand(20, 46),
          swayFreq: rand(1.5, 2.9),
          swayPhase: rand(0, Math.PI * 2),
          glow: layer.glow,
        })
      }
    })

    // Radial prism flare from center optical stage
    rings.push({
      x: cx,
      y: cy,
      r0: 28,
      r1: Math.min(width, height) * 0.42,
      color: palette.accent2,
      lineWidth: 1.6,
      age: 0,
      life: 1.05,
      delay: 0.08,
      dashed: true,
    })

    addMilestoneCrest()
  }

  // --- Scene 4: 浮光萤火 (Lantern Fireflies) ---
  function setupLanternFireflies() {
    addOriginPulse()

    const count = Math.round(56 * density)
    for (let i = 0; i < count; i++) {
      const fromButton = i < Math.round(12 * density)
      const midWave = !fromButton && i < Math.round(28 * density)
      const x = fromButton ? ox + rand(-48, 48) : rand(width * 0.05, width * 0.95)
      const y = fromButton
        ? oy + rand(-18, 18)
        : midWave
          ? rand(height * 0.48, height * 0.86)
          : rand(height * 0.78, height * 1.02)
      const isHero = i % 5 === 0
      fireflies.push({
        x,
        y,
        vx: rand(-32, 32),
        vy: -rand(isCompact ? 185 : 230, isCompact ? 340 : 430),
        radius: isHero ? rand(8.5, 13.5) : rand(3.6, 7.2),
        color: isHero ? (i % 10 === 0 || options.milestone ? palette.gold : palette.accent) : pick(palette.swatches),
        age: 0,
        life: rand(2.0, 2.9),
        delay: fromButton ? rand(0, 0.14) : midWave ? rand(0, 0.22) : rand(0.14, 0.48),
        driftFreq: rand(1.8, 3.5),
        driftAmp: rand(38, 92),
        driftPhase: rand(0, Math.PI * 2),
        pulseSpeed: rand(4.8, 8.8),
        bloomAt: isHero ? rand(0.24, 0.46) : undefined,
        history: [],
      })
    }

    addMilestoneCrest()
  }

  // --- Scene 5: 礼赞星焰 (Celestial Fireworks) ---
  function setupCelestialFireworks() {
    addOriginPulse()

    const bursts: Array<{ x: number; y: number; delay: number; color: RGB; scale: number }> = [
      { x: width * 0.22, y: height * 0.26, delay: 0, color: palette.accent, scale: 1.08 },
      { x: width * 0.78, y: height * 0.24, delay: 0.1, color: palette.accent2, scale: 1.08 },
      { x: width * 0.33, y: height * 0.18, delay: 0.24, color: options.milestone ? palette.gold : palette.success, scale: 0.96 },
      { x: width * 0.67, y: height * 0.19, delay: 0.36, color: palette.gold, scale: 1.0 },
    ]
    if (options.milestone) {
      bursts.push({ x: width * 0.5, y: height * 0.16, delay: 0.48, color: palette.champagne, scale: 1.22 })
    }

    for (const b of bursts) {
      const startX = b.x + rand(-width * 0.08, width * 0.08)
      const startY = height * 0.98
      comets.push({
        x0: startX,
        y0: startY,
        x1: b.x,
        y1: b.y,
        cx: (startX + b.x) * 0.5 + rand(-36, 36),
        cy: (startY + b.y) * 0.45,
        color: b.color,
        age: 0,
        life: 0.32,
        delay: b.delay,
        history: [],
        onArrive: (ax, ay) => spawnWillowBurst(ax, ay, b.color, b.scale),
      })
    }

    addMilestoneCrest()
  }

  function spawnWillowBurst(bx: number, by: number, primary: RGB, scale: number) {
    rings.push({
      x: bx,
      y: by,
      r0: 6,
      r1: (isCompact ? 76 : 112) * scale,
      color: primary,
      lineWidth: 2,
      age: 0,
      life: 0.65,
      delay: 0,
      glow: true,
    })

    const count = Math.round(32 * density * scale)
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + rand(-0.08, 0.08)
      const tier = i % 3 === 0 ? 1 : i % 3 === 1 ? 0.76 : 0.52
      const speed = (isCompact ? 205 : 295) * scale * tier * rand(0.84, 1.14)
      const color = i % 4 === 0 ? palette.gold : i % 3 === 0 ? palette.accentLight : primary
      trails.push({
        x: bx,
        y: by,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 22,
        gravity: rand(145, 225),
        drag: rand(1.45, 2.05),
        color,
        core: palette.pearl,
        width: rand(1.8, 3.1),
        age: 0,
        life: rand(1.15, 1.85),
        delay: 0,
        history: [{ x: bx, y: by }],
        maxHistory: isCompact ? 6 : 8,
        crackle: i % 5 === 0,
      })
    }
  }

  // Initialize selected choreography
  switch (options.scene) {
    case 'chronos-bloom':
      setupChronosBloom()
      break
    case 'aurora-ribbons':
      setupAuroraRibbons()
      break
    case 'starfall-prism':
      setupStarfallPrism()
      break
    case 'lantern-fireflies':
      setupLanternFireflies()
      break
    case 'celestial-fireworks':
      setupCelestialFireworks()
      break
  }

  // --- Animation Loop ---
  let rafId = 0
  let destroyed = false
  let fadingOut = false
  let masterAlpha = 1
  let elapsed = 0
  let lastTs = performance.now()
  const maxDuration = options.milestone ? 4.0 : 3.65

  function renderFrame(now: number) {
    if (destroyed) return
    const dt = Math.min((now - lastTs) / 1000, 0.05)
    lastTs = now
    elapsed += dt

    if (fadingOut) {
      masterAlpha = Math.max(0, masterAlpha - dt / 0.26)
      if (masterAlpha <= 0.005) {
        finish()
        return
      }
    }

    ctx!.clearRect(0, 0, width, height)
    ctx!.save()
    ctx!.globalAlpha = masterAlpha

    let alive = 0

    // 1. Caustic prism wash
    for (let i = caustics.length - 1; i >= 0; i--) {
      const c = caustics[i]!
      c.age += dt
      const local = c.age - c.delay
      if (local < 0) {
        alive++
        continue
      }
      const p = local / c.life
      if (p >= 1) {
        caustics.splice(i, 1)
        continue
      }
      alive++
      const sweepX = width * (-0.2 + 1.4 * easeOutCubic(p))
      const alpha = Math.sin(p * Math.PI) * (palette.isDark ? 0.24 : 0.16)
      const grad = ctx!.createRadialGradient(sweepX, c.y, 12, sweepX, c.y, width * 0.42)
      grad.addColorStop(0, rgba(c.colorC, alpha * 1.1))
      grad.addColorStop(0.45, rgba(c.colorA, alpha * 0.75))
      grad.addColorStop(0.8, rgba(c.colorB, alpha * 0.35))
      grad.addColorStop(1, rgba(c.colorB, 0))
      ctx!.save()
      if (palette.isDark) ctx!.globalCompositeOperation = 'lighter'
      ctx!.fillStyle = grad
      ctx!.fillRect(0, 0, width, c.y + c.height * 1.8)
      ctx!.restore()
    }

    // 2. Timepiece Dial (Chronos Bloom)
    for (let i = dials.length - 1; i >= 0; i--) {
      const d = dials[i]!
      d.age += dt
      const local = d.age - d.delay
      if (local < 0) {
        alive++
        continue
      }
      const p = local / d.life
      if (p >= 1) {
        dials.splice(i, 1)
        continue
      }
      alive++

      const sweepProgress = easeOutQuart(clamp01(local / 0.82))
      const fadeOut = p > 0.62 ? 1 - easeInOutSine((p - 0.62) / 0.38) : 1
      const scale = 0.86 + 0.24 * easeOutCubic(clamp01(local / 1.45))
      const r = d.radius * scale
      const startAngle = -Math.PI / 2
      const endAngle = startAngle + Math.PI * 2 * sweepProgress

      // Emit subtle radial sparks as sweep passes each of 12 ticks
      const ticksPassed = Math.floor(sweepProgress * 12)
      for (let tIdx = 0; tIdx < ticksPassed; tIdx++) {
        if (!d.ticksEmitted.has(tIdx)) {
          d.ticksEmitted.add(tIdx)
          const ta = startAngle + (tIdx / 12) * Math.PI * 2
          const tx = d.cx + Math.cos(ta) * r
          const ty = d.cy + Math.sin(ta) * r
          for (let k = 0; k < 3; k++) {
            const spreadA = ta + rand(-0.35, 0.35)
            const spd = rand(52, 138)
            sparks.push({
              x: tx,
              y: ty,
              vx: Math.cos(spreadA) * spd,
              vy: Math.sin(spreadA) * spd,
              ax: 0,
              ay: -14,
              drag: 1.8,
              size: rand(2.6, 5.2),
              rotation: rand(0, Math.PI * 2),
              vRot: rand(-3, 3),
              shape: k === 0 ? 'star4' : 'diamond',
              color: tIdx % 3 === 0 ? d.gold : d.accent2,
              secondary: palette.pearl,
              age: 0,
              life: rand(0.95, 1.55),
              delay: 0,
              twinkleSpeed: rand(6, 11),
              twinklePhase: rand(0, Math.PI * 2),
              swayAmp: rand(6, 14),
              swayFreq: rand(1.6, 2.8),
              swayPhase: rand(0, Math.PI * 2),
              glow: 1,
            })
          }
        }
      }

      ctx!.save()
      if (palette.isDark) ctx!.globalCompositeOperation = 'lighter'

      // Soft outer halo band
      ctx!.beginPath()
      ctx!.arc(d.cx, d.cy, r, startAngle, endAngle)
      ctx!.strokeStyle = rgba(d.color, 0.22 * fadeOut)
      ctx!.lineWidth = 10
      ctx!.lineCap = 'round'
      ctx!.stroke()

      // Primary crisp luminous arc
      const arcGrad = ctx!.createLinearGradient(d.cx - r, d.cy - r, d.cx + r, d.cy + r)
      arcGrad.addColorStop(0, rgba(d.color, 0.85 * fadeOut))
      arcGrad.addColorStop(0.55, rgba(d.accent2, 0.9 * fadeOut))
      arcGrad.addColorStop(1, rgba(d.gold, 0.92 * fadeOut))
      ctx!.beginPath()
      ctx!.arc(d.cx, d.cy, r, startAngle, endAngle)
      ctx!.strokeStyle = arcGrad
      ctx!.lineWidth = 2.4
      ctx!.stroke()

      // 12 precision timepiece ticks
      for (let tIdx = 0; tIdx < 12; tIdx++) {
        const tickRatio = tIdx / 12
        if (sweepProgress < tickRatio) continue
        const tickAlpha = clamp01((sweepProgress - tickRatio) * 6) * fadeOut
        const ta = startAngle + tickRatio * Math.PI * 2
        const major = tIdx % 3 === 0
        const inner = r - (major ? 14 : 8)
        const outer = r + (major ? 8 : 4)
        ctx!.beginPath()
        ctx!.moveTo(d.cx + Math.cos(ta) * inner, d.cy + Math.sin(ta) * inner)
        ctx!.lineTo(d.cx + Math.cos(ta) * outer, d.cy + Math.sin(ta) * outer)
        ctx!.strokeStyle = rgba(major ? d.gold : d.accent2, (major ? 0.85 : 0.55) * tickAlpha)
        ctx!.lineWidth = major ? 2.2 : 1.3
        ctx!.stroke()
      }

      // Leading specular comet head while sweeping
      if (sweepProgress < 0.995) {
        const hx = d.cx + Math.cos(endAngle) * r
        const hy = d.cy + Math.sin(endAngle) * r
        const headGrad = ctx!.createRadialGradient(hx, hy, 1, hx, hy, 18)
        headGrad.addColorStop(0, rgba(palette.pearl, 0.95 * fadeOut))
        headGrad.addColorStop(0.4, rgba(d.accent2, 0.65 * fadeOut))
        headGrad.addColorStop(1, rgba(d.color, 0))
        ctx!.fillStyle = headGrad
        ctx!.beginPath()
        ctx!.arc(hx, hy, 18, 0, Math.PI * 2)
        ctx!.fill()
      }

      ctx!.restore()
    }

    // 3. Expanding Rings
    for (let i = rings.length - 1; i >= 0; i--) {
      const ring = rings[i]!
      ring.age += dt
      const local = ring.age - ring.delay
      if (local < 0) {
        alive++
        continue
      }
      const p = local / ring.life
      if (p >= 1) {
        rings.splice(i, 1)
        continue
      }
      alive++
      const radius = ring.r0 + (ring.r1 - ring.r0) * easeOutQuart(p)
      const alpha = (1 - p) * (1 - p) * (palette.isDark ? 0.72 : 0.56)

      ctx!.save()
      if (ring.glow && palette.isDark) ctx!.globalCompositeOperation = 'lighter'
      if (ring.dashed) ctx!.setLineDash([4, 9])
      ctx!.beginPath()
      ctx!.arc(ring.x, ring.y, radius, 0, Math.PI * 2)
      ctx!.strokeStyle = rgba(ring.color, alpha)
      ctx!.lineWidth = Math.max(0.6, ring.lineWidth * (1 - p * 0.55))
      ctx!.stroke()
      ctx!.restore()
    }

    // 4. Ascending / Arcing Comets
    for (let i = comets.length - 1; i >= 0; i--) {
      const c = comets[i]!
      c.age += dt
      const local = c.age - c.delay
      if (local < 0) {
        alive++
        continue
      }
      const p = clamp01(local / c.life)
      const e = easeOutCubic(p)
      const inv = 1 - e
      const x = inv * inv * c.x0 + 2 * inv * e * c.cx + e * e * c.x1
      const y = inv * inv * c.y0 + 2 * inv * e * c.cy + e * e * c.y1
      c.history.push({ x, y })
      if (c.history.length > 10) c.history.shift()

      if (p >= 1) {
        if (!c.arrived) {
          c.arrived = true
          c.onArrive?.(c.x1, c.y1)
        }
        comets.splice(i, 1)
        continue
      }
      alive++

      ctx!.save()
      if (palette.isDark) ctx!.globalCompositeOperation = 'lighter'
      for (let h = 1; h < c.history.length; h++) {
        const prev = c.history[h - 1]!
        const curr = c.history[h]!
        const frac = h / c.history.length
        ctx!.beginPath()
        ctx!.moveTo(prev.x, prev.y)
        ctx!.lineTo(curr.x, curr.y)
        ctx!.strokeStyle = rgba(c.color, frac * 0.78)
        ctx!.lineWidth = 1.1 + frac * 2.2
        ctx!.lineCap = 'round'
        ctx!.stroke()
      }
      const glow = ctx!.createRadialGradient(x, y, 0.5, x, y, 10)
      glow.addColorStop(0, rgba(palette.pearl, 0.95))
      glow.addColorStop(0.45, rgba(c.color, 0.7))
      glow.addColorStop(1, rgba(c.color, 0))
      ctx!.fillStyle = glow
      ctx!.beginPath()
      ctx!.arc(x, y, 10, 0, Math.PI * 2)
      ctx!.fill()
      ctx!.restore()
    }

    // 5. 3D-Twisting Silk Ribbons (Aurora Ribbons)
    for (let i = ribbons.length - 1; i >= 0; i--) {
      const rb = ribbons[i]!
      rb.age += dt
      const local = rb.age - rb.delay
      if (local < 0) {
        alive++
        continue
      }
      const p = local / rb.life
      if (p >= 1) {
        ribbons.splice(i, 1)
        continue
      }
      alive++

      const damp = Math.exp(-rb.drag * dt)
      rb.vx *= damp
      rb.vy = rb.vy * damp + rb.gravity * dt
      const flutter = Math.sin(local * rb.flutterFreq + rb.flutterPhase) * rb.flutterAmp
      rb.x += (rb.vx + flutter) * dt
      rb.y += rb.vy * dt
      rb.twistPhase += rb.twistSpeed * dt

      rb.points.push({ x: rb.x, y: rb.y })
      if (rb.points.length > rb.maxPoints) rb.points.shift()

      // Shed occasional subtle glitter along crests
      rb.shedCooldown -= dt
      if (rb.shedCooldown <= 0 && p < 0.7) {
        rb.shedCooldown = rand(0.14, 0.28)
        sparks.push({
          x: rb.x,
          y: rb.y,
          vx: rb.vx * 0.14 + rand(-24, 24),
          vy: rb.vy * 0.14 + rand(-18, 22),
          ax: 0,
          ay: 36,
          drag: 1.8,
          size: rand(2.2, 4.2),
          rotation: rand(0, Math.PI * 2),
          vRot: rand(-4, 4),
          shape: 'star4',
          color: rb.colorFront,
          secondary: palette.pearl,
          age: 0,
          life: rand(0.55, 0.95),
          delay: 0,
          twinkleSpeed: rand(8, 13),
          twinklePhase: rand(0, Math.PI * 2),
          swayAmp: 6,
          swayFreq: 2,
          swayPhase: rand(0, Math.PI * 2),
          glow: 0.9,
        })
      }

      if (rb.points.length < 3) continue
      const fade = p > 0.65 ? 1 - easeInOutSine((p - 0.65) / 0.35) : clamp01(p * 6)
      const len = rb.points.length

      for (let s = 1; s < len; s++) {
        const p0 = rb.points[s - 1]!
        const p1 = rb.points[s]!
        const frac = s / (len - 1)
        const dx = p1.x - p0.x
        const dy = p1.y - p0.y
        const dist = Math.hypot(dx, dy) || 1
        const nx = -dy / dist
        const ny = dx / dist

        const twist0 = Math.cos(rb.twistPhase - (len - s) * 0.34)
        const twist1 = Math.cos(rb.twistPhase - (len - 1 - s) * 0.34)
        const taper0 = Math.sin(((s - 1) / (len - 1)) * Math.PI)
        const taper1 = Math.sin(frac * Math.PI)
        const w0 = rb.width * 0.5 * (0.22 + 0.78 * Math.abs(twist0)) * (0.25 + 0.75 * taper0)
        const w1 = rb.width * 0.5 * (0.22 + 0.78 * Math.abs(twist1)) * (0.25 + 0.75 * taper1)

        const facingFront = twist1 >= 0
        const col = facingFront ? rb.colorFront : rb.colorBack
        const segAlpha = fade * (0.35 + 0.65 * taper1) * (facingFront ? 0.92 : 0.72)

        ctx!.beginPath()
        ctx!.moveTo(p0.x + nx * w0, p0.y + ny * w0)
        ctx!.lineTo(p1.x + nx * w1, p1.y + ny * w1)
        ctx!.lineTo(p1.x - nx * w1, p1.y - ny * w1)
        ctx!.lineTo(p0.x - nx * w0, p0.y - ny * w0)
        ctx!.closePath()
        ctx!.fillStyle = rgba(col, segAlpha)
        ctx!.fill()
      }
    }

    // 6. Willow Trail Sparks (Celestial Fireworks)
    for (let i = trails.length - 1; i >= 0; i--) {
      const tr = trails[i]!
      tr.age += dt
      const local = tr.age - tr.delay
      if (local < 0) {
        alive++
        continue
      }
      const p = local / tr.life
      if (p >= 1) {
        trails.splice(i, 1)
        continue
      }
      alive++

      const damp = Math.exp(-tr.drag * dt)
      tr.vx *= damp
      tr.vy = tr.vy * damp + tr.gravity * dt
      tr.x += tr.vx * dt
      tr.y += tr.vy * dt
      tr.history.push({ x: tr.x, y: tr.y })
      if (tr.history.length > tr.maxHistory) tr.history.shift()

      if (tr.crackle && !tr.crackled && p > 0.62) {
        tr.crackled = true
        sparks.push({
          x: tr.x,
          y: tr.y,
          vx: rand(-35, 35),
          vy: rand(-35, 35),
          ax: 0,
          ay: 45,
          drag: 2.4,
          size: rand(3.2, 5.2),
          rotation: rand(0, Math.PI * 2),
          vRot: rand(-4, 4),
          shape: 'star4',
          color: palette.champagne,
          secondary: palette.pearl,
          age: 0,
          life: rand(0.35, 0.55),
          delay: 0,
          twinkleSpeed: 14,
          twinklePhase: rand(0, Math.PI * 2),
          swayAmp: 0,
          swayFreq: 0,
          swayPhase: 0,
          glow: 1.2,
        })
      }

      const alpha = (1 - easeInOutSine(Math.max(0, (p - 0.35) / 0.65))) * (0.78 + 0.22 * Math.sin(local * 26))
      ctx!.save()
      if (palette.isDark) ctx!.globalCompositeOperation = 'lighter'
      for (let h = 1; h < tr.history.length; h++) {
        const a = tr.history[h - 1]!
        const b = tr.history[h]!
        const frac = h / tr.history.length
        ctx!.beginPath()
        ctx!.moveTo(a.x, a.y)
        ctx!.lineTo(b.x, b.y)
        ctx!.strokeStyle = rgba(tr.color, alpha * frac * (palette.isDark ? 0.92 : 0.85))
        ctx!.lineWidth = Math.max(0.7, tr.width * frac * (1 - p * 0.35))
        ctx!.lineCap = 'round'
        ctx!.stroke()
      }
      ctx!.fillStyle = rgba(tr.core, alpha * 0.92)
      ctx!.beginPath()
      ctx!.arc(tr.x, tr.y, Math.max(1, tr.width * 0.55), 0, Math.PI * 2)
      ctx!.fill()
      ctx!.restore()
    }

    // 7. Lantern Fireflies
    for (let i = fireflies.length - 1; i >= 0; i--) {
      const f = fireflies[i]!
      f.age += dt
      const local = f.age - f.delay
      if (local < 0) {
        alive++
        continue
      }
      const p = local / f.life
      if (p >= 1) {
        fireflies.splice(i, 1)
        continue
      }
      alive++

      const sway = Math.sin(local * f.driftFreq + f.driftPhase) * f.driftAmp
      f.vy *= Math.exp(-0.52 * dt)
      f.x += (f.vx + sway) * dt
      f.y += f.vy * dt
      f.history.push({ x: f.x, y: f.y })
      if (f.history.length > 9) f.history.shift()

      if (f.bloomAt && !f.bloomed && p >= f.bloomAt) {
        f.bloomed = true
        rings.push({
          x: f.x,
          y: f.y,
          r0: f.radius,
          r1: f.radius * 5.6,
          color: f.color,
          lineWidth: 1.5,
          age: 0,
          life: 0.78,
          delay: 0,
          glow: true,
        })
        for (let k = 0; k < 6; k++) {
          const a = (Math.PI * 2 * k) / 6 + rand(-0.25, 0.25)
          const spd = rand(40, 105)
          sparks.push({
            x: f.x,
            y: f.y,
            vx: Math.cos(a) * spd,
            vy: Math.sin(a) * spd - 20,
            ax: 0,
            ay: -12,
            drag: 1.9,
            size: rand(2.5, 4.8),
            rotation: rand(0, Math.PI * 2),
            vRot: rand(-3, 3),
            shape: 'star4',
            color: f.color,
            secondary: palette.pearl,
            age: 0,
            life: rand(0.75, 1.25),
            delay: 0,
            twinkleSpeed: rand(7, 12),
            twinklePhase: rand(0, Math.PI * 2),
            swayAmp: 10,
            swayFreq: 2.2,
            swayPhase: rand(0, Math.PI * 2),
            glow: 1,
          })
        }
      }

      const env = clamp01(p * 4.5) * (p > 0.62 ? 1 - easeInOutSine((p - 0.62) / 0.38) : 1)
      const pulse = 0.72 + 0.28 * Math.sin(local * f.pulseSpeed + f.driftPhase)
      const alpha = env * pulse

      ctx!.save()
      if (palette.isDark) ctx!.globalCompositeOperation = 'lighter'

      // Soft curved filament tail
      if (f.history.length > 2) {
        for (let h = 1; h < f.history.length; h++) {
          const a = f.history[h - 1]!
          const b = f.history[h]!
          const frac = h / f.history.length
          ctx!.beginPath()
          ctx!.moveTo(a.x, a.y)
          ctx!.lineTo(b.x, b.y)
          ctx!.strokeStyle = rgba(f.color, alpha * frac * (palette.isDark ? 0.52 : 0.62))
          ctx!.lineWidth = Math.max(1.0, f.radius * 0.42 * frac)
          ctx!.lineCap = 'round'
          ctx!.stroke()
        }
      }

      // Luminous orb halo
      const haloR = f.radius * 3.1
      const grad = ctx!.createRadialGradient(f.x, f.y, 0.5, f.x, f.y, haloR)
      grad.addColorStop(0, rgba(palette.pearl, alpha * 0.96))
      grad.addColorStop(0.28, rgba(f.color, alpha * (palette.isDark ? 0.8 : 0.82)))
      grad.addColorStop(0.7, rgba(f.color, alpha * (palette.isDark ? 0.2 : 0.24)))
      grad.addColorStop(1, rgba(f.color, 0))
      ctx!.fillStyle = grad
      ctx!.beginPath()
      ctx!.arc(f.x, f.y, haloR, 0, Math.PI * 2)
      ctx!.fill()

      // Crisp glass-lantern rim in light mode so orbs remain sculptural on light canvas
      if (!palette.isDark && f.radius >= 5) {
        ctx!.beginPath()
        ctx!.arc(f.x, f.y, f.radius * 0.92, 0, Math.PI * 2)
        ctx!.strokeStyle = rgba(f.color, alpha * 0.55)
        ctx!.lineWidth = 1.15
        ctx!.stroke()
      }
      ctx!.restore()
    }

    // 8. Vector Sparks / Glints / Glass Shards
    for (let i = sparks.length - 1; i >= 0; i--) {
      const sp = sparks[i]!
      sp.age += dt
      const local = sp.age - sp.delay
      if (local < 0) {
        alive++
        continue
      }
      const p = local / sp.life
      if (p >= 1) {
        sparks.splice(i, 1)
        continue
      }
      alive++

      const damp = Math.exp(-sp.drag * dt)
      sp.vx = sp.vx * damp + sp.ax * dt
      sp.vy = sp.vy * damp + sp.ay * dt
      const swayX = sp.swayAmp ? Math.sin(local * sp.swayFreq + sp.swayPhase) * sp.swayAmp : 0
      sp.x += (sp.vx + swayX) * dt
      sp.y += sp.vy * dt
      sp.rotation += sp.vRot * dt

      const fade = clamp01(p * 7) * (p > 0.58 ? 1 - easeInOutSine((p - 0.58) / 0.42) : 1)
      const twinkle = 0.66 + 0.34 * Math.sin(local * sp.twinkleSpeed + sp.twinklePhase)
      const alpha = fade * twinkle
      const s = sp.size * (0.75 + 0.25 * twinkle)

      ctx!.save()
      ctx!.translate(sp.x, sp.y)
      if (palette.isDark && sp.glow > 0.8) ctx!.globalCompositeOperation = 'lighter'

      // Soft halo for larger glints
      if (s >= 4.2 && sp.glow > 0.8) {
        const halo = ctx!.createRadialGradient(0, 0, 0.5, 0, 0, s * 2.2)
        halo.addColorStop(0, rgba(sp.color, alpha * (palette.isDark ? 0.42 : 0.24)))
        halo.addColorStop(1, rgba(sp.color, 0))
        ctx!.fillStyle = halo
        ctx!.beginPath()
        ctx!.arc(0, 0, s * 2.2, 0, Math.PI * 2)
        ctx!.fill()
      }

      ctx!.rotate(sp.rotation)
      if (sp.shape === 'dot') {
        ctx!.beginPath()
        ctx!.arc(0, 0, s * 0.55, 0, Math.PI * 2)
        ctx!.fillStyle = rgba(sp.color, alpha * 0.92)
        ctx!.fill()
      } else if (sp.shape === 'star4') {
        drawFourPointStar(ctx!, s)
        ctx!.fillStyle = rgba(sp.color, alpha * 0.95)
        ctx!.fill()
        // Specular center dot
        drawFourPointStar(ctx!, s * 0.48)
        ctx!.fillStyle = rgba(sp.secondary, alpha * 0.88)
        ctx!.fill()
      } else if (sp.shape === 'diamond') {
        drawDiamond(ctx!, s * 0.85)
        ctx!.fillStyle = rgba(sp.color, alpha * 0.9)
        ctx!.fill()
      } else if (sp.shape === 'crescent') {
        drawCrescent(ctx!, s * 0.85)
        ctx!.fillStyle = rgba(sp.color, alpha * 0.88)
        ctx!.fill()
      } else {
        drawPrismShard(ctx!, s * 0.92)
        ctx!.fillStyle = rgba(sp.color, alpha * (palette.isDark ? 0.74 : 0.8))
        ctx!.fill()
        ctx!.strokeStyle = rgba(sp.secondary, alpha * (palette.isDark ? 0.86 : 0.42))
        ctx!.lineWidth = 1.05
        ctx!.stroke()
      }

      ctx!.restore()
    }

    ctx!.restore()

    if (alive === 0 || elapsed >= maxDuration) {
      finish()
      return
    }
    rafId = window.requestAnimationFrame(renderFrame)
  }

  function finish() {
    if (destroyed) return
    destroy()
    options.onComplete?.()
  }

  function fadeOut() {
    fadingOut = true
  }

  function destroy() {
    if (destroyed) return
    destroyed = true
    window.cancelAnimationFrame(rafId)
    window.removeEventListener('resize', syncSize)
    ctx?.clearRect(0, 0, width, height)
  }

  rafId = window.requestAnimationFrame(renderFrame)
  return { fadeOut, destroy }
}
