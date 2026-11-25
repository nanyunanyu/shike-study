<script setup lang="ts">
import { ref, watch } from 'vue'
import { Plus, Save } from 'lucide-vue-next'
import { saveCategoriesApi } from '@/api/plan'
import GlassModal from '@/components/ui/GlassModal.vue'
import { notify } from '@/stores/ui'
import type { Category } from '@/types'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{ categories: Category[] }>()
const emit = defineEmits<{ saved: [categories: Category[]] }>()

const draft = ref<Category[]>([])
const busy = ref(false)
const error = ref('')

watch(open, isOpen => {
  if (isOpen) {
    draft.value = props.categories.map(c => ({ ...c }))
    error.value = ''
  }
})

function addCategory() {
  draft.value.push({ id: crypto.randomUUID(), name: '', builtin: false, archived: false })
}

async function submit() {
  if (busy.value) return
  error.value = ''
  busy.value = true
  try {
    const updated = await saveCategoriesApi(draft.value)
    emit('saved', updated)
    open.value = false
    notify('学习分类已保存')
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <GlassModal v-model="open" title="管理学习分类" :busy="busy">
    <form class="form-stack" @submit.prevent="submit">
      <div v-for="item in draft" :key="item.id" class="cat-edit-row">
        <input v-model="item.name" :disabled="item.builtin" maxlength="100" required placeholder="输入分类名称" />
        <label v-if="!item.builtin" class="archive-check">
          <input v-model="item.archived" type="checkbox" />归档
        </label>
        <span v-else class="pill">内置</span>
      </div>
      <div>
        <button type="button" class="btn secondary sm" :disabled="draft.length >= 100" @click="addCategory">
          <Plus :size="14" />新增分类
        </button>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <div class="dialog-actions">
        <button type="submit" class="btn primary" :disabled="busy"><Save :size="15" />保存分类</button>
      </div>
    </form>
  </GlassModal>
</template>

<style scoped>
.cat-edit-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}
.archive-check {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12.5px;
  color: var(--ink-secondary);
}
</style>
