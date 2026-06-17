<template>
  <div class="dashboard container">

    <!-- Header -->
    <div class="dashboard__header fade-up">
      <div>
        <h1 class="dashboard__title">Operations Dashboard</h1>
        <p class="dashboard__sub">Active cases and evidence registry status</p>
      </div>
      <button v-if="canCreateCase" class="btn btn--primary" @click="openModal">
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
        <select v-model="statusFilter" class="form-input dashboard__select">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="under_review">Under Review</option>
          <option value="closed">Closed</option>
        </select>
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
            v-for="c in cases" :key="c.id"
            class="dashboard__row"
            @click="goToCase(c.id)"
          >
            <td><code class="dashboard__case-num">{{ c.case_number }}</code></td>
            <td class="dashboard__case-title">{{ c.title }}</td>
            <td>
              <span :class="['badge', `badge--${priorityClass(c.priority)}`]">{{ c.priority }}</span>
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

      <div v-if="totalPages > 1" class="dashboard__pagination">
        <button class="btn btn--ghost" :disabled="page === 1" @click="page--">‹ Prev</button>
        <span class="dashboard__page-info">Page {{ page }} of {{ totalPages }}</span>
        <button class="btn btn--ghost" :disabled="page === totalPages" @click="page++">Next ›</button>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- NEW CASE MODAL                                                -->
    <!-- Structure: overlay (scrollable) > modal (flex-col) >         -->
    <!--   sticky header | scrollable body | sticky footer            -->
    <!-- ============================================================ -->
    <Teleport to="body">
      <div
        v-if="showNewCase"
        class="nc-overlay"
        @click.self="closeModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="nc-title"
      >
        <div class="nc-modal">

          <!-- Sticky title bar -->
          <div class="nc-header">
            <h2 id="nc-title" class="nc-title">Create New Case</h2>
            <button class="nc-close" @click="closeModal" aria-label="Close">✕</button>
          </div>

          <!-- Scrollable form area -->
          <div class="nc-body">
            <form id="nc-form" @submit.prevent="createCase">

              <!-- ── Section 1 ── -->
              <p class="nc-section">📋 Case Information</p>

              <div class="form-group">
                <label class="form-label">Case Title <span class="nc-req">*</span></label>
                <input
                  v-model="newCase.title"
                  class="form-input"
                  required
                  placeholder="e.g. Cybercrime Investigation — Dar es Salaam 2026"
                />
              </div>

              <div class="form-group">
                <label class="form-label">Description</label>
                <textarea
                  v-model="newCase.description"
                  class="form-input"
                  rows="2"
                  placeholder="Brief overview of the investigation…"
                />
              </div>

              <div class="nc-row">
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
                  <input
                    v-model="newCase.jurisdiction"
                    class="form-input"
                    placeholder="e.g. Polisi Tanzania, Dodoma"
                  />
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">Incident Date</label>
                <input v-model="newCase.incident_date" type="datetime-local" class="form-input" />
              </div>

              <!-- ── Section 2 ── -->
              <p class="nc-section">⚖️ Legal Authority <span class="nc-section-sub">Criminal Procedure Act Cap 20</span></p>

              <div class="nc-row">
                <div class="form-group">
                  <label class="form-label">Warrant Number <span class="nc-req">*</span></label>
                  <input
                    v-model="newCase.warrant_number"
                    class="form-input"
                    placeholder="e.g. HCT-W-2026-001"
                  />
                </div>
                <div class="form-group">
                  <label class="form-label">OB Number <span class="nc-req">*</span></label>
                  <input
                    v-model="newCase.ob_number"
                    class="form-input"
                    placeholder="e.g. OB-TPF-DSM-2026-4421"
                  />
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">Issuing Court</label>
                <input
                  v-model="newCase.warrant_issuing_court"
                  class="form-input"
                  placeholder="e.g. Resident Magistrate Court, Dodoma"
                />
              </div>

              <div class="nc-row">
                <div class="form-group">
                  <label class="form-label">Warrant Issue Date</label>
                  <input v-model="newCase.warrant_issue_date" type="date" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">Warrant Expiry Date</label>
                  <input v-model="newCase.warrant_expiry_date" type="date" class="form-input" />
                </div>
              </div>

              <!-- ── Section 3 ── -->
              <p class="nc-section">🏛 DPP &amp; Court Tracking</p>

              <div class="nc-row">
                <div class="form-group">
                  <label class="form-label">DPP Reference Number</label>
                  <input
                    v-model="newCase.dpp_reference_number"
                    class="form-input"
                    placeholder="e.g. DPP/CRM/2026/001"
                  />
                </div>
                <div class="form-group">
                  <label class="form-label">Referring Agency</label>
                  <select v-model="newCase.referring_agency" class="form-input">
                    <option value="">— Select Agency —</option>
                    <option value="TPF">TPF (Tanzania Police Force)</option>
                    <option value="PCCB">PCCB (Anti-Corruption Bureau)</option>
                    <option value="TCRA">TCRA</option>
                    <option value="FIU">FIU (Financial Intelligence Unit)</option>
                    <option value="INTERPOL">INTERPOL NCB Tanzania</option>
                    <option value="TRA">TRA (Revenue Authority)</option>
                  </select>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">External Reference Number</label>
                <input
                  v-model="newCase.external_reference"
                  class="form-input"
                  placeholder="External agency reference number"
                />
              </div>

            </form>
          </div>
          <!-- END .nc-body -->

          <!-- Sticky action footer -->
          <div class="nc-footer">
            <span class="nc-footer-hint"><span class="nc-req">*</span> Required for court admissibility</span>
            <div class="nc-footer-btns">
              <button type="button" class="btn btn--ghost" @click="closeModal">Cancel</button>
              <button
                type="submit"
                form="nc-form"
                class="btn btn--primary"
                :disabled="isCreating || !newCase.title.trim()"
              >
                <span v-if="isCreating" class="nc-spinner" />
                {{ isCreating ? 'Creating…' : 'Create Case' }}
              </button>
            </div>
          </div>

        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const userRole      = computed(() => localStorage.getItem('user_role') || '')
