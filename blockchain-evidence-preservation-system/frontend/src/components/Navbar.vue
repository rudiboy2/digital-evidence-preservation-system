<template>
  <nav class="navbar">
    <div class="navbar__inner">

      <!-- Brand -->
      <RouterLink :to="homeRoute" class="navbar__brand">
        <span class="navbar__logo">⬡</span>
        <span class="navbar__title">BEPS</span>
        <span class="navbar__subtitle">Evidence Vault</span>
      </RouterLink>

      <!-- Role-based Nav Links -->
      <ul class="navbar__links">

        <!-- Admin & Investigator & Officer → Dashboard -->
        <li v-if="['admin','investigator','officer'].includes(userRole)">
          <RouterLink to="/dashboard" class="navbar__link" active-class="navbar__link--active">
            Dashboard
          </RouterLink>
        </li>

        <!-- Analyst → Forensic Analysis -->
        <li v-if="['analyst','admin'].includes(userRole)">
          <RouterLink to="/analyst" class="navbar__link" active-class="navbar__link--active">
            🔬 Analysis
          </RouterLink>
        </li>

        <!-- Auditor → Compliance Audit -->
        <li v-if="['auditor','admin'].includes(userRole)">
          <RouterLink to="/auditor" class="navbar__link" active-class="navbar__link--active">
            📋 Audit
          </RouterLink>
        </li>

        <!-- Admin → User Management -->
        <li v-if="userRole === 'admin'">
          <RouterLink to="/users" class="navbar__link" active-class="navbar__link--active">
            👤 Users
          </RouterLink>
        </li>

      </ul>

      <!-- Right Side -->
      <div class="navbar__right">

        <!-- User Card showing name + role -->
        <div class="navbar__user-card">
          <div class="navbar__user-avatar">{{ userInitial }}</div>
          <div class="navbar__user-info">
            <span class="navbar__user-name">{{ userName || userEmail }}</span>
            <span :class="['navbar__user-role', `navbar__user-role--${userRole}`]">
              {{ roleLabel }}
            </span>
          </div>
        </div>

        <!-- Chain Status -->
        <div class="navbar__status">
          <span :class="['navbar__dot', chainConnected ? 'navbar__dot--on' : 'navbar__dot--off']" />
          <span class="navbar__status-text">
            {{ chainConnected ? 'Chain Connected' : 'Chain Offline' }}
          </span>
        </div>

        <button class="btn btn--ghost navbar__logout" @click="logout">Logout</button>
      </div>

    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const chainConnected = ref(false)
let intervalId = null

const userRole  = computed(() => localStorage.getItem('user_role')  || '')
const userName  = computed(() => localStorage.getItem('user_name')  || '')
const userEmail = computed(() => localStorage.getItem('user_email') || '')

const userInitial = computed(() => {
  const n = userName.value || userEmail.value
  return n ? n.charAt(0).toUpperCase() : 'U'
})

const roleLabel = computed(() => ({
  admin:        '⬡ Admin',
  investigator: '🔍 Investigator',
  officer:      '👮 Officer',
  analyst:      '🔬 Analyst',
  auditor:      '📋 Auditor',
}[userRole.value] || userRole.value))

// Where the brand logo navigates based on role
const homeRoute = computed(() => ({
  analyst: '/analyst',
  auditor: '/auditor',
}[userRole.value] || '/dashboard'))

async function checkChain() {
  try {
    const r = await fetch('http://localhost:8000/health')
    const d = await r.json()
    chainConnected.value = d.status === 'healthy'
  } catch {
    chainConnected.value = false
  }
}

onMounted(() => {
  checkChain()
  intervalId = setInterval(checkChain, 8000)
})

onUnmounted(() => { if (intervalId) clearInterval(intervalId) })

function logout() {
  ['access_token','refresh_token','user_role','user_name','user_email']
    .forEach(k => localStorage.removeItem(k))
  router.push({ name: 'home' })
}
</script>

<style scoped>
.navbar {
  position: fixed; top: 0; left: 0; right: 0; height: 64px;
  background: rgba(10,12,15,0.95); backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border); z-index: 1000;
}
.navbar__inner {
  max-width: 1280px; margin: 0 auto; padding: 0 24px;
  height: 100%; display: flex; align-items: center; gap: 24px;
}
.navbar__brand {
  display: flex; align-items: center; gap: 10px;
  text-decoration: none; flex-shrink: 0;
}
.navbar__logo { font-size: 1.4rem; color: var(--amber); line-height: 1; }
.navbar__title {
  font-family: var(--font-display); font-size: 1.2rem; font-weight: 700;
  letter-spacing: 0.15em; text-transform: uppercase; color: var(--text-primary);
}
.navbar__subtitle {
  font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted); border-left: 1px solid var(--border);
  padding-left: 10px; margin-left: 4px;
}
.navbar__links { display: flex; list-style: none; gap: 4px; flex: 1; }
.navbar__link {
  font-family: var(--font-display); font-size: 0.78rem; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-secondary); padding: 6px 12px;
  border-radius: var(--radius); text-decoration: none; transition: all 0.2s;
}
.navbar__link:hover, .navbar__link--active {
  color: var(--amber); background: var(--amber-glow); text-decoration: none;
}
.navbar__right { display: flex; align-items: center; gap: 16px; margin-left: auto; }

/* User card */
.navbar__user-card {
  display: flex; align-items: center; gap: 10px;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 6px 14px 6px 8px;
}
.navbar__user-avatar {
  width: 30px; height: 30px; border-radius: 50%;
  background: var(--amber); color: var(--bg-primary);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 0.9rem; font-weight: 700;
}
.navbar__user-info { display: flex; flex-direction: column; gap: 1px; }
.navbar__user-name {
  font-size: 0.75rem; font-weight: 500; color: var(--text-primary);
  max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.navbar__user-role {
  font-size: 0.62rem; letter-spacing: 0.06em;
  text-transform: uppercase; font-weight: 600;
}
.navbar__user-role--admin        { color: #f87171; }
.navbar__user-role--investigator { color: var(--amber); }
.navbar__user-role--officer      { color: var(--blue-info); }
.navbar__user-role--analyst      { color: var(--green-ok); }
.navbar__user-role--auditor      { color: #94a3b8; }

/* Chain status */
.navbar__status { display: flex; align-items: center; gap: 6px; }
.navbar__dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.navbar__dot--on {
  background: var(--green-ok); box-shadow: 0 0 6px var(--green-ok);
  animation: pulse 2.5s infinite;
}
.navbar__dot--off { background: var(--red-alert); }
@keyframes pulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(16,185,129,0.5); }
  50%      { box-shadow: 0 0 0 5px rgba(16,185,129,0); }
}
.navbar__status-text {
  font-size: 0.65rem; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--text-muted);
}
.navbar__logout { padding: 6px 14px; font-size: 0.72rem; }
</style>
