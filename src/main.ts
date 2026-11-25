import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import './styles/tokens.css'
import './styles/base.css'
import App from './App.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: { name: 'today' } },
    { path: '/today', name: 'today', component: () => import('./views/Today.vue') },
    { path: '/timer', name: 'timer', component: () => import('./views/Timer.vue') },
    { path: '/plan', name: 'plan', component: () => import('./views/Plan.vue') },
    { path: '/reviews', name: 'reviews', component: () => import('./views/Reviews.vue') },
    { path: '/stats', name: 'stats', component: () => import('./views/Stats.vue') },
    { path: '/me', name: 'me', component: () => import('./views/Me.vue') },
    { path: '/admin', name: 'admin', component: () => import('./views/Admin.vue') },
    { path: '/:pathMatch(.*)*', redirect: { name: 'today' } },
  ],
  scrollBehavior(_to, _from, saved) {
    return saved ?? { top: 0 }
  },
})

createApp(App).use(router).mount('#app')