const canCreateCase = computed(() => ['admin', 'investigator'].includes(userRole.value))

const cases        = ref([])
const isLoading    = ref(false)
const isCreating   = ref(false)
const showNewCase  = ref(false)
const page         = ref(1)
const totalPages   = ref(1)
const totalCases   = ref(0)
const statusFilter = ref('')

const stats = computed(() => [
  { label: 'Total Cases',    value: totalCases.value,                                              icon: '📁' },
  { label: 'Open Cases',     value: cases.value.filter(c => c.status === 'open').length,           icon: '🔓' },
  { label: 'Total Evidence', value: cases.value.reduce((s, c) => s + (c.evidence_count || 0), 0), icon: '⬡'  },
  { label: 'Chain Status',   value: 'Online',                                                      icon: '⛓'  },
])

const newCase = reactive({
  title: '', description: '', priority: 'medium', jurisdiction: '',
  incident_date: '',
  warrant_number: '', ob_number: '', warrant_issuing_court: '',
  warrant_issue_date: '', warrant_expiry_date: '',
  dpp_reference_number: '', referring_agency: '', external_reference: '',
})

function resetForm() {
  Object.assign(newCase, {
    title: '', description: '', priority: 'medium', jurisdiction: '',
    incident_date: '',
    warrant_number: '', ob_number: '', warrant_issuing_court: '',
    warrant_issue_date: '', warrant_expiry_date: '',
    dpp_reference_number: '', referring_agency: '', external_reference: '',
  })
}

// ── Modal helpers ──────────────────────────────────────────────────────────
function openModal() {
  showNewCase.value = true
  document.body.style.overflow = 'hidden'
}
function closeModal() {
  showNewCase.value = false
  document.body.style.overflow = ''
}

function onKey(e) {
  if (e.key === 'Escape' && showNewCase.value) closeModal()
}

onMounted(() => {
  document.addEventListener('keydown', onKey)
  fetchCases()
})
onUnmounted(() => {
  document.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})

watch([page, statusFilter], fetchCases)

// ── Auth fetch with auto token-refresh ────────────────────────────────────
async function authFetch(url, options = {}) {
  const makeHeaders = () => {
    const token = localStorage.getItem('access_token')
    const h = { 'Content-Type': 'application/json', ...(options.headers || {}) }
    if (token) h['Authorization'] = `Bearer ${token}`
    return h
  }

  let response
  try {
    response = await fetch(url, { ...options, headers: makeHeaders() })
  } catch {
    throw new Error('Cannot reach the server. Check your connection.')
  }

  // Try silent token refresh on 401
  if (response.status === 401) {
    const rt = localStorage.getItem('refresh_token')
    if (rt) {
      try {
        const rr = await fetch('http://localhost:8000/api/v1/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: rt }),
        })
        if (rr.ok) {
          const tokens = await rr.json()
          localStorage.setItem('access_token',  tokens.access_token)
          localStorage.setItem('refresh_token', tokens.refresh_token)
          // Retry with new token
          response = await fetch(url, { ...options, headers: makeHeaders() })
        }
      } catch {}
    }
    // Still 401 after refresh — redirect to login
    if (response.status === 401) {
      ;['access_token','refresh_token','user_role','user_name','user_email']
        .forEach(k => localStorage.removeItem(k))
      window.location.href = '/'
      return null
    }
  }

  return response
}

