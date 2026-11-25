import { reactive } from 'vue'

export type SoundPreset = 'off' | 'rain' | 'brown' | 'wind' | 'cafe'

export const SOUND_OPTIONS: ReadonlyArray<{ id: SoundPreset; label: string; desc: string }> = [
  { id: 'off', label: '静音', desc: '纯净无声' },
  { id: 'rain', label: '细雨', desc: '窗畔柔雨' },
  { id: 'brown', label: '深棕噪', desc: '温润低频' },
  { id: 'wind', label: '林风', desc: '松林微风' },
  { id: 'cafe', label: '书咖', desc: '柔和暖噪' },
]

export const soundState = reactive<{
  preset: SoundPreset
  volume: number
  chimeEnabled: boolean
}>({
  preset: 'off',
  volume: 0.38,
  chimeEnabled: true,
})

let ctx: AudioContext | null = null
let masterGain: GainNode | null = null
let activeNodes: AudioNode[] = []

function ensureContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!AudioCtx) return null
  if (!ctx) {
    ctx = new AudioCtx()
    masterGain = ctx.createGain()
    masterGain.gain.value = soundState.volume
    masterGain.connect(ctx.destination)
  }
  if (ctx.state === 'suspended') {
    void ctx.resume()
  }
  return ctx
}

function createNoiseBuffer(audioCtx: AudioContext, type: 'pink' | 'brown' | 'white', seconds = 4): AudioBuffer {
  const length = audioCtx.sampleRate * seconds
  const buffer = audioCtx.createBuffer(2, length, audioCtx.sampleRate)
  for (let channel = 0; channel < 2; channel++) {
    const out = buffer.getChannelData(channel)
    if (type === 'white') {
      for (let i = 0; i < length; i++) out[i] = Math.random() * 2 - 1
    } else if (type === 'brown') {
      let last = 0
      for (let i = 0; i < length; i++) {
        const white = Math.random() * 2 - 1
        last = (last + 0.02 * white) / 1.02
        out[i] = last * 3.2
      }
    } else {
      let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0
      for (let i = 0; i < length; i++) {
        const white = Math.random() * 2 - 1
        b0 = 0.99886 * b0 + white * 0.0555179
        b1 = 0.99332 * b1 + white * 0.0750759
        b2 = 0.96900 * b2 + white * 0.1538520
        b3 = 0.86650 * b3 + white * 0.3104856
        b4 = 0.55000 * b4 + white * 0.5329522
        b5 = -0.7616 * b5 - white * 0.0168980
        out[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.09
        b6 = white * 0.115926
      }
    }
  }
  return buffer
}

function stopCurrent() {
  for (const node of activeNodes) {
    try {
      if ('stop' in node && typeof (node as AudioScheduledSourceNode).stop === 'function') {
        ;(node as AudioScheduledSourceNode).stop()
      }
      node.disconnect()
    } catch {
      /* ignore */
    }
  }
  activeNodes = []
}

export function setSoundPreset(preset: SoundPreset) {
  soundState.preset = preset
  stopCurrent()
  if (preset === 'off') return
  const audioCtx = ensureContext()
  if (!audioCtx || !masterGain) return

  const now = audioCtx.currentTime
  const env = audioCtx.createGain()
  env.gain.setValueAtTime(0.0001, now)
  env.gain.linearRampToValueAtTime(1, now + 0.6)
  env.connect(masterGain)
  activeNodes.push(env)

  if (preset === 'rain') {
    const src = audioCtx.createBufferSource()
    src.buffer = createNoiseBuffer(audioCtx, 'pink', 5)
    src.loop = true
    const hp = audioCtx.createBiquadFilter()
    hp.type = 'highpass'
    hp.frequency.value = 320
    const lp = audioCtx.createBiquadFilter()
    lp.type = 'lowpass'
    lp.frequency.value = 2600
    const lfo = audioCtx.createOscillator()
    lfo.frequency.value = 0.14
    const lfoGain = audioCtx.createGain()
    lfoGain.gain.value = 420
    lfo.connect(lfoGain).connect(lp.frequency)
    src.connect(hp).connect(lp).connect(env)
    src.start()
    lfo.start()
    activeNodes.push(src, hp, lp, lfo, lfoGain)
  } else if (preset === 'brown') {
    const src = audioCtx.createBufferSource()
    src.buffer = createNoiseBuffer(audioCtx, 'brown', 5)
    src.loop = true
    const lp = audioCtx.createBiquadFilter()
    lp.type = 'lowpass'
    lp.frequency.value = 440
    const boost = audioCtx.createGain()
    boost.gain.value = 0.82
    src.connect(lp).connect(boost).connect(env)
    src.start()
    activeNodes.push(src, lp, boost)
  } else if (preset === 'wind') {
    const src = audioCtx.createBufferSource()
    src.buffer = createNoiseBuffer(audioCtx, 'pink', 5)
    src.loop = true
    const bp = audioCtx.createBiquadFilter()
    bp.type = 'bandpass'
    bp.frequency.value = 520
    bp.Q.value = 1.6
    const lfo = audioCtx.createOscillator()
    lfo.frequency.value = 0.09
    const lfoGain = audioCtx.createGain()
    lfoGain.gain.value = 240
    lfo.connect(lfoGain).connect(bp.frequency)
    src.connect(bp).connect(env)
    src.start()
    lfo.start()
    activeNodes.push(src, bp, lfo, lfoGain)
  } else if (preset === 'cafe') {
    const lowSrc = audioCtx.createBufferSource()
    lowSrc.buffer = createNoiseBuffer(audioCtx, 'brown', 5)
    lowSrc.loop = true
    const lowFilter = audioCtx.createBiquadFilter()
    lowFilter.type = 'lowpass'
    lowFilter.frequency.value = 280
    const lowGain = audioCtx.createGain()
    lowGain.gain.value = 0.55

    const midSrc = audioCtx.createBufferSource()
    midSrc.buffer = createNoiseBuffer(audioCtx, 'pink', 4)
    midSrc.loop = true
    const midFilter = audioCtx.createBiquadFilter()
    midFilter.type = 'bandpass'
    midFilter.frequency.value = 920
    midFilter.Q.value = 0.9
    const midGain = audioCtx.createGain()
    midGain.gain.value = 0.28

    lowSrc.connect(lowFilter).connect(lowGain).connect(env)
    midSrc.connect(midFilter).connect(midGain).connect(env)
    lowSrc.start()
    midSrc.start()
    activeNodes.push(lowSrc, lowFilter, lowGain, midSrc, midFilter, midGain)
  }
}

export function setSoundVolume(value: number) {
  soundState.volume = Math.max(0, Math.min(1, value))
  if (ctx && masterGain) {
    masterGain.gain.setTargetAtTime(soundState.volume, ctx.currentTime, 0.05)
  }
}

export function playCompletionChime() {
  if (!soundState.chimeEnabled) return
  const audioCtx = ensureContext()
  if (!audioCtx) return
  const now = audioCtx.currentTime
  const notes = [523.25, 659.25, 783.99, 1046.5]
  notes.forEach((freq, idx) => {
    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(freq, now + idx * 0.14)
    gain.gain.setValueAtTime(0.0001, now + idx * 0.14)
    gain.gain.exponentialRampToValueAtTime(0.14 / (idx * 0.4 + 1), now + idx * 0.14 + 0.04)
    gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.14 + 2.2)
    osc.connect(gain).connect(audioCtx.destination)
    osc.start(now + idx * 0.14)
    osc.stop(now + idx * 0.14 + 2.3)
  })
}

