import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Views
import HomeView          from './views/HomeView.vue'
import DashboardView     from './views/DashboardView.vue'
import EvidenceUploadView from './views/EvidenceUploadView.vue'
import CaseDetailView    from './views/CaseDetailView.vue'
import UserManagementView from './views/UserManagementView.vue'
import ChainOfCustodyView from './views/ChainOfCustodyView.vue'
import AnalystView       from './views/AnalystView.vue'
import AuditorView       from './views/AuditorView.vue'

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: HomeView,
      name: 'home',
    },
    {
      path: '/dashboard',
      component: DashboardView,
      name: 'dashboard',
      meta: { requiresAuth: true },
    },
    {
      path: '/analyst',
      component: AnalystView,
      name: 'analyst',
      meta: { requiresAuth: true, roles: ['analyst', 'admin'] },
    },
    {
      path: '/auditor',
      component: AuditorView,
      name: 'auditor',
      meta: { requiresAuth: true, roles: ['auditor', 'admin'] },
    },
    {
      path: '/cases/:id',
      component: CaseDetailView,
      name: 'case-detail',
      meta: { requiresAuth: true },
    },
    {
      path: '/cases/:id/upload',
      component: EvidenceUploadView,
      name: 'evidence-upload',
      meta: {
        requiresAuth: true,
        roles: ['officer', 'investigator', 'admin'],
      },
    },
    {
      path: '/cases/:id/custody',
      component: ChainOfCustodyView,
      name: 'chain-of-custody',
      meta: { requiresAuth: true },
    },
    {
      path: '/users',
      component: UserManagementView,
      name: 'user-management',
      meta: { requiresAuth: true, roles: ['admin'] },
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

// ---------------------------------------------------------------------------
// Navigation Guard — enforces role-based route access
// ---------------------------------------------------------------------------
router.beforeEach((to, from, next) => {
  const token    = localStorage.getItem('access_token')
  const userRole = localStorage.getItem('user_role') || ''

  // Not logged in → send to login
  if (to.meta.requiresAuth && !token) {
    next({ name: 'home' })
    return
  }

  // Role restriction defined on route
  if (to.meta.roles && !to.meta.roles.includes(userRole)) {
    // Redirect to the appropriate home view for this role
    const roleHome = {
      analyst:      'analyst',
      auditor:      'auditor',
      officer:      'dashboard',
      investigator: 'dashboard',
      admin:        'dashboard',
    }
    next({ name: roleHome[userRole] || 'dashboard' })
    return
  }

  next()
})

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------
const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