// ── Data functions ─────────────────────────────────────────────────────────
async function fetchCases() {
  isLoading.value = true
  try {
    const params = new URLSearchParams({ page: page.value, page_size: 15 })
    if (statusFilter.value) params.append('status', statusFilter.value)

    const response = await authFetch(`http://localhost:8000/api/v1/cases/?${params}`)
    if (!response) return

    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data      = await response.json()
    cases.value      = data.items || []
    totalPages.value  = data.pages || 1
    totalCases.value  = data.total || 0
  } catch (err) {
    console.error('fetchCases:', err.message)
  } finally {
    isLoading.value = false
  }
}

async function createCase() {
  isCreating.value = true
  let caseCreated = false

  try {
    const response = await authFetch('http://localhost:8000/api/v1/cases/', {
      method: 'POST',
      body: JSON.stringify({ ...newCase }),
    })

    // Redirected to login
    if (!response) return

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      let msg = `Error ${response.status}`
      if (typeof err.detail === 'string')  msg = err.detail
      else if (Array.isArray(err.detail))  msg = err.detail.map(e => e.msg || JSON.stringify(e)).join(', ')
      throw new Error(msg)
    }

    // ✅ Case created — close modal and reset form immediately
    caseCreated = true
    closeModal()
    resetForm()

  } catch (err) {
    // Only show error if case was NOT created
    if (!caseCreated) {
      alert(err.message || 'Failed to create case.')
    }
  } finally {
    isCreating.value = false
  }

  // Refresh list silently — never block or alert on this
  if (caseCreated) {
    fetchCases().catch(() => {
      // Silent fail — page refresh will show the new case
    })
  }
}

function goToCase(id)  { router.push({ name: 'case-detail', params: { id } }) }

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function priorityClass(p) {
  return { critical: 'tampered', high: 'tampered', medium: 'pending', low: 'closed' }[p] || 'closed'
}
</script>

<style scoped>
/* ── Dashboard ──────────────────────────────────────────────────────────── */
.dashboard { padding: 32px 24px; }

.dashboard__header {
  display: flex; align-items: flex-start;
  justify-content: space-between; margin-bottom: 32px;
}
.dashboard__title { font-size: 2rem; }
.dashboard__sub   { font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; }

.dashboard__stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px; margin-bottom: 28px;
}
.stat-card {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 20px;
  display: flex; flex-direction: column; gap: 4px;
  position: relative; overflow: hidden;
}
.stat-card__value {
  font-family: var(--font-display); font-size: 2.2rem;
  font-weight: 700; color: var(--amber); line-height: 1;
}
.stat-card__label {
  font-size: 0.68rem; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--text-muted);
}
.stat-card__icon {
  position: absolute; right: 16px; top: 50%;
  transform: translateY(-50%); font-size: 2rem; opacity: 0.15;
}

.dashboard__table-header {
  display: flex; align-items: center;
  justify-content: space-between; margin-bottom: 20px;
}
.dashboard__section-title { font-size: 1rem; }
.dashboard__select { padding: 6px 12px; font-size: 0.78rem; width: auto; }

.dashboard__loading,
.dashboard__empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 12px; padding: 48px;
  color: var(--text-muted); font-size: 0.82rem;
}
.dashboard__spinner {
  width: 28px; height: 28px;
  border: 2px solid var(--border); border-top-color: var(--amber);
  border-radius: 50%; animation: spin 0.8s linear infinite;
}

.dashboard__row          { cursor: pointer; }
.dashboard__case-num     { font-size: 0.72rem; color: var(--amber); }
.dashboard__case-title   { max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-primary); }
.dashboard__date         { font-size: 0.72rem; }
.dashboard__evidence-count { color: var(--amber); font-weight: 600; }
.dashboard__open-btn     { padding: 4px 10px; font-size: 0.7rem; }

