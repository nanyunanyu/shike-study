<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Check, Copy, Download, Moon, Sun } from 'lucide-vue-next'
import { dark, notify, preferences } from '../state'
import { renderShareCard, type ShareCardPayload } from '../utils/shareCard'
import GlassModal from './ui/GlassModal.vue'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{ payload: Omit<ShareCardPayload, 'palette' | 'dark'> | null }>()

const cardDark = ref(dark.value)
const previewUrl = ref('')
const copied = ref(false)

watch(open, isOpen => {
  if (isOpen) {
    cardDark.value = dark.value
    copied.value = false
    regenerate()
  }
})

watch(cardDark, regenerate)

const fullPayload = computed<ShareCardPayload | null>(() =>
  props.payload
    ? {
        ...props.payload,
        palette: preferences.value.palette,
        dark: cardDark.value,
      }
    : null,
)

let lastCanvas: HTMLCanvasElement | null = null

function regenerate() {
  if (!fullPayload.value) return
  lastCanvas = renderShareCard(fullPayload.value)
  previewUrl.value = lastCanvas.toDataURL('image/png')
}

function downloadPng() {
  if (!lastCanvas || !fullPayload.value) return
  const link = document.createElement('a')
  link.download = `shike-checkin-${fullPayload.value.date}.png`
  link.href = lastCanvas.toDataURL('image/png')
  link.click()
  notify('打卡海报已保存')
}

async function copyImage() {
  if (!lastCanvas || !navigator.clipboard || typeof ClipboardItem === 'undefined') {
    downloadPng()
    return
  }
  try {
    const blob = await new Promise<Blob | null>(resolve => lastCanvas?.toBlob(resolve, 'image/png'))
    if (!blob) throw new Error('no blob')
    await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })])
    copied.value = true
    notify('已复制图片到剪贴板')
    setTimeout(() => {
      copied.value = false
    }, 2400)
  } catch {
    downloadPng()
  }
}
</script>

<template>
  <GlassModal v-model="open" title="学习打卡分享海报" subtitle="高分辨率 3:4 卡片，适配朋友圈与手账留存">
    <div class="share-wrap">
      <div class="share-toolbar">
        <span class="muted">海报风格</span>
        <div class="segmented" role="group" aria-label="海报明暗模式">
          <button type="button" :aria-pressed="!cardDark" @click="cardDark = false"><Sun :size="14" />浅色通透</button>
          <button type="button" :aria-pressed="cardDark" @click="cardDark = true"><Moon :size="14" />深色午夜</button>
        </div>
      </div>

      <div class="poster-stage">
        <img v-if="previewUrl" :src="previewUrl" alt="学习打卡分享海报预览" class="poster-img" />
      </div>

      <div class="dialog-actions">
        <button type="button" class="btn secondary" @click="copyImage">
          <Check v-if="copied" :size="15" /><Copy v-else :size="15" />{{ copied ? '已复制' : '复制图片' }}
        </button>
        <button type="button" class="btn primary" @click="downloadPng">
          <Download :size="15" />保存 PNG 海报
        </button>
      </div>
    </div>
  </GlassModal>
</template>

<style scoped>
.share-wrap {
  display: grid;
  gap: 16px;
}
.share-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}
.poster-stage {
  display: grid;
  place-items: center;
  padding: 14px;
  border-radius: var(--radius-md);
  background: var(--surface-subtle);
  border: 1px solid var(--border);
}
.poster-img {
  width: min(100%, 310px);
  height: auto;
  border-radius: 16px;
  box-shadow: var(--shadow-float);
}
</style>
