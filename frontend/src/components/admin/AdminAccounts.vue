<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Ellipsis, Eye, KeyRound, Power, Send, ShieldCheck, Trash2 } from 'lucide-vue-next'
import GlassPopover from '@/components/ui/GlassPopover.vue'
import PageSkeleton from '@/components/ui/PageSkeleton.vue'
import type { AdminAccount, User } from '@/types'
import AdminAccountModal, { type AccountActionMode } from './AdminAccountModal.vue'
import AdminInspectDrawer from './AdminInspectDrawer.vue'

const props = defineProps<{ accounts: AdminAccount[] | null; loading: boolean }>()
const emit = defineEmits<{ changed: []; compose: [ids: number[]] }>()
const route = useRoute()
const router = useRouter()

const search = ref('')
const page = ref(1)
const pageSize = 20
const active = computed(() => (route.query.active === 'enabled' || route.query.active === 'disabled' ? route.query.active : ''))
const checkin = computed(() =>
  route.query.checkin === 'checked' || route.query.checkin === 'unchecked' ? route.query.checkin : '',
)

const users = computed(() =>
  (props.accounts ?? [])
    .filter(
      user =>
        user.username.toLowerCase().includes(search.value.trim().toLowerCase()) &&
        (!active.value || (user.role === 'user' && user.active === (active.value === 'enabled'))) &&
        (!checkin.value || (user.role === 'user' && user.checked_today === (checkin.value === 'checked'))),
    )
    .sort((a, b) => Number(b.role === 'admin') - Number(a.role === 'admin') || b.id - a.id),
)
const pageCount = computed(() => Math.max(1, Math.ceil(users.value.length / pageSize)))
const visibleUsers = computed(() => users.value.slice((page.value - 1) * pageSize, page.value * pageSize))

const actionOpen = ref(false)
const actionMode = ref<AccountActionMode>('create')
const actionTarget = ref<User | null>(null)
const inspectOpen = ref(false)
const inspectTarget = ref<User | null>(null)

function setFilters(activeValue: string, checkinValue: string) {
  void router.replace({
    name: 'admin',
    query: { section: 'accounts', active: activeValue || undefined, checkin: checkinValue || undefined },
  })
}

watch([search, active, checkin], () => {
  page.value = 1
})

function openAction(mode: AccountActionMode, user?: User) {
  actionMode.value = mode
  actionTarget.value = user ?? null
  actionOpen.value = true
}

function openInspect(user: User) {
  inspectTarget.value = user
  inspectOpen.value = true
}

function create() {
  openAction('create')
}
defineExpose({ create })

function runAction(action: AccountActionMode | 'inspect' | 'message', user: User) {
  if (action === 'message') {
    if (user.active) emit('compose', [user.id])
    else void router.push({ name: 'admin', query: { section: 'messages', status: 'sent', recipient: user.id } })
  } else if (action === 'inspect') {
    openInspect(user)
  } else {
    openAction(action, user)
  }
}

function onActionDone(created: boolean) {
  if (created) page.value = 1
  emit('changed')
}
</script>

