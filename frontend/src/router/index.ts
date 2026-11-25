import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: { name: 'today' } },
    { path: '/today', name: 'today', component: () => import('@/views/Today.vue') },
    { path: '/timer', name: 'timer', component: () => import('@/views/Timer.vue') },
    { path: '/plan', name: 'plan', component: () => import('@/views/Plan.vue') },
    { path: '/reviews', name: 'reviews', component: () => import('@/views/Reviews.vue') },
    { path: '/stats', name: 'stats', component: () => import('@/views/Stats.vue') },
    { path: '/me', name: 'me', component: () => import('@/views/Me.vue') },
    { path: '/admin', name: 'admin', meta: { requiresAdmin: true }, component: () => import('@/views/Admin.vue') },
    { path: '/:pathMatch(.*)*', redirect: { name: 'today' } },
  ],
  scrollBehavior(_to, _from, saved) {
    return saved ?? { top: 0 }
  },
})

export default router
