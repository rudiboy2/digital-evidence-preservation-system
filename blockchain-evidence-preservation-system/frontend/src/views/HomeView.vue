<template>
  <div class="home">
    <!-- Background hex grid -->
    <div class="home__bg" aria-hidden="true">
      <div v-for="n in 24" :key="n" class="home__hex" :style="hexStyle(n)">⬡</div>
    </div>

    <div class="home__content fade-up">
      <!-- Hero -->
      <div class="home__hero">
        <div class="home__badge">Blockchain-Secured</div>
        <h1 class="home__title">Evidence<br /><span class="home__title--accent">Vault</span></h1>
        <p class="home__tagline">
          
        </p>
      </div>

      <!-- Login Card -->
      <div class="home__login card">
        <h2 class="home__login-title">Officer Login</h2>

        <div v-if="errorMsg" class="home__error">
          {{ errorMsg }}
        </div>

        <form class="home__form" @submit.prevent="handleLogin">
          <div class="form-group">
            <label class="form-label" for="email">Badge Email</label>
            <input
              id="email"
              v-model="email"
              type="email"
              class="form-input"
              placeholder="officer@department.gov"
              autocomplete="username"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="password">Password</label>
            <input
              id="password"
              v-model="password"
              type="password"
              class="form-input"
              placeholder="••••••••••••"
              autocomplete="current-password"
              required
            />
          </div>

          <button type="submit" class="btn btn--primary home__submit" :disabled="isLoading">
            <span v-if="isLoading" class="home__spinner" />
            <span v-else>⬡</span>
            {{ isLoading ? 'Authenticating…' : 'Access Vault' }}
          </button>
        </form>

        <p class="home__hint">
          Contact your system administrator to create an account.
        </p>
      </div>
    </div>

    <!-- Feature Strip -->
    <div class="home__features">
      <div v-for="f in features" :key="f.label" class="home__feature">
        <span class="home__feature-icon">{{ f.icon }}</span>
        <span class="home__feature-label">{{ f.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/apiService'

const router = useRouter()
const email    = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMsg  = ref('')

const features = [
  { icon: '⬡', label: 'Blockchain Immutability' },
  { icon: '🔐', label: 'SHA-256 Integrity' },
  { icon: '⛓', label: 'Chain of Custody' },
  { icon: '🌐', label: 'IPFS Decentralised Storage' },
  { icon: '👤', label: 'Role-Based Access' },
  { icon: '📋', label: 'Full Audit Trail' },
]

function hexStyle(n) {
  const row = Math.floor((n - 1) / 6)
  const col = (n - 1) % 6
  return {
    left: `${col * 18 + (row % 2) * 9}%`,
    top:  `${row * 22}%`,
    opacity: (0.03 + Math.random() * 0.06).toFixed(2),
    fontSize: `${3 + Math.random() * 4}rem`,
    animationDelay: `${(n * 0.4).toFixed(1)}s`,
  }
}

async function handleLogin() {
  errorMsg.value  = ''
  isLoading.value = true
  try {
    const form = new URLSearchParams()
    form.append('username', email.value)
    form.append('password', password.value)

    // Step 1: Login to get tokens
    const loginResp = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    })

    if (!loginResp.ok) {
      const errData = await loginResp.json()
      throw new Error(errData.detail || 'Invalid credentials')
    }

    const tokens = await loginResp.json()
    localStorage.setItem('access_token',  tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)

    // Step 2: Fetch profile to get name, email, role
    const profileResp = await fetch('http://localhost:8000/api/v1/auth/me', {
      headers: { 'Authorization': `Bearer ${tokens.access_token}` },
    })

    if (profileResp.ok) {
      const profile = await profileResp.json()
      const roleName = profile.role?.name || profile.role || ''
      localStorage.setItem('user_role',  roleName)
      localStorage.setItem('user_name',  profile.full_name || '')
      localStorage.setItem('user_email', profile.email     || '')
      console.log('Login success — role:', roleName)
    }

    // Send each role to their correct home page
    const roleHome = {
      admin:        'dashboard',
      investigator: 'dashboard',
      officer:      'dashboard',
      analyst:      'analyst',
      auditor:      'auditor',
    }
    const dest = roleHome[localStorage.getItem('user_role') || ''] || 'dashboard'
    router.push({ name: dest })

  } catch (err) {
    errorMsg.value = err.message || 'Authentication failed. Check your credentials.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
  padding: 40px 24px;
}

/* BG hex floaters */
.home__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.home__hex {
  position: absolute;
  color: var(--amber);
  font-family: monospace;
  animation: floatHex 8s ease-in-out infinite;
}

@keyframes floatHex {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50%       { transform: translateY(-12px) rotate(5deg); }
}

/* Content */
.home__content {
  display: flex;
  align-items: center;
  gap: 80px;
  max-width: 900px;
  width: 100%;
  position: relative;
  z-index: 1;
}

.home__hero { flex: 1; }

.home__badge {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--amber);
  border: 1px solid var(--border-amber);
  padding: 4px 12px;
  border-radius: 2px;
  margin-bottom: 20px;
  background: var(--amber-glow);
}

.home__title {
  font-size: 4.5rem;
  line-height: 1;
  margin-bottom: 20px;
  color: var(--text-primary);
}

.home__title--accent { color: var(--amber); }

.home__tagline {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.7;
  max-width: 360px;
}

/* Login card */
.home__login {
  width: 360px;
  flex-shrink: 0;
}

.home__login-title {
  font-size: 1.1rem;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.home__error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: var(--red-alert);
  padding: 10px 14px;
  border-radius: var(--radius);
  font-size: 0.78rem;
  margin-bottom: 16px;
}

.home__form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.home__submit {
  width: 100%;
  justify-content: center;
  margin-top: 8px;
}

.home__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(0,0,0,0.3);
  border-top-color: var(--bg-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

.home__hint {
  margin-top: 16px;
  font-size: 0.68rem;
  color: var(--text-muted);
  text-align: center;
}

/* Feature strip */
.home__features {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 60px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
  width: 100%;
  max-width: 900px;
}

.home__feature {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.home__feature-icon { font-size: 1rem; }

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .home__content { flex-direction: column; gap: 40px; }
  .home__login   { width: 100%; }
  .home__title   { font-size: 3rem; }
}
</style>
