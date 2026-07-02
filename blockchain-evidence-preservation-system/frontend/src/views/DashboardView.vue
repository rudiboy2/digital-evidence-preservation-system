<template>
  <div class="dashboard container">

    <!-- Header -->
    <div class="dashboard__header fade-up">
      <div>
        <h1 class="dashboard__title">Operations Dashboard</h1>
        <p class="dashboard__sub">Active cases and evidence registry status</p>
      </div>
      <button v-if="canCreateCase" class="btn btn--primary" @click="openModal">
        + New Case
      </button>
    </div>

    <!-- Stats -->
    <div class="dashboard__stats fade-up" style="animation-delay:0.1s">
      <div v-for="stat in stats" :key="stat.label" class="stat-card">
        <span class="stat-card__value">{{ stat.value }}</span>
        <span class="stat-card__label">{{ stat.label }}</span>
        <span class="stat-card__icon">{{ stat.icon }}</span>
      </div>
    </div>

    <!-- Status filter tabs -->
    <div class="dashboard__filter-tabs fade-up" style="animation-delay:0.15s">
      <button
        v-for="tab in statusTabs" :key="tab.value"
        :class="['filter-tab', statusFilter === tab.value ? 'filter-tab--active' : '']"
        @click="setFilter(tab.value)"
      >
        <span class="filter-tab__dot" :class="`filter-tab__dot--${tab.color}`" />
        {{ tab.label }}
        <span class="filter-tab__count">{{ tabCounts[tab.value] }}</span>
      </button>
    </div>

    <!-- Cases table -->
    <div class="card fade-up" style="animation-delay:0.2s">
      <div class="dashboard__table-header">
        <h2 class="dashboard__section-title">
          {{ currentTabLabel }} Cases
          <span class="dashboard__total">({{ filteredCases.length }})</span>
        </h2>
        <input v-model="searchQuery" class="form-input dashboard__search"
          placeholder="Search by title or case number…" />
      </div>

      <div v-if="isLoading" class="dashboard__loading">
        <div class="dashboard__spinner" />
      </div>

      <div v-else-if="filteredCases.length === 0" class="dashboard__empty">
        <span style="font-size:2rem">📁</span>
        <p>No {{ statusFilter || '' }} cases found.</p>
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
            <th>Closed</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in filteredCases" :key="c.id"
            class="dashboard__row"
            @click="goToCase(c.id)"
          >
            <td><code class="dashboard__case-num">{{ c.case_number }}</code></td>
            <td class="dashboard__case-title">{{ c.title }}</td>
            <td>
              <span :class="['badge', `badge--${priorityClass(c.priority)}`]">{{ c.priority }}</span>
            </td>
            <td>
              <span :class="['status-badge', `status-badge--${c.status}`]">
                {{ statusLabel(c.status) }}
              </span>
            </td>
            <td class="dashboard__evidence-count">{{ c.evidence_count ?? '—' }}</td>
            <td class="dashboard__date">{{ formatDate(c.created_at) }}</td>
            <td class="dashboard__date">{{ c.closed_at ? formatDate(c.closed_at) : '—' }}</td>
            <td>
              <div class="dashboard__row-actions" @click.stop>
                <button class="btn btn--ghost small-btn" @click.stop="goToCase(c.id)">
                  Open →
                </button>
                <!-- Advance status button — investigator and admin only -->
                <button
                  v-if="canAdvance && c.status === 'open'"
                  class="btn btn--ghost small-btn advance-btn"
                  :disabled="advancingId === c.id"
                  @click.stop="advanceStatus(c)"
                >
                  <span v-if="advancingId === c.id" class="btn-spin" />
                  {{ advancingId === c.id ? '…' : '→ Under Review' }}
                </button>
                <button
                  v-if="canAdvance && c.status === 'under_review'"
                  class="btn btn--ghost small-btn close-btn"
                  :disabled="advancingId === c.id"
                  @click.stop="advanceStatus(c)"
                >
                  <span v-if="advancingId === c.id" class="btn-spin" />
                  {{ advancingId === c.id ? '…' : '🔒 Close' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ================================================================ -->
    <!-- NEW CASE MODAL                                                    -->
    <!-- ================================================================ -->
    <Teleport to="body">
      <div v-if="showNewCase" class="nc-overlay" @click.self="closeModal" role="dialog" aria-modal="true">
        <div class="nc-modal">
          <div class="nc-header">
            <h2 class="nc-title">Create New Case</h2>
            <button class="nc-close" @click="closeModal">✕</button>
          </div>
          <div class="nc-body">
            <form id="nc-form" @submit.prevent="createCase">

              <p class="nc-section">📋 Case Information</p>
              <div class="form-group">
                <label class="form-label">Case Title <span class="nc-req">*</span></label>
                <input v-model="newCase.title" class="form-input" required
                  placeholder="e.g. Cybercrime Investigation — Dar es Salaam 2026" />
              </div>
              <div class="form-group">
                <label class="form-label">Description</label>
                <textarea v-model="newCase.description" class="form-input" rows="2"
                  placeholder="Brief overview of the investigation…" />
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
                  <input v-model="newCase.jurisdiction" class="form-input"
                    placeholder="e.g. Polisi Tanzania, Dodoma" />
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">Incident Date</label>
                <input v-model="newCase.incident_date" type="datetime-local" class="form-input" />
              </div>

              <p class="nc-section">⚖️ Legal Authority <span class="nc-section-sub">Criminal Procedure Act Cap 20</span></p>
              <div class="nc-row">
                <div class="form-group">
                  <label class="form-label">Warrant Number <span class="nc-req">*</span></label>
                  <input v-model="newCase.warrant_number" class="form-input" placeholder="e.g. HCT-W-2026-001" />
                </div>
                <div class="form-group">
                  <label class="form-label">OB Number <span class="nc-req">*</span></label>
                  <input v-model="newCase.ob_number" class="form-input" placeholder="e.g. OB-TPF-DSM-2026-4421" />
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">Issuing Court</label>
                <input v-model="newCase.warrant_issuing_court" class="form-input"
                  placeholder="e.g. Resident Magistrate Court, Dodoma" />
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

              <p class="nc-section">🏛 DPP &amp; Court Tracking</p>
              <div class="nc-row">
                <div class="form-group">
                  <label class="form-label">DPP Reference Number</label>
                  <input v-model="newCase.dpp_reference_number" class="form-input"
                    placeholder="e.g. DPP/CRM/2026/001" />
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
                <input v-model="newCase.external_reference" class="form-input"
                  placeholder="External agency reference number" />
              </div>

            </form>
          </div>
          <div class="nc-footer">
            <span class="nc-footer-hint"><span class="nc-req">*</span> Required for court admissibility</span>
            <div class="nc-footer-btns">
              <button type="button" class="btn btn--ghost" @click="closeModal">Cancel</button>
              <button type="submit" form="nc-form" class="btn btn--primary"
                :disabled="isCreating || !newCase.title.trim()">
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
const canAdvance    = computed(() => ['admin', 'investigator'].includes(userRole.value))

const allCases     = ref([])
const isLoading    = ref(false)
const isCreating   = ref(false)
const showNewCase  = ref(false)
const statusFilter = ref('')
const searchQuery  = ref('')
const advancingId  = ref(null)

const statusTabs = [
  { value: '',             label: 'All',          color: 'all'          },
  { value: 'open',         label: 'Open',         color: 'open'         },
  { value: 'under_review', label: 'Under Review', color: 'under_review' },
  { value: 'closed',       label: 'Closed',       color: 'closed'       },
]

const tabCounts = computed(() => {
  const c = { '': allCases.value.length }
  for (const tab of statusTabs.slice(1)) {
    c[tab.value] = allCases.value.filter(x => x.status === tab.value).length
  }
  return c
})

const currentTabLabel = computed(() =>
  statusTabs.find(t => t.value === statusFilter.value)?.label || 'All'
)

const filteredCases = computed(() => {
  let list = allCases.value
  if (statusFilter.value) list = list.filter(c => c.status === statusFilter.value)
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(c =>
      c.title.toLowerCase().includes(q) || c.case_number.toLowerCase().includes(q)
    )
  }
  return list
})

const stats = computed(() => [
  { label: 'Total Cases',    value: allCases.value.length,                                                     icon: '📁' },
  { label: 'Open',           value: allCases.value.filter(c => c.status === 'open').length,                    icon: '🔓' },
  { label: 'Under Review',   value: allCases.value.filter(c => c.status === 'under_review').length,            icon: '🔍' },
  { label: 'Closed',         value: allCases.value.filter(c => c.status === 'closed').length,                  icon: '🔒' },
  { label: 'Total Evidence', value: allCases.value.reduce((s, c) => s + (c.evidence_count || 0), 0),           icon: '⬡'  },
])

const newCase = reactive({
  title: '', description: '', priority: 'medium', jurisdiction: '', incident_date: '',
  warrant_number: '', ob_number: '', warrant_issuing_court: '',
  warrant_issue_date: '', warrant_expiry_date: '',
  dpp_reference_number: '', referring_agency: '', external_reference: '',
})

function resetForm() {
  Object.assign(newCase, {
    title: '', description: '', priority: 'medium', jurisdiction: '', incident_date: '',
    warrant_number: '', ob_number: '', warrant_issuing_court: '',
    warrant_issue_date: '', warrant_expiry_date: '',
    dpp_reference_number: '', referring_agency: '', external_reference: '',
  })
}

function openModal()  { showNewCase.value = true;  document.body.style.overflow = 'hidden' }
function closeModal() { showNewCase.value = false; document.body.style.overflow = ''       }
function setFilter(v) { statusFilter.value = v }
function onKey(e) { if (e.key === 'Escape' && showNewCase.value) closeModal() }

onMounted(() => { document.addEventListener('keydown', onKey); fetchCases() })
onUnmounted(() => { document.removeEventListener('keydown', onKey); document.body.style.overflow = '' })

// ── Auth fetch with token refresh ──────────────────────────────────────────
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
  if (response.status === 401) {
    const rt = localStorage.getItem('refresh_token')
    if (rt) {
      try {
        const rr = await fetch('http://localhost:8000/api/v1/auth/refresh', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: rt }),
        })
        if (rr.ok) {
          const tokens = await rr.json()
          localStorage.setItem('access_token',  tokens.access_token)
          localStorage.setItem('refresh_token', tokens.refresh_token)
          response = await fetch(url, { ...options, headers: makeHeaders() })
        }
      } catch {}
    }
    if (response.status === 401) {
      ;['access_token','refresh_token','user_role','user_name','user_email']
        .forEach(k => localStorage.removeItem(k))
      window.location.href = '/'
      return null
    }
  }
  return response
}

