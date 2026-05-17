<template>
  <div class="users-view container">

    <!-- Header -->
    <div class="users-view__header fade-up">
      <div>
        <h1>User Management</h1>
        <p class="users-view__sub">Create and manage officer and forensic professional accounts</p>
      </div>
      <button class="btn btn--primary" @click="showCreateModal = true">
        + Add New User
      </button>
    </div>

    <!-- Role legend -->
    <div class="role-legend fade-up" style="animation-delay:0.05s">
      <div v-for="role in roleDescriptions" :key="role.name" class="role-legend__item">
        <span :class="['badge', `badge--${roleBadge(role.name)}`]">{{ role.name }}</span>
        <span class="role-legend__desc">{{ role.desc }}</span>
      </div>
    </div>

    <!-- Users Table -->
    <div class="card fade-up" style="animation-delay:0.1s">
      <div class="users-view__table-header">
        <h2 class="users-view__section-title">All Accounts ({{ users.length }})</h2>
        <input
          v-model="search"
          class="form-input users-view__search"
          placeholder="Search by name or email…"
        />
      </div>

      <div v-if="isLoading" class="users-view__loading">
        <div class="users-view__spinner" />
      </div>

      <div v-else-if="filteredUsers.length === 0" class="users-view__empty">
        <span style="font-size:2rem">👤</span>
        <p>{{ search ? 'No users match your search.' : 'No users found. Create the first account.' }}</p>
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Full Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Badge #</th>
            <th>Department</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td class="users-view__name">{{ user.full_name }}</td>
            <td class="users-view__email">{{ user.email }}</td>
            <td>
              <span :class="['badge', `badge--${roleBadge(user.role?.name || '')}`]">
                {{ user.role?.name || '—' }}
              </span>
            </td>
            <td><code class="users-view__badge-num">{{ user.badge_number || '—' }}</code></td>
            <td class="users-view__dept">{{ user.department || '—' }}</td>
            <td>
              <span :class="['badge', user.is_active ? 'badge--verified' : 'badge--tampered']">
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="users-view__date">{{ formatDate(user.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ------------------------------------------------------------------ -->
    <!-- Create User Modal                                                    -->
    <!-- ------------------------------------------------------------------ -->
    <Teleport to="body">
      <div v-if="showCreateModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal card fade-up">
          <h2 class="modal__title">Create New Account</h2>
          <p class="modal__subtitle">
            The new user will log in with the email and password you set here.
          </p>

          <div v-if="createError" class="modal__error">{{ createError }}</div>
          <div v-if="createSuccess" class="modal__success">
            ✓ Account created! Share these credentials with the user:<br/>
            <strong>Email:</strong> {{ createdCredentials.email }}<br/>
            <strong>Password:</strong> {{ createdCredentials.password }}
          </div>

          <form v-if="!createSuccess" class="modal__form" @submit.prevent="createUser">

            <!-- Name & Email -->
            <div class="modal__row">
              <div class="form-group">
                <label class="form-label">Full Name *</label>
                <input v-model="newUser.full_name" class="form-input" required
                  placeholder="e.g. Jane Smith" />
              </div>
              <div class="form-group">
                <label class="form-label">Email Address *</label>
                <input v-model="newUser.email" type="email" class="form-input" required
                  placeholder="officer@department.com" />
              </div>
            </div>

            <!-- Password -->
            <div class="form-group">
              <label class="form-label">Password * (min 12 characters)</label>
              <div class="modal__pw-row">
                <input
                  v-model="newUser.password"
                  :type="showPassword ? 'text' : 'password'"
                  class="form-input modal__pw-input"
                  required
                  minlength="12"
                  placeholder="Min. 12 characters"
                />
                <button type="button" class="modal__pw-toggle" @click="showPassword = !showPassword">
                  {{ showPassword ? '🙈' : '👁' }}
                </button>
                <button type="button" class="btn btn--ghost modal__pw-gen" @click="generatePassword">
                  Generate
                </button>
              </div>
              <span v-if="newUser.password && newUser.password.length < 12" class="modal__field-hint modal__field-hint--warn">
                {{ 12 - newUser.password.length }} more characters needed
              </span>
            </div>

            <!-- Role & Badge -->
            <div class="modal__row">
              <div class="form-group">
                <label class="form-label">Role *</label>
                <select v-model="newUser.role_name" class="form-input" required>
                  <option value="">— Select Role —</option>
                  <option value="admin">Admin</option>
                  <option value="investigator">Investigator</option>
                  <option value="officer">Officer</option>
                  <option value="analyst">Forensic Analyst</option>
                  <option value="auditor">Auditor</option>
                </select>
                <span class="modal__field-hint">{{ roleHint }}</span>
              </div>
              <div class="form-group">
                <label class="form-label">Badge Number</label>
                <input v-model="newUser.badge_number" class="form-input"
                  placeholder="e.g. OFF-1042" />
              </div>
            </div>

            <!-- Department -->
            <div class="form-group">
              <label class="form-label">Department</label>
              <input v-model="newUser.department" class="form-input"
                placeholder="e.g. Digital Forensics, Cybercrime Unit" />
            </div>

            <!-- Actions -->
            <div class="modal__actions">
              <button type="button" class="btn btn--ghost" @click="closeModal">Cancel</button>
              <button type="submit" class="btn btn--primary" :disabled="isCreating || !isFormValid">
                <span v-if="isCreating" class="modal__spinner" />
                {{ isCreating ? 'Creating…' : 'Create Account' }}
              </button>
            </div>
          </form>

          <!-- After success -->
          <div v-else class="modal__actions" style="margin-top:20px">
            <button class="btn btn--ghost" @click="createAnother">Create Another</button>
            <button class="btn btn--primary" @click="closeModal">Done</button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { api } from '../services/apiService'

// ── State ──────────────────────────────────────────────────────────────────
const users         = ref([])
const isLoading     = ref(false)
const search        = ref('')
const showCreateModal = ref(false)
const isCreating    = ref(false)
const createError   = ref('')
const createSuccess = ref(false)
const showPassword  = ref(false)
const createdCredentials = ref({})

const newUser = reactive({
  full_name:    '',
  email:        '',
  password:     '',
  role_name:    '',
  badge_number: '',
  department:   '',
})

// ── Role metadata ──────────────────────────────────────────────────────────
const roleDescriptions = [
  { name: 'admin',        desc: 'Full system access — manages users and cases' },
  { name: 'investigator', desc: 'Creates cases, uploads and transfers evidence' },
  { name: 'officer',      desc: 'Uploads evidence and views assigned cases' },
  { name: 'analyst',      desc: 'Forensic professional — read-only access for analysis' },
  { name: 'auditor',      desc: 'Compliance auditor — read-only access to all records' },
]

const roleHints = {
  admin:        'Full system access including user management.',
  investigator: 'Can create cases, upload evidence, and transfer custody.',
  officer:      'Can upload evidence and view cases they are assigned to.',
  analyst:      'Forensic analyst — can view and verify evidence, read-only.',
  auditor:      'Compliance role — read-only access to all cases and evidence.',
}

// ── Computed ───────────────────────────────────────────────────────────────
const filteredUsers = computed(() => {
  if (!search.value) return users.value
  const q = search.value.toLowerCase()
  return users.value.filter(u =>
    u.full_name.toLowerCase().includes(q) ||
    u.email.toLowerCase().includes(q) ||
    (u.role?.name || '').toLowerCase().includes(q) ||
    (u.department || '').toLowerCase().includes(q)
  )
})

const roleHint = computed(() => roleHints[newUser.role_name] || '')

const isFormValid = computed(() =>
  newUser.full_name.trim() &&
  newUser.email.trim() &&
  newUser.password.length >= 12 &&
  newUser.role_name
)

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(fetchUsers)

// ── Methods ────────────────────────────────────────────────────────────────
async function fetchUsers() {
  isLoading.value = true
  try {
    // Try to fetch users list — endpoint may need to be added to the backend
    const data = await api.get('/users/')
    users.value = data.items || data
  } catch {
    // Fallback: show current user only if list endpoint not available
    try {
      const me = await api.get('/auth/me')
      users.value = [me]
    } catch {}
  } finally {
    isLoading.value = false
  }
}

async function createUser() {
  createError.value  = ''
  isCreating.value   = true
  try {
    await api.post('/auth/register', { ...newUser })
    createdCredentials.value = { email: newUser.email, password: newUser.password }
    createSuccess.value = true
    await fetchUsers()
  } catch (err) {
    createError.value = err.message || 'Failed to create account. Please try again.'
  } finally {
    isCreating.value = false
  }
}

function generatePassword() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%'
  let pw = ''
  // Ensure at least one of each required type
  pw += 'ABCDEFGHJKLMNPQRSTUVWXYZ'[Math.floor(Math.random() * 24)]
  pw += 'abcdefghijkmnpqrstuvwxyz'[Math.floor(Math.random() * 24)]
  pw += '23456789'[Math.floor(Math.random() * 8)]
  pw += '!@#$%'[Math.floor(Math.random() * 5)]
  for (let i = pw.length; i < 14; i++) {
    pw += chars[Math.floor(Math.random() * chars.length)]
  }
  // Shuffle
  newUser.password = pw.split('').sort(() => Math.random() - 0.5).join('')
  showPassword.value = true
}

function createAnother() {
  Object.assign(newUser, {
    full_name: '', email: '', password: '',
    role_name: '', badge_number: '', department: '',
  })
  createSuccess.value = false
  createError.value   = ''
  showPassword.value  = false
}

function closeModal() {
  showCreateModal.value = false
  createAnother()
}

function roleBadge(role) {
  return { admin: 'tampered', investigator: 'pending', officer: 'open',
           analyst: 'verified', auditor: 'closed' }[role] || 'closed'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric'
  })
}
</script>