export function playCheckInChime(milestone = false) {
  if (!soundState.chimeEnabled) return
  const audioCtx = ensureContext()
  if (!audioCtx) return

  const now = audioCtx.currentTime
  const filter = audioCtx.createBiquadFilter()
  filter.type = 'lowpass'
  filter.frequency.value = milestone ? 4200 : 3400
  filter.connect(audioCtx.destination)

  const notes = milestone
    ? [523.25, 659.25, 783.99, 987.77, 1318.51]
    : [523.25, 659.25, 783.99, 1174.66]
  const step = milestone ? 0.072 : 0.068
  const tail = milestone ? 1.55 : 1.05

  notes.forEach((freq, idx) => {
    const start = now + idx * step
    const peak = (milestone ? 0.115 : 0.095) / (idx * 0.18 + 1)

    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.type = 'triangle'
    osc.frequency.setValueAtTime(freq, start)
    gain.gain.setValueAtTime(0.0001, start)
    gain.gain.exponentialRampToValueAtTime(peak, start + 0.016)
    gain.gain.exponentialRampToValueAtTime(0.0001, start + tail)
    osc.connect(gain).connect(filter)
    osc.start(start)
    osc.stop(start + tail + 0.06)

    // Delicate crystal harmonic overtone
    const shimmer = audioCtx.createOscillator()
    const shimmerGain = audioCtx.createGain()
    shimmer.type = 'sine'
    shimmer.frequency.setValueAtTime(freq * 2, start)
    shimmerGain.gain.setValueAtTime(0.0001, start)
    shimmerGain.gain.exponentialRampToValueAtTime(peak * 0.24, start + 0.012)
    shimmerGain.gain.exponentialRampToValueAtTime(0.0001, start + tail * 0.58)
    shimmer.connect(shimmerGain).connect(filter)
    shimmer.start(start)
    shimmer.stop(start + tail * 0.62)
  })

  if (milestone) {
    // Warm fifth pad shimmer for streak milestones
    ;[261.63, 392.0].forEach(freq => {
      const pad = audioCtx.createOscillator()
      const padGain = audioCtx.createGain()
      pad.type = 'sine'
      pad.frequency.setValueAtTime(freq, now)
      padGain.gain.setValueAtTime(0.0001, now)
      padGain.gain.exponentialRampToValueAtTime(0.045, now + 0.12)
      padGain.gain.exponentialRampToValueAtTime(0.0001, now + 1.85)
      pad.connect(padGain).connect(filter)
      pad.start(now)
      pad.stop(now + 1.92)
    })
  }
}