// ── Fetch ALL cases (no status filter — tabs are client-side) ─────────────
async function fetchCases() {
  isLoading.value = true
  try {
    const response = await authFetch(
      'http://localhost:8000/api/v1/cases/?page=1&page_size=200'
    )
    if (!response) return
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    allCases.value = data.items || []
  } catch (err) {
    console.error('fetchCases:', err.message)
  } finally {
    isLoading.value = false
  }
}

// ── Advance case status: open → under_review → closed ─────────────────────
async function advanceStatus(c) {
  const actionLabel = c.status === 'open' ? 'move to Under Review' : 'close this case'
  if (!confirm(`Are you sure you want to ${actionLabel}?\nThis is recorded in the audit trail.`)) return

  advancingId.value = c.id
  try {
    const response = await authFetch(
      `http://localhost:8000/api/v1/cases/${c.id}/advance-status`,
      { method: 'POST', body: JSON.stringify({ notes: null }) }
    )
    if (!response) return
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || `Error ${response.status}`)
    }
    const updated = await response.json()
    // Update the case in-memory so the tab counts and status badge
    // update immediately without a full re-fetch
    const idx = allCases.value.findIndex(x => x.id === c.id)
    if (idx !== -1) allCases.value[idx] = { ...allCases.value[idx], ...updated }
  } catch (err) {
    alert(err.message || 'Failed to update case status.')
  } finally {
    advancingId.value = null
  }
}

