<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Ellipsis, Eye, KeyRound, Power, Send, ShieldCheck, Trash2 } from 'lucide-vue-next'
import type { AdminAccount } from '../admin'
import type { Day, Plan, Statistics, User } from '../types'
import { api, duration, notify, today } from '../state'
import ReviewCard from '../components/ReviewCard.vue'
import StudyReport from '../components/StudyReport.vue'
import CategoryBadge from '../components/ui/CategoryBadge.vue'
import GlassModal from '../components/ui/GlassModal.vue'
import GlassPopover from '../components/ui/GlassPopover.vue'
import PageSkeleton from '../components/ui/PageSkeleton.vue'

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

const busy = ref(false)
const formError = ref('')
const target = ref<User | null>(null)
const pane = ref<'create' | 'reset' | 'active' | 'delete' | 'inspect' | null>(null)
const open = computed({
  get: () => pane.value !== null,
  set: value => {
    if (!value) pane.value = null
  },
})
const username = ref('')
const password = ref('')
const mustChange = ref(true)
const confirmation = ref('')

const tab = ref<'day' | 'plan' | 'statistics'>('day')
const date = ref(today.value)
const day = ref<Day | null>(null)
const plan = ref<Plan | null>(null)
const stats = ref<Statistics | null>(null)
const inspectionError = ref('')

const title = computed(
  () =>
    ({
      create: '创建学习账号',
      reset: '重置账号密码',
      active: target.value?.active ? '停用账号' : '启用账号',
      delete: '删除账号',
      inspect: `${target.value?.username ?? ''} · 只读查看`,
    })[pane.value ?? 'create'],
)

function setFilters(activeValue: string, checkinValue: string) {
  void router.replace({
    name: 'admin',
    query: { section: 'accounts', active: activeValue || undefined, checkin: checkinValue || undefined },
  })
}

watch([search, active, checkin], () => {
  page.value = 1
})

function show(kind: NonNullable<typeof pane.value>, user?: User) {
  target.value = user ?? null
  formError.value = ''
  username.value = password.value = confirmation.value = ''
  mustChange.value = true
  tab.value = 'day'
  date.value = today.value
  pane.value = kind
}

function create() {
  show('create')
}
defineExpose({ create })

function runAction(action: string, user: User) {
  if (action === 'message') {
    if (user.active) emit('compose', [user.id])
    else void router.push({ name: 'admin', query: { section: 'messages', status: 'sent', recipient: user.id } })
  } else {
    show(action as NonNullable<typeof pane.value>, user)
  }
}

async function submit() {
  if (!pane.value) return
  busy.value = true
  formError.value = ''
  const user = target.value
  const base = `/admin/users${user ? `/${user.id}` : ''}`
  try {
    if (pane.value === 'create') {
      await api(base, 'POST', { username: username.value, password: password.value, must_change: mustChange.value })
      page.value = 1
    }
    if (pane.value === 'reset') await api(`${base}/password`, 'PUT', { password: password.value, must_change: mustChange.value })
    if (pane.value === 'active' && user) await api(`${base}/active`, 'PUT', { active: !user.active })
    if (pane.value === 'delete' && user && confirmation.value === user.username) await api(base, 'DELETE')
    notify(`${title.value}成功`)
    pane.value = null
    password.value = ''
    emit('changed')
  } catch (e) {
    formError.value = (e as Error).message
  } finally {
    busy.value = false
  }
}

