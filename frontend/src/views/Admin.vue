<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LayoutDashboard, Mail, Plus, Send, Users } from 'lucide-vue-next'
import { fetchAdminOverview } from '@/api/admin'
import AdminAccounts from '@/components/admin/AdminAccounts.vue'
import AdminComposer from '@/components/admin/AdminComposer.vue'
import AdminDispatches from '@/components/admin/AdminDispatches.vue'
import AdminOverviewSection from '@/components/admin/AdminOverviewSection.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PageSkeleton from '@/components/ui/PageSkeleton.vue'
import { session, today } from '@/stores/session'
import type { AdminOverview } from '@/types'

const route = useRoute()
const router = useRouter()

const sections = [
  { id: 'overview', label: '学习总览', icon: LayoutDashboard },
  { id: 'accounts', label: '账号管理', icon: Users },
  { id: 'messages', label: '消息管理', icon: Mail },
] as const

const section = computed(() => sections.find(item => item.id === route.query.section)?.id ?? 'overview')
const snapshot = ref<AdminOverview | null>(null)
const error = ref('')
const loading = ref(false)
const composer = ref(false)
const composerKey = ref(0)
const initialRecipients = ref<number[]>([])
const dispatchRevision = ref(0)
const accountsView = ref<InstanceType<typeof AdminAccounts> | null>(null)
let sentDispatch: { key: string; scheduled: boolean } | null = null
let version = 0

const timeZone = computed(() => session.value?.timezone ?? 'Asia/Shanghai')

async function refresh() {
  const token = ++version
  loading.value = true
  error.value = ''
  try {
    const data = await fetchAdminOverview()
    if (token === version) snapshot.value = data
  } catch (e) {
    if (token === version) error.value = (e as Error).message
  } finally {
    if (token === version) loading.value = false
  }
}

watch(today, refresh, { immediate: true })
watch(section, () => void refresh())
onMounted(() => window.addEventListener('focus', refresh))
onUnmounted(() => {
  window.removeEventListener('focus', refresh)
  version++
})

function openComposer(ids: number[] = []) {
  if (!snapshot.value) return
  initialRecipients.value = ids
  composerKey.value++
  composer.value = true
}

async function composerClosed() {
  const result = sentDispatch
  sentDispatch = null
  if (result) {
    await router.push({
      name: 'admin',
      query: { section: 'messages', status: result.scheduled ? 'pending' : 'sent', dispatch: result.key },
    })
    dispatchRevision.value++
    void refresh()
  }
}

async function primaryAction() {
  if (section.value === 'messages') return openComposer()
  if (section.value !== 'accounts') await router.push({ name: 'admin', query: { section: 'accounts' } })
  await nextTick()
  accountsView.value?.create()
}
</script>

<template>
  <div class="page admin-page">
    <PageHeader eyebrow="ADMIN CONSOLE" title="管理后台" subtitle="学习打卡总览、账号管理与站内消息投递">
      <button type="button" class="btn primary pill" :disabled="section === 'messages' && !snapshot" @click="primaryAction">
        <Send v-if="section === 'messages'" :size="15" />
        <Plus v-else :size="15" />
        {{ section === 'messages' ? '新建消息' : '创建账号' }}
      </button>
    </PageHeader>

    <nav class="admin-tabs segmented" aria-label="后台栏目">
      <RouterLink
        v-for="item in sections"
        :key="item.id"
        :to="{ name: 'admin', query: item.id === 'overview' ? {} : { section: item.id } }"
        custom
        v-slot="{ navigate }"
      >
        <button type="button" :aria-pressed="section === item.id" @click="navigate">
          <component :is="item.icon" :size="14" />{{ item.label }}
        </button>
      </RouterLink>
    </nav>

    <p v-if="error" class="error-text" role="alert" style="margin-bottom: 14px">
      {{ error }} <button type="button" class="btn ghost sm" @click="refresh">重试</button>
    </p>

    <template v-if="section === 'overview'">
      <PageSkeleton v-if="!snapshot && loading" layout="admin-overview" />
      <AdminOverviewSection v-else-if="snapshot" :snapshot="snapshot" />
    </template>

    <AdminAccounts
      v-else-if="section === 'accounts'"
      ref="accountsView"
      :accounts="snapshot?.accounts ?? null"
      :loading="loading"
      @changed="refresh"
      @compose="openComposer"
    />

    <AdminDispatches
      v-else
      :accounts="snapshot?.accounts ?? []"
      :timezone="timeZone"
      :revision="dispatchRevision"
      @changed="refresh"
    />

    <AdminComposer
      v-if="composerKey && snapshot"
      :key="composerKey"
      v-model="composer"
      :accounts="snapshot.accounts"
      :initial-recipients="initialRecipients"
      :timezone="timeZone"
      @sent="(key, scheduled) => { sentDispatch = { key, scheduled } }"
      @refresh="refresh"
      @after-leave="composerClosed"
    />
  </div>
</template>

<style scoped>
.admin-tabs {
  margin-bottom: 20px;
}
@media (max-width: 768px) {
  .admin-tabs {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    margin-bottom: 14px;
  }
}
</style>