// ── Create case ────────────────────────────────────────────────────────────
async function createCase() {
  isCreating.value = true
  let caseCreated  = false
  try {
    const response = await authFetch('http://localhost:8000/api/v1/cases/', {
      method: 'POST', body: JSON.stringify({ ...newCase }),
    })
    if (!response) return
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      let msg = `Error ${response.status}`
      if (typeof err.detail === 'string') msg = err.detail
      else if (Array.isArray(err.detail)) msg = err.detail.map(e => e.msg || JSON.stringify(e)).join(', ')
      throw new Error(msg)
    }
    const created = await response.json()
    caseCreated = true
    closeModal()
    resetForm()
    // Add the new case to the local array immediately
    allCases.value.unshift(created)
  } catch (err) {
    if (!caseCreated) alert(err.message || 'Failed to create case.')
  } finally {
    isCreating.value = false
  }
}

function goToCase(id) { router.push({ name: 'case-detail', params: { id } }) }

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'numeric' })
}
function priorityClass(p) {
  return { critical:'tampered', high:'tampered', medium:'pending', low:'closed' }[p] || 'closed'
}
function statusLabel(s) {
  return { open:'Open', under_review:'Under Review', closed:'Closed', archived:'Archived' }[s] || s
}
</script>

<style scoped>
.dashboard { padding: 32px 24px; }
.dashboard__header { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:28px; }
.dashboard__title  { font-size:2rem; }
.dashboard__sub    { font-size:0.78rem; color:var(--text-muted); margin-top:4px; }