.dashboard__pagination {
  display: flex; align-items: center; justify-content: center;
  gap: 16px; padding-top: 20px; margin-top: 8px;
  border-top: 1px solid var(--border);
}
.dashboard__page-info { font-size: 0.72rem; color: var(--text-muted); letter-spacing: 0.06em; }

/* ── Modal overlay ──────────────────────────────────────────────────────── */
/*
 * KEY RULES:
 *   1. overlay = fixed fullscreen, itself scrollable (overflow-y: auto)
 *      so the modal is reachable on tiny screens.
 *   2. .nc-modal = flex column, max-height = viewport minus padding so it
 *      never overflows; only .nc-body is scrollable.
 *   3. .nc-header and .nc-footer are flex-shrink:0 — always visible.
 */
.nc-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(5px);

  /* scrollable wrapper so modal is reachable even on very short screens */
  overflow-y: auto;
  overflow-x: hidden;

  /* centre the modal */
  display: flex;
  justify-content: center;
  align-items: flex-start;          /* top-align; centred via padding  */
  padding: 40px 16px 40px;
}

/* On tall screens: vertically centre */
@media (min-height: 780px) {
  .nc-overlay { align-items: center; }
}

/* ── Modal box ──────────────────────────────────────────────────────────── */
.nc-modal {
  /* three-row flex: header | body | footer */
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 540px;

  /* never taller than viewport minus overlay padding */
  max-height: calc(100vh - 80px);

  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.65);
  animation: modalIn 0.2s ease both;
  overflow: hidden;               /* clip rounded corners on children */
}

@keyframes modalIn {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0);    }
}

/* ── Sticky header ──────────────────────────────────────────────────────── */
.nc-header {
  flex-shrink: 0;                 /* never shrinks — always visible */
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-card);
}

.nc-title {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-primary);
  margin: 0;
}

.nc-close {
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.8rem;
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: color 0.2s, border-color 0.2s;
}
.nc-close:hover { color: var(--red-alert); border-color: rgba(239,68,68,0.4); }

/* ── Scrollable body ────────────────────────────────────────────────────── */
.nc-body {
  flex: 1;                        /* fills all space between header and footer */
  overflow-y: auto;               /* ← THIS is what makes the form scroll      */
  overflow-x: hidden;
  padding: 20px 24px 4px;

  /* thin custom scrollbar */
  scrollbar-width: thin;
  scrollbar-color: var(--text-muted) transparent;
}
.nc-body::-webkit-scrollbar        { width: 5px; }
.nc-body::-webkit-scrollbar-track  { background: transparent; }
.nc-body::-webkit-scrollbar-thumb  { background: var(--text-muted); border-radius: 3px; }

/* form inside body */
.nc-body form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-bottom: 8px;            /* small gap above footer */
}

/* section labels */
.nc-section {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--amber);
  margin: 6px 0 2px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}
/* first section: no top border/padding */
.nc-body form .nc-section:first-child {
  border-top: none;
  padding-top: 0;
  margin-top: 0;
}

.nc-section-sub {
  font-size: 0.58rem;
  color: var(--text-muted);
  text-transform: none;
  letter-spacing: 0;
  font-weight: 400;
  margin-left: 6px;
}

/* two-column row */
.nc-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

/* required star */
.nc-req { color: var(--red-alert); margin-left: 1px; }

/* ── Sticky footer ──────────────────────────────────────────────────────── */
.nc-footer {
  flex-shrink: 0;                 /* never shrinks — always visible */
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 24px 18px;
  border-top: 1px solid var(--border);
  background: var(--bg-card);
}

.nc-footer-hint {
  font-size: 0.62rem;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

.nc-footer-btns {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
}

/* button spinner */
.nc-spinner {
  display: inline-block;
  width: 12px; height: 12px;
  border: 2px solid rgba(0, 0, 0, 0.25);
  border-top-color: var(--bg-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  vertical-align: middle;
  margin-right: 4px;
}

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 580px) {
  .nc-overlay  { padding: 16px 10px; align-items: flex-start; }
  .nc-modal    { max-height: calc(100vh - 32px); }
  .nc-header   { padding: 14px 16px 12px; }
  .nc-body     { padding: 16px 16px 4px; }
  .nc-footer   {
    padding: 12px 16px 16px;
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .nc-footer-hint { text-align: center; }
  .nc-footer-btns {
    flex-direction: column-reverse;
    gap: 8px;
  }
  .nc-footer-btns .btn { width: 100%; justify-content: center; }
  .nc-row { grid-template-columns: 1fr; gap: 12px; }
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
