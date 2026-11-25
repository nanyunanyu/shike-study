<script setup lang="ts">
import { ArrowRight, X } from 'lucide-vue-next'
import { MESSAGE_KINDS } from '@/constants/messages'
import type { InboxMessage, MessagePreview } from '@/types'

defineProps<{
  visible: boolean
  preview: MessagePreview | null
}>()

const emit = defineEmits<{
  open: [message: InboxMessage]
  dismiss: []
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="toast-slide">
      <aside v-if="visible && preview" class="float-notice glass-card-solid" aria-label="站内新消息">
        <div class="notice-icon">
          <component :is="MESSAGE_KINDS[preview.message.kind].icon" :size="17" />
        </div>
        <div class="notice-copy">
          <div class="notice-top">
            <strong>{{ MESSAGE_KINDS[preview.message.kind].label }}</strong>
            <span class="tertiary">{{ preview.message.sender }}</span>
          </div>
          <p>{{ preview.message.body }}</p>
          <small v-if="preview.more" class="accent-text">另有 {{ preview.more }} 条未读消息</small>
        </div>
        <div class="notice-actions">
          <button type="button" class="icon-btn sm" aria-label="查看详情" @click="emit('open', preview.message)">
            <ArrowRight :size="15" />
          </button>
          <button type="button" class="icon-btn sm" aria-label="暂不查看" @click="emit('dismiss')">
            <X :size="15" />
          </button>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<style scoped>
.float-notice {
  position: fixed;
  z-index: 90;
  top: max(14px, env(safe-area-inset-top));
  left: 50%;
  transform: translateX(-50%);
  width: min(400px, calc(100vw - 28px));
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 13px 12px 13px 15px;
  border-radius: 18px;
}
.notice-icon {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  flex: none;
  background: var(--accent-soft);
  color: var(--accent);
}
.notice-copy {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 3px;
}
.notice-top {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
}
.notice-copy p {
  font-size: 13px;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.notice-actions {
  display: flex;
  gap: 2px;
  flex: none;
}
</style>
