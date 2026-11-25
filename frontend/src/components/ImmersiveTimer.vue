<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { CheckCircle2, Coffee, Link2, Minimize2, Pause, Play, Square } from 'lucide-vue-next'
import { actTimer, finishTimer, timer, timerBusy, timerProgress, timerStatus } from '../state'
import AmbientMixer from './AmbientMixer.vue'
import ProgressRing from './ui/ProgressRing.vue'

const props = defineProps<{
  displayTime: string
  taskTitle: string
  canStart: boolean
}>()

const emit = defineEmits<{ close: []; start: [] }>()

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    e.preventDefault()
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKey)
  if (document.documentElement.requestFullscreen) {
    void document.documentElement.requestFullscreen().catch(() => {})
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  if (document.fullscreenElement) {
    void document.exitFullscreen().catch(() => {})
  }
})
</script>

<template>
  <Teleport to="body">
    <div class="theater-stage" role="dialog" aria-modal="true" aria-label="沉浸专注剧场">
      <div class="theater-aura" :class="{ running: timer?.running_since !== null && !!timer }"></div>

      <header class="theater-top">
        <span class="theater-pill"><Link2 :size="14" />{{ props.taskTitle }}</span>
        <button type="button" class="theater-exit" @click="emit('close')">
          <Minimize2 :size="15" />退出剧场 <kbd>Esc</kbd>
        </button>
      </header>

      <main class="theater-center">
        <div class="theater-dial">
          <ProgressRing :progress="timerProgress ?? 0" :size="336" :stroke="8" ticks />
          <div class="theater-face">
            <span class="theater-status">{{ timerStatus }}</span>
            <strong class="theater-digits tabular" :class="{ long: displayTime.length > 5 }">{{ displayTime }}</strong>
          </div>
        </div>

        <div class="theater-controls">
          <template v-if="timer?.stage === 'offer'">
            <button type="button" class="btn primary lg pill" :disabled="timerBusy" @click="actTimer('start_break')">
              <Coffee :size="17" />开始休息
            </button>
            <button type="button" class="btn secondary lg pill" :disabled="timerBusy" @click="actTimer('dismiss')">
              <CheckCircle2 :size="16" />完成本轮
            </button>
          </template>
          <template v-else-if="timer">
            <button
              type="button"
              class="btn primary lg pill"
              :disabled="timerBusy"
              @click="actTimer(timer.running_since === null ? 'resume' : 'pause')"
            >
              <Play v-if="timer.running_since === null" :size="17" />
              <Pause v-else :size="17" />
              {{ timer.running_since === null ? '继续专注' : '暂停专注' }}
            </button>
            <button type="button" class="btn secondary lg pill" :disabled="timerBusy" @click="finishTimer">
              <Square :size="15" />{{ timer.stage === 'break' ? '结束休息' : '结束并记录' }}
            </button>
          </template>
          <template v-else>
            <button type="button" class="btn primary lg pill" :disabled="!canStart || timerBusy" @click="emit('start')">
              <Play :size="17" />开始沉浸专注
            </button>
          </template>
        </div>
      </main>

      <footer class="theater-foot glass-card">
        <AmbientMixer compact />
      </footer>
    </div>
  </Teleport>
</template>

<style scoped>
.theater-stage {
  position: fixed;
  inset: 0;
  z-index: 180;
  display: grid;
  grid-template-rows: auto 1fr auto;
  padding: 24px 28px max(24px, env(safe-area-inset-bottom));
  background: var(--bg-canvas);
  overflow: auto;
}
.theater-aura {
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background:
    radial-gradient(50% 50% at 50% 44%, var(--accent-soft-strong), transparent 68%),
    radial-gradient(45% 45% at 20% 20%, var(--ambient-1), transparent 70%),
    radial-gradient(45% 45% at 80% 80%, var(--ambient-2), transparent 70%);
  transition: opacity 0.8s;
}
.theater-aura.running {
  animation: breath 7s ease-in-out infinite;
}
@keyframes breath {
  0%, 100% { opacity: 0.72; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.06); }
}
.theater-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  max-width: 960px;
  width: 100%;
  margin: 0 auto;
}
.theater-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 14px;
  border-radius: var(--radius-pill);
  background: var(--surface-glass);
  border: 1px solid var(--border);
  font-size: 13px;
  font-weight: 560;
  max-width: 60vw;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.theater-exit {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 14px;
  border-radius: var(--radius-pill);
  background: var(--surface-glass);
  border: 1px solid var(--border);
  font-size: 12.5px;
  font-weight: 560;
  color: var(--ink-secondary);
}
.theater-exit:hover {
  color: var(--ink);
  border-color: var(--border-strong);
}
.theater-exit kbd {
  font-family: var(--font-mono);
  font-size: 10.5px;
  padding: 1px 5px;
  border-radius: 5px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
}
.theater-center {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 32px;
  padding: 20px 0;
}
.theater-dial {
  position: relative;
  display: grid;
  place-items: center;
}
.theater-face {
  position: absolute;
  text-align: center;
  display: grid;
  gap: 6px;
}
.theater-status {
  font-size: 13.5px;
  font-weight: 620;
  color: var(--accent);
  letter-spacing: 0.04em;
}
.theater-digits {
  font-size: 76px;
  font-weight: 740;
  line-height: 1;
  letter-spacing: -0.04em;
}
.theater-digits.long {
  font-size: 56px;
}
.theater-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}
.theater-foot {
  width: min(100%, 600px);
  margin: 0 auto;
  padding: 14px 18px;
}
@media (max-width: 600px) {
  .theater-stage {
    padding: 14px 14px max(16px, env(safe-area-inset-bottom));
  }
  .theater-dial :deep(.progress-ring) {
    width: min(256px, 72vw);
    height: min(256px, 72vw);
  }
  .theater-digits {
    font-size: 52px;
  }
  .theater-digits.long {
    font-size: 38px;
  }
  .theater-foot {
    padding: 12px 14px;
  }
}
</style>