<template>
  <section class="glass-card admin-card">
    <header class="section-head">
      <h2>账号列表</h2>
      <span v-if="accounts" class="pill tabular">{{ users.length }} 个账号</span>
    </header>

    <div class="admin-filters">
      <input v-model="search" type="search" placeholder="搜索用户名…" style="max-width: 240px" />
      <select :value="active" style="max-width: 150px" @change="setFilters(($event.target as HTMLSelectElement).value, checkin)">
        <option value="">全部状态</option>
        <option value="enabled">已启用</option>
        <option value="disabled">已停用</option>
      </select>
      <select :value="checkin" style="max-width: 150px" @change="setFilters(active, ($event.target as HTMLSelectElement).value)">
        <option value="">全部打卡</option>
        <option value="checked">今日已打卡</option>
        <option value="unchecked">今日未打卡</option>
      </select>
      <button v-if="search || active || checkin" type="button" class="btn ghost sm" @click="search = ''; setFilters('', '')">
        清除筛选
      </button>
    </div>

    <PageSkeleton v-if="!accounts && loading" layout="accounts" />
    <div v-else-if="accounts && !users.length" class="empty-box compact">没有符合筛选条件的账号</div>

    <div v-else-if="accounts" class="account-rows">
      <div v-for="user in visibleUsers" :key="user.id" class="account-row">
        <div class="acc-user">
          <span class="avatar-circle sm-av">{{ user.username[0]?.toUpperCase() }}</span>
          <div class="acc-names">
            <button v-if="user.role === 'user'" type="button" class="name-link" @click="openInspect(user)">
              {{ user.username }}
            </button>
            <strong v-else>{{ user.username }}</strong>
            <small class="tertiary">{{ user.role === 'admin' ? '超级管理员' : '学习账号' }}</small>
          </div>
        </div>

        <div class="acc-badges">
          <span class="pill" :class="user.active ? 'success' : ''">{{ user.active ? '已启用' : '已停用' }}</span>
          <span v-if="user.must_change" class="pill warning">待改密</span>
          <span v-if="user.role === 'user'" class="pill" :class="{ accent: user.checked_today }">
            {{ user.checked_today ? '今日已打卡' : '今日未打卡' }}
          </span>
        </div>

        <span class="acc-last tertiary tabular">
          {{ user.role === 'user' ? (user.last_checkin_date ? `最近 ${user.last_checkin_date}` : '尚无打卡') : '—' }}
        </span>

        <div class="acc-ops">
          <GlassPopover v-if="user.role === 'user'">
            <template #trigger="{ toggle }">
              <button type="button" class="icon-btn sm" :aria-label="`操作 ${user.username}`" @click="toggle">
                <Ellipsis :size="18" />
              </button>
            </template>
            <button type="button" role="menuitem" @click="runAction('message', user)">
              <Send :size="15" />{{ user.active ? '发送消息' : '消息记录' }}
            </button>
            <button type="button" role="menuitem" @click="runAction('inspect', user)">
              <Eye :size="15" />查看学习数据
            </button>
            <button type="button" role="menuitem" @click="runAction('active', user)">
              <Power :size="15" />{{ user.active ? '停用账号' : '启用账号' }}
            </button>
            <button type="button" role="menuitem" @click="runAction('reset', user)">
              <KeyRound :size="15" />重置密码
            </button>
            <button type="button" role="menuitem" class="danger-item" @click="runAction('delete', user)">
              <Trash2 :size="15" />删除账号
            </button>
          </GlassPopover>
          <ShieldCheck v-else :size="17" class="tertiary" />
        </div>
      </div>
    </div>

    <div v-if="pageCount > 1" class="pager">
      <button type="button" class="btn ghost sm" :disabled="page <= 1" @click="page--">上一页</button>
      <span class="tabular muted">{{ page }} / {{ pageCount }}</span>
      <button type="button" class="btn ghost sm" :disabled="page >= pageCount" @click="page++">下一页</button>
    </div>

    <AdminAccountModal v-model="actionOpen" :mode="actionMode" :target="actionTarget" @done="onActionDone" />
    <AdminInspectDrawer v-model="inspectOpen" :user="inspectTarget" />
  </section>
</template>

<style scoped>
.admin-card {
  padding: 20px 22px;
  display: grid;
  gap: 16px;
}
.admin-card h2 {
  font-size: 16px;
  font-weight: 680;
}
.admin-filters {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.account-rows {
  display: grid;
  gap: 8px;
}
.account-row {
  display: grid;
  grid-template-columns: minmax(150px, 1.2fr) minmax(160px, 1.4fr) auto auto;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 15px;
  background: var(--surface-subtle);
  border: 1px solid var(--border);
}
.acc-user {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.sm-av {
  width: 32px;
  height: 32px;
  font-size: 13px;
}
.acc-names {
  display: grid;
  min-width: 0;
}
.name-link {
  font-weight: 640;
  text-align: left;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.name-link:hover {
  color: var(--accent);
}
.acc-badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.acc-last {
  font-size: 12px;
  white-space: nowrap;
}
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
@media (max-width: 780px) {
  .admin-card {
    padding: 15px 14px;
    gap: 12px;
  }
  .admin-filters {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .admin-filters input[type='search'] {
    grid-column: 1 / -1;
    max-width: none !important;
  }
  .admin-filters select {
    max-width: none !important;
  }
  .account-row {
    grid-template-columns: minmax(0, 1fr) auto;
    padding: 11px 12px;
    gap: 8px;
  }
  .acc-user {
    grid-column: 1;
    grid-row: 1;
  }
  .acc-ops {
    grid-column: 2;
    grid-row: 1;
    justify-self: end;
    align-self: center;
  }
  .acc-badges {
    grid-column: 1 / -1;
    grid-row: 2;
  }
  .acc-last {
    grid-column: 1 / -1;
    grid-row: 3;
  }
}
</style>