watch([pane, tab, date], async (_, _old, cleanup) => {
  if (pane.value !== 'inspect' || !target.value || (tab.value === 'day' && !date.value)) return
  let valid = true
  cleanup(() => {
    valid = false
  })
  day.value = plan.value = stats.value = null
  inspectionError.value = ''
  const base = `/admin/users/${target.value.id}`
  try {
    if (tab.value === 'day') {
      const value = await api<Day>(`${base}/day/${date.value}`)
      if (valid) day.value = value
    }
    if (tab.value === 'plan') {
      const value = await api<Plan>(`${base}/plan`)
      if (valid) plan.value = value
    }
    if (tab.value === 'statistics') {
      const value = await api<Statistics>(`${base}/statistics`)
      if (valid) stats.value = value
    }
  } catch (e) {
    if (valid) inspectionError.value = (e as Error).message
  }
})
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
            <button v-if="user.role === 'user'" type="button" class="name-link" @click="show('inspect', user)">
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

    <GlassModal v-model="open" :title="title" :busy="busy" :drawer="pane === 'inspect'">
      <form v-if="pane && pane !== 'inspect'" class="form-stack" @submit.prevent="submit">
        <template v-if="pane === 'create' || pane === 'reset'">
          <label v-if="pane === 'create'" class="field">
            <span class="field-label">用户名</span>
            <input v-model="username" required minlength="3" maxlength="32" pattern="[A-Za-z0-9][A-Za-z0-9_.\-]{2,31}" placeholder="3-32 位字母/数字" />
          </label>
          <p v-else class="muted">目标账号：<strong>{{ target?.username }}</strong></p>
          <label class="field">
            <span class="field-label">{{ pane === 'create' ? '初始密码' : '新密码' }}</span>
            <input v-model="password" type="password" required minlength="6" maxlength="256" placeholder="至少 6 位" />
          </label>
          <label class="switch-row glass-inset" style="padding: 8px 14px">
            <span>下次登录必须修改密码</span>
            <input v-model="mustChange" type="checkbox" role="switch" />
          </label>
        </template>
        <template v-if="pane === 'active'">
          <p>确认{{ target?.active ? '停用' : '启用' }}账号 <strong>{{ target?.username }}</strong>？</p>
          <p v-if="target?.active" class="muted">停用后该账号的现有登录会话将立即失效。</p>
        </template>
        <template v-if="pane === 'delete'">
          <p>将永久删除账号及其所有在线学习数据。请输入 <strong>{{ target?.username }}</strong> 以确认：</p>
          <input v-model="confirmation" required autocomplete="off" />
        </template>
        <p v-if="formError" class="error-text" role="alert">{{ formError }}</p>
        <div class="dialog-actions">
          <button type="button" class="btn ghost" :disabled="busy" @click="pane = null">取消</button>
          <button type="submit" class="btn" :class="pane === 'delete' ? 'danger' : 'primary'" :disabled="busy || (pane === 'delete' && confirmation !== target?.username)">
            {{ title }}
          </button>
        </div>
      </form>

      <div v-else-if="pane === 'inspect'" class="form-stack">
        <div class="section-head">
          <div class="segmented">
            <button type="button" :aria-pressed="tab === 'day'" @click="tab = 'day'">日记录</button>
            <button type="button" :aria-pressed="tab === 'plan'" @click="tab = 'plan'">计划</button>
            <button type="button" :aria-pressed="tab === 'statistics'" @click="tab = 'statistics'">统计</button>
          </div>
          <input v-if="tab === 'day'" v-model="date" :max="today" type="date" style="width: auto" />
        </div>

        <p v-if="inspectionError" class="error-text" role="alert">{{ inspectionError }}</p>

        <template v-else-if="tab === 'day' && day">
          <div v-if="!day.exists && day.date !== today" class="empty-box compact">当天无记录</div>
          <template v-else>
            <div class="inspect-pills">
              <span class="pill" :class="{ success: !!day.checked_at }">{{ day.checked_at ? '已打卡' : '未打卡' }}</span>
              <span class="pill tabular">专注 {{ duration(day.focus_seconds) }}</span>
            </div>
            <ul class="inspect-list">
              <li v-for="item in day.tasks" :key="item.id">
                <span>{{ (item.override ?? item).start }} · {{ item.title }}</span>
                <span class="pill" :class="{ accent: item.done }">{{ item.done ? '已完成' : '未完成' }}</span>
              </li>
            </ul>
            <h3 style="font-size: 14px; margin-top: 6px">每日复盘</h3>
            <ReviewCard v-model="day.review" readonly />
          </template>
        </template>

        <template v-else-if="tab === 'plan' && plan">
          <p class="muted">当前计划版本 · {{ plan.current.date }}</p>
          <ul class="inspect-list">
            <li v-for="item in plan.current.tasks" :key="item.id">
              <span>{{ item.start }} · {{ item.title }}</span>
              <CategoryBadge :id="item.category" :name="item.category_name" />
            </li>
          </ul>
        </template>

        <StudyReport v-else-if="tab === 'statistics' && stats" :data="stats" compact />
        <PageSkeleton v-else :layout="tab === 'statistics' ? 'stats' : tab === 'day' ? 'inspection-day' : 'inspection-plan'" />
      </div>
    </GlassModal>
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
.inspect-pills {
  display: flex;
  gap: 8px;
}
.inspect-list {
  display: grid;
  gap: 6px;
  max-height: 260px;
  overflow-y: auto;
}
.inspect-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 11px;
  border-radius: 11px;
  background: var(--surface-subtle);
  font-size: 12.5px;
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
  .acc-badges,
  .acc-last {
    grid-column: 1 / -1;
  }
}
</style>
