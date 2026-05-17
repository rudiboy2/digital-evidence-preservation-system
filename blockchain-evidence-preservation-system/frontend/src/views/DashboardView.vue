<template>
  <div class="dashboard container">
    <!-- Header -->
    <div class="dashboard__header fade-up">
      <div>
        <h1 class="dashboard__title">Operations Dashboard</h1>
        <p class="dashboard__sub">Active cases and evidence registry status</p>
      </div>
      <button
        v-if="canCreateCase"
        class="btn btn--primary"
        @click="showNewCase = true"
      >
        <span>+</span> New Case
      </button>
    </div>

    <!-- Stats Row -->
    <div class="dashboard__stats fade-up" style="animation-delay:0.1s">
      <div v-for="stat in stats" :key="stat.label" class="stat-card">
        <span class="stat-card__value">{{ stat.value }}</span>
        <span class="stat-card__label">{{ stat.label }}</span>
        <span class="stat-card__icon">{{ stat.icon }}</span>
      </div>
    </div>

    <!-- Cases Table -->
    <div class="card fade-up" style="animation-delay:0.2s">
      <div class="dashboard__table-header">
        <h2 class="dashboard__section-title">Cases</h2>
        <div class="dashboard__filters">
          <select v-model="statusFilter" class="form-input dashboard__select">
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="under_review">Under Review</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      <div v-if="isLoading" class="dashboard__loading">
        <div class="dashboard__spinner" />
      </div>

      <div v-else-if="cases.length === 0" class="dashboard__empty">
        <span>⬡</span>
        <p>No cases found. Create your first case to begin.</p>
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Case #</th>
            <th>Title</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Evidence</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in cases"
            :key="c.id"
            class="dashboard__row"
            @click="goToCase(c.id)"
          >
            <td><code class="dashboard__case-num">{{ c.case_number }}</code></td>
            <td class="dashboard__case-title">{{ c.title }}</td>
            <td>
              <span :class="['badge', `badge--${priorityClass(c.priority)}`]">
                {{ c.priority }}
              </span>
            </td>
            <td>
              <span :class="['badge', `badge--${c.status}`]">{{ c.status }}</span>
            </td>
            <td class="dashboard__evidence-count">{{ c.evidence_count ?? '—' }}</td>
            <td class="dashboard__date">{{ formatDate(c.created_at) }}</td>
            <td>
              <button class="btn btn--ghost dashboard__open-btn" @click.stop="goToCase(c.id)">
                Open →
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="dashboard__pagination">
        <button class="btn btn--ghost" :disabled="page === 1" @click="page--">‹ Prev</button>
        <span class="dashboard__page-info">Page {{ page }} of {{ totalPages }}</span>
        <button class="btn btn--ghost" :disabled="page === totalPages" @click="page++">Next ›</button>
      </div>
    </div>

    <!-- New Case Modal -->
    <Teleport to="body">
      <div v-if="showNewCase" class="modal-overlay" @click.self="showNewCase = false">
        <div class="modal card fade-up">
          <h2 class="modal__title">Create New Case</h2>
          <form class="modal__form" @submit.prevent="createCase">
            <div class="form-group">
              <label class="form-label">Case Title *</label>
              <input v-model="newCase.title" class="form-input" required placeholder="e.g. Digital Fraud Investigation Q3 2024" />
            </div>
            <div class="form-group">
              <label class="form-label">Description</label>
              <textarea v-model="newCase.description" class="form-input" rows="3" placeholder="Brief overview of the investigation…" />
            </div>
            <div class="modal__row">
              <div class="form-group">
                <label class="form-label">Priority</label>
                <select v-model="newCase.priority" class="form-input">
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Jurisdiction</label>
                <input v-model="newCase.jurisdiction" class="form-input" placeholder="Federal / State / Local" />
              </div>
            </div>
            <div class="modal__actions">
              <button type="button" class="btn btn--ghost" @click="showNewCase = false">Cancel</button>
              <button type="submit" class="btn btn--primary" :disabled="isCreating">
                {{ isCreating ? 'Creating…' : 'Create Case' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/apiService'

const router = useRouter()

// Role-based permissions
const userRole      = computed(() => localStorage.getItem('user_role') || '')
const canCreateCase = computed(() => ['admin', 'investigator'].includes(userRole.value))

const cases = ref([])
const isLoading = ref(false)
const isCreating = ref(false)
const showNewCase = ref(false)
const page = ref(1)
const totalPages = ref(1)
const totalCases = ref(0)
const statusFilter = ref('')

const stats = computed(() => [
  { label: 'Total Cases',    value: totalCases.value, icon: '📁' },
  { label: 'Open Cases',     value: cases.value.filter(c => c.status === 'open').length, icon: '🔓' },
  { label: 'Total Evidence', value: cases.value.reduce((s, c) => s + (c.evidence_count || 0), 0), icon: '⬡' },
  { label: 'Chain Status',   value: 'Online', icon: '⛓' },
])

const newCase = reactive({ title: '', description: '', priority: 'medium', jurisdiction: '' })

onMounted(fetchCases)
watch([page, statusFilter], fetchCases)

async function fetchCases() {
  isLoading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const params = new URLSearchParams({ page: page.value, page_size: 15 })
    if (statusFilter.value) params.append('status', statusFilter.value)

    const response = await fetch(`http://localhost:8000/api/v1/cases/?${params}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()
    cases.value      = data.items || []
    totalPages.value  = data.pages || 1
    totalCases.value  = data.total || 0

  } catch (err) {
    console.error('Failed to fetch cases:', err.message)
  } finally {
    isLoading.value = false
  }
}
async function createCase() {
  isCreating.value = true
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('http://localhost:8000/api/v1/cases/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        title:        newCase.title,
        description:  newCase.description,
        priority:     newCase.priority,
        jurisdiction: newCase.jurisdiction,
      })
    })

    if (!response.ok) {
      const err = await response.json()
      let msg = `Error: ${response.status}`
      if (typeof err.detail === 'string') msg = err.detail
      else if (Array.isArray(err.detail)) msg = err.detail.map(e => e.msg).join(', ')
      throw new Error(msg)
    }

    showNewCase.value = false
    Object.assign(newCase, { title: '', description: '', priority: 'medium', jurisdiction: '' })
    await fetchCases()

  } catch (err) {
    alert(err.message || 'Failed to create case.')
  } finally {
    isCreating.value = false
  }
}

function goToCase(id) { router.push({ name: 'case-detail', params: { id } }) }

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function priorityClass(p) {
  return { critical: 'tampered', high: 'tampered', medium: 'pending', low: 'closed' }[p] || 'closed'
}
</script>

<style scoped>
.dashboard { padding: 32px 24px; }

.dashboard__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 32px;
}

.dashboard__title { font-size: 2rem; }
.dashboard__sub { font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; }

/* Stats */
.dashboard__stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  overflow: hidden;
}

.stat-card__value {
  font-family: var(--font-display);
  font-size: 2.2rem;
  font-weight: 700;
  color: var(--amber);
  line-height: 1;
}

.stat-card__label {
  font-size: 0.68rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.stat-card__icon {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 2rem;
  opacity: 0.15;
}

/* Table area */
.dashboard__table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.dashboard__section-title { font-size: 1rem; }

.dashboard__select {
  padding: 6px 12px;
  font-size: 0.78rem;
  width: auto;
}

.dashboard__loading,
.dashboard__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.dashboard__spinner {
  width: 28px;
  height: 28px;
  border: 2px solid var(--border);
  border-top-color: var(--amber);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.dashboard__row { cursor: pointer; }

.dashboard__case-num {
  font-size: 0.72rem;
  color: var(--amber);
}

.dashboard__case-title {
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
}

.dashboard__date { font-size: 0.72rem; }

.dashboard__evidence-count { color: var(--amber); font-weight: 600; }

.dashboard__open-btn { padding: 4px 10px; font-size: 0.7rem; }

/* Pagination */
.dashboard__pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding-top: 20px;
  margin-top: 8px;
  border-top: 1px solid var(--border);
}

.dashboard__page-info {
  font-size: 0.72rem;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.modal {
  width: 100%;
  max-width: 520px;
}

.modal__title {
  font-size: 1.2rem;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.modal__form { display: flex; flex-direction: column; gap: 16px; }

.modal__row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