<style scoped>
.users-view { padding: 32px 24px; }

.users-view__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.users-view__sub { font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; }

/* Role legend */
.role-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
}

.role-legend__item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.role-legend__desc { color: var(--text-secondary); }

/* Table */
.users-view__table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;
}

.users-view__section-title { font-size: 1rem; }

.users-view__search {
  width: 260px;
  padding: 7px 12px;
  font-size: 0.78rem;
}

.users-view__loading,
.users-view__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.users-view__spinner {
  width: 26px; height: 26px;
  border: 2px solid var(--border);
  border-top-color: var(--amber);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.users-view__name  { color: var(--text-primary); font-weight: 500; }
.users-view__email { font-size: 0.78rem; color: var(--text-secondary); }
.users-view__dept  { font-size: 0.78rem; color: var(--text-secondary); }
.users-view__date  { font-size: 0.72rem; color: var(--text-muted); }
.users-view__badge-num { font-size: 0.72rem; color: var(--amber); }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.75);
  backdrop-filter: blur(6px);
  z-index: 9999;
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}

.modal { width: 100%; max-width: 580px; }

.modal__title {
  font-size: 1.1rem;
  margin-bottom: 4px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.modal__subtitle {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 20px;
  margin-top: 12px;
}

.modal__error {
  background: rgba(239,68,68,0.1);
  border: 1px solid rgba(239,68,68,0.3);
  color: var(--red-alert);
  padding: 10px 14px;
  border-radius: var(--radius);
  font-size: 0.78rem;
  margin-bottom: 16px;
}

.modal__success {
  background: rgba(16,185,129,0.1);
  border: 1px solid rgba(16,185,129,0.3);
  color: var(--green-ok);
  padding: 14px 16px;
  border-radius: var(--radius);
  font-size: 0.82rem;
  line-height: 1.8;
  margin-bottom: 16px;
}

.modal__form { display: flex; flex-direction: column; gap: 16px; }

.modal__row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.modal__pw-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.modal__pw-input { flex: 1; }

.modal__pw-toggle {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 12px;
  cursor: pointer;
  font-size: 1rem;
  flex-shrink: 0;
}

.modal__pw-gen {
  padding: 8px 12px;
  font-size: 0.72rem;
  flex-shrink: 0;
}

.modal__field-hint {
  font-size: 0.68rem;
  color: var(--text-muted);
  margin-top: 4px;
  display: block;
  font-style: italic;
}

.modal__field-hint--warn { color: var(--amber); }

.modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.modal__spinner {
  width: 13px; height: 13px;
  border: 2px solid rgba(0,0,0,0.3);
  border-top-color: var(--bg-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .modal__row { grid-template-columns: 1fr; }
  .users-view__search { width: 100%; }
}
</style>