.dashboard__stats {
  display:grid; grid-template-columns:repeat(auto-fit, minmax(155px,1fr));
  gap:14px; margin-bottom:20px;
}
.stat-card {
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:var(--radius-lg); padding:18px 20px;
  display:flex; flex-direction:column; gap:4px;
  position:relative; overflow:hidden;
}
.stat-card__value { font-family:var(--font-display); font-size:2rem; font-weight:700; color:var(--amber); line-height:1; }
.stat-card__label { font-size:0.65rem; letter-spacing:0.1em; text-transform:uppercase; color:var(--text-muted); }
.stat-card__icon  { position:absolute; right:14px; top:50%; transform:translateY(-50%); font-size:1.8rem; opacity:0.13; }

/* Filter tabs */
.dashboard__filter-tabs { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:16px; }
.filter-tab {
  display:inline-flex; align-items:center; gap:7px; padding:7px 16px;
  background:var(--bg-card); border:1px solid var(--border); border-radius:20px;
  cursor:pointer; font-size:0.75rem; color:var(--text-secondary); transition:all 0.2s;
}
.filter-tab:hover { border-color:var(--amber); color:var(--amber); }
.filter-tab--active { background:var(--amber-glow); border-color:var(--amber); color:var(--amber); font-weight:600; }
.filter-tab__dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; }
.filter-tab__dot--all          { background:var(--text-muted); }
.filter-tab__dot--open         { background:var(--blue-info); box-shadow:0 0 5px var(--blue-info); }
.filter-tab__dot--under_review { background:var(--amber); box-shadow:0 0 5px var(--amber); }
.filter-tab__dot--closed       { background:#64748b; }
.filter-tab__count {
  background:var(--bg-secondary); border:1px solid var(--border);
  border-radius:10px; padding:0 7px; font-size:0.65rem; color:var(--text-muted); min-width:20px; text-align:center;
}
.filter-tab--active .filter-tab__count { background:var(--amber-glow); border-color:var(--border-amber); color:var(--amber); }

/* Table */
.dashboard__table-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; gap:12px; }
.dashboard__section-title { font-size:1rem; }
.dashboard__total { font-size:0.78rem; color:var(--text-muted); margin-left:6px; }
.dashboard__search { width:240px; padding:7px 12px; font-size:0.78rem; }
.dashboard__loading, .dashboard__empty {
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  gap:12px; padding:48px; color:var(--text-muted); font-size:0.82rem;
}
.dashboard__spinner { width:28px; height:28px; border:2px solid var(--border); border-top-color:var(--amber); border-radius:50%; animation:spin 0.8s linear infinite; }
.dashboard__row { cursor:pointer; }
.dashboard__case-num     { font-size:0.72rem; color:var(--amber); }
.dashboard__case-title   { max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--text-primary); }
.dashboard__date         { font-size:0.72rem; color:var(--text-secondary); }
.dashboard__evidence-count { color:var(--amber); font-weight:600; }

/* Row actions */
.dashboard__row-actions { display:flex; gap:6px; align-items:center; flex-wrap:wrap; }
.small-btn   { padding:4px 10px; font-size:0.68rem; white-space:nowrap; }
.advance-btn { color:var(--amber); border-color:rgba(245,158,11,0.3); }
.advance-btn:hover { background:rgba(245,158,11,0.1); }
.close-btn   { color:var(--red-alert); border-color:rgba(239,68,68,0.3); }
.close-btn:hover { background:rgba(239,68,68,0.1); }
.btn-spin {
  display:inline-block; width:10px; height:10px;
  border:2px solid rgba(255,255,255,0.3); border-top-color:currentColor;
  border-radius:50%; animation:spin 0.7s linear infinite; flex-shrink:0;
}

/* Status badges */
.status-badge {
  display:inline-flex; align-items:center;
  padding:3px 10px; border-radius:2px;
  font-size:0.68rem; font-weight:600; letter-spacing:0.08em;
  text-transform:uppercase; border:1px solid;
}
.status-badge--open         { background:rgba(59,130,246,0.12);  color:var(--blue-info);  border-color:rgba(59,130,246,0.3); }
.status-badge--under_review { background:rgba(245,158,11,0.12);  color:var(--amber);      border-color:rgba(245,158,11,0.3); }
.status-badge--closed       { background:rgba(100,116,139,0.12); color:#94a3b8;           border-color:rgba(100,116,139,0.3); }
.status-badge--archived     { background:rgba(71,85,105,0.12);   color:#64748b;           border-color:rgba(71,85,105,0.3); }

/* Modal */
.nc-overlay {
  position:fixed; inset:0; z-index:9999;
  background:rgba(0,0,0,0.75); backdrop-filter:blur(5px);
  overflow-y:auto; overflow-x:hidden;
  display:flex; justify-content:center; align-items:flex-start; padding:40px 16px;
}
@media (min-height:780px) { .nc-overlay { align-items:center; } }
.nc-modal {
  display:flex; flex-direction:column; width:100%; max-width:540px;
  max-height:calc(100vh - 80px);
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:var(--radius-lg); box-shadow:0 24px 64px rgba(0,0,0,0.65);
  animation:modalIn 0.2s ease both; overflow:hidden;
}
@keyframes modalIn { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
.nc-header {
  flex-shrink:0; display:flex; align-items:center; justify-content:space-between;
  padding:20px 24px 16px; border-bottom:1px solid var(--border); background:var(--bg-card);
}
.nc-title { font-family:var(--font-display); font-size:1.05rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; margin:0; }
.nc-close {
  background:none; border:1px solid var(--border); border-radius:var(--radius);
  color:var(--text-muted); cursor:pointer; font-size:0.8rem;
  width:28px; height:28px; display:flex; align-items:center; justify-content:center;
  transition:color 0.2s, border-color 0.2s;
}
.nc-close:hover { color:var(--red-alert); border-color:rgba(239,68,68,0.4); }
.nc-body {
  flex:1; overflow-y:auto; overflow-x:hidden; padding:20px 24px 4px;
  scrollbar-width:thin; scrollbar-color:var(--text-muted) transparent;
}
.nc-body::-webkit-scrollbar       { width:5px; }
.nc-body::-webkit-scrollbar-track { background:transparent; }
.nc-body::-webkit-scrollbar-thumb { background:var(--text-muted); border-radius:3px; }
.nc-body form { display:flex; flex-direction:column; gap:14px; padding-bottom:8px; }
.nc-section {
  font-size:0.68rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase;
  color:var(--amber); margin:6px 0 2px; padding-top:12px; border-top:1px solid var(--border);
}
.nc-body form .nc-section:first-child { border-top:none; padding-top:0; margin-top:0; }
.nc-section-sub { font-size:0.58rem; color:var(--text-muted); text-transform:none; letter-spacing:0; font-weight:400; margin-left:6px; }
.nc-row { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.nc-req { color:var(--red-alert); margin-left:1px; }
.nc-footer {
  flex-shrink:0; display:flex; align-items:center; justify-content:space-between; gap:12px;
  padding:14px 24px 18px; border-top:1px solid var(--border); background:var(--bg-card);
}
.nc-footer-hint { font-size:0.62rem; color:var(--text-muted); }
.nc-footer-btns { display:flex; gap:10px; align-items:center; flex-shrink:0; }
.nc-spinner {
  display:inline-block; width:12px; height:12px;
  border:2px solid rgba(0,0,0,0.25); border-top-color:var(--bg-primary);
  border-radius:50%; animation:spin 0.7s linear infinite; vertical-align:middle; margin-right:4px;
}
@media (max-width:580px) {
  .nc-overlay { padding:16px 10px; }
  .nc-modal   { max-height:calc(100vh - 32px); }
  .nc-header  { padding:14px 16px 12px; }
  .nc-body    { padding:16px 16px 4px; }
  .nc-footer  { padding:12px 16px 16px; flex-direction:column; align-items:stretch; }
  .nc-footer-hint { text-align:center; }
  .nc-footer-btns { flex-direction:column-reverse; }
  .nc-footer-btns .btn { width:100%; justify-content:center; }
  .nc-row { grid-template-columns:1fr; gap:12px; }
  .dashboard__search { width:100%; }
}
@keyframes spin { to { transform:rotate(360deg); } }
</style>
