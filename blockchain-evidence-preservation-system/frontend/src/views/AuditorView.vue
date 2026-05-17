<template>
  <div class="auditor-view container">

    <!-- Header -->
    <div class="auditor-view__header fade-up">
      <div>
        <h1>Compliance Audit Dashboard</h1>
        <p class="auditor-view__sub">
          Full read-only access to all cases, evidence, and audit logs. Zero write permissions.
        </p>
      </div>
      <div class="auditor-view__badge">
        <span class="badge badge--closed">📋 Auditor — Read Only</span>
      </div>
    </div>

    <!-- Stats -->
    <div class="auditor-view__stats fade-up" style="animation-delay:0.05s">
      <div class="astat">
        <span class="astat__val">{{ stats.totalCases }}</span>
        <span class="astat__label">Total Cases</span>
      </div>
      <div class="astat">
        <span class="astat__val">{{ stats.totalEvidence }}</span>
        <span class="astat__label">Evidence Items</span>
      </div>
      <div class="astat">
        <span class="astat__val">{{ stats.totalLogs }}</span>
        <span class="astat__label">Audit Log Entries</span>
      </div>
      <div class="astat">
        <span class="astat__val">{{ stats.openCases }}</span>
        <span class="astat__label">Open Cases</span>
      </div>
    </div>

    <!-- Tabs -->
    <div class="auditor-view__tabs fade-up" style="animation-delay:0.1s">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab-btn', activeTab === tab.id ? 'tab-btn--active' : '']"
        @click="activeTab = tab.id"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </div>

    <!-- ── ALL CASES TAB ─────────────────────────────────────────────── -->
    <div v-if="activeTab === 'cases'" class="card fade-up">
      <div class="tab-header">
        <h2>All Cases</h2>
        <input v-model="caseSearch" class="form-input tab-search" placeholder="Search cases…" />
      </div>

      <div v-if="isLoadingCases" class="tab-loading">
        <div class="spinner" /> Loading cases…
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Case #</th>
            <th>Title</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Created By</th>
            <th>Evidence</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in filteredCases" :key="c.id">
            <td><code class="amber-text">{{ c.case_number }}</code></td>
            <td class="bold-text">{{ c.title }}</td>
            <td><span :class="['badge', `badge--${c.status}`]">{{ c.status }}</span></td>
            <td><span :class="['badge', priorityBadge(c.priority)]">{{ c.priority }}</span></td>
            <td class="muted-text">{{ c.created_by }}</td>
            <td class="amber-text">{{ c.evidence_count ?? '—' }}</td>
            <td class="muted-text">{{ formatDate(c.created_at) }}</td>
            <td>
              <button class="btn btn--ghost small-btn" @click="viewCaseAudit(c)">
                Audit Log →
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── ALL EVIDENCE TAB ──────────────────────────────────────────── -->
    <div v-if="activeTab === 'evidence'" class="card fade-up">
      <div class="tab-header">
        <h2>All Evidence</h2>
        <input v-model="evidenceSearch" class="form-input tab-search" placeholder="Search by filename or hash…" />
      </div>

      <div v-if="isLoadingEvidence" class="tab-loading">
        <div class="spinner" /> Loading evidence…
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>File</th>
            <th>Type</th>
            <th>SHA-256</th>
            <th>Status</th>
            <th>Case</th>
            <th>Uploaded</th>
            <th>Blockchain TX</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ev in filteredEvidence" :key="ev.id">
            <td>
              <span class="ev-icon">{{ fileIcon(ev.mime_type) }}</span>
              {{ ev.file_name }}
            </td>
            <td class="muted-text">{{ ev.evidence_type }}</td>
            <td><code class="amber-text hash-text">{{ ev.sha256_hash?.slice(0,16) }}…</code></td>
            <td><span :class="['badge', `badge--${ev.status}`]">{{ ev.status }}</span></td>
            <td><code class="amber-text small-text">{{ ev.case_id?.slice(0,8) }}…</code></td>
            <td class="muted-text">{{ formatDate(ev.created_at) }}</td>
            <td>
              <span v-if="ev.blockchain_tx_hash" class="chain-confirmed">⬡ Confirmed</span>
              <span v-else class="chain-pending">⏳ Pending</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── AUDIT LOG TAB ─────────────────────────────────────────────── -->
    <div v-if="activeTab === 'audit'" class="card fade-up">
      <div class="tab-header">
        <h2>
          {{ selectedAuditCase ? `Audit Log — ${selectedAuditCase.case_number}` : 'Select a case to view audit log' }}
        </h2>
        <div style="display:flex;gap:10px;align-items:center">
          <select v-model="auditCaseId" class="form-input tab-search" @change="loadAuditLog">
            <option value="">— Select Case —</option>
            <option v-for="c in allCases" :key="c.id" :value="c.id">
              {{ c.case_number }} — {{ c.title }}
            </option>
          </select>
          <select v-model="auditActionFilter" class="form-input tab-search" style="width:160px">
            <option value="">All Actions</option>
            <option v-for="a in auditActions" :key="a" :value="a">{{ a }}</option>
          </select>
        </div>
      </div>

      <div v-if="isLoadingAudit" class="tab-loading">
        <div class="spinner" /> Loading audit log…
      </div>

      <div v-else-if="!auditCaseId" class="tab-empty">
        Select a case above to view its full audit trail.
      </div>

      <div v-else-if="filteredAuditLogs.length === 0" class="tab-empty">
        No audit entries found.
      </div>

      <div v-else class="audit-timeline">
        <div v-for="log in filteredAuditLogs" :key="log.id" class="audit-entry">
          <!-- Action dot -->
          <div :class="['audit-entry__dot', `audit-dot--${log.action}`]">
            {{ actionIcon(log.action) }}
          </div>

          <!-- Content -->
          <div class="audit-entry__content">
            <div class="audit-entry__top">
              <span :class="['audit-badge', `audit-badge--${log.action}`]">
                {{ log.action.replace('_', ' ').toUpperCase() }}
              </span>
              <span class="audit-entry__role">{{ log.performed_by_role || 'unknown' }}</span>
              <span class="audit-entry__time">{{ formatDateFull(log.timestamp) }}</span>
            </div>

            <div class="audit-entry__details">
              <span v-if="log.evidence_id" class="audit-detail">
                Evidence: <code>{{ log.evidence_id?.slice(0,12) }}…</code>
              </span>
              <span v-if="log.performed_by" class="audit-detail">
                User: <code>{{ log.performed_by?.slice(0,12) }}…</code>
              </span>
              <span v-if="log.ip_address" class="audit-detail">
                IP: <code>{{ log.ip_address }}</code>
              </span>
            </div>

            <p v-if="log.notes" class="audit-entry__notes">{{ log.notes }}</p>

            <div v-if="log.blockchain_tx_hash" class="audit-entry__tx">
              ⬡ TX: <code>{{ log.blockchain_tx_hash }}</code>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../services/apiService'

const activeTab    = ref('cases')
const allCases     = ref([])
const allEvidence  = ref([])
const auditLogs    = ref([])
const caseSearch     = ref('')
const evidenceSearch = ref('')
const auditCaseId    = ref('')
const auditActionFilter = ref('')
const selectedAuditCase = ref(null)
const isLoadingCases    = ref(true)
const isLoadingEvidence = ref(false)
const isLoadingAudit    = ref(false)

const stats = ref({ totalCases: 0, totalEvidence: 0, totalLogs: 0, openCases: 0 })

const tabs = [
  { id: 'cases',    label: 'All Cases',    icon: '📁' },
  { id: 'evidence', label: 'All Evidence', icon: '⬡'  },
  { id: 'audit',    label: 'Audit Logs',   icon: '📋' },
]

const auditActions = [
  'case_created', 'case_viewed', 'case_updated', 'case_closed',
  'officer_assigned', 'analyst_assigned',
  'upload', 'view', 'download', 'verify', 'custody_transfer',
  'report_submission', 'analysis',
]

onMounted(async () => {
  await loadCases()
})

watch(activeTab, async (tab) => {
  if (tab === 'evidence' && allEvidence.value.length === 0) await loadAllEvidence()
})

async function loadCases() {
  isLoadingCases.value = true
  try {
    const data = await api.get('/cases/?page_size=100')
    allCases.value = data.items || []
    stats.value.totalCases = data.total || allCases.value.length
    stats.value.openCases  = allCases.value.filter(c => c.status === 'open').length
  } catch {}
  isLoadingCases.value = false
}

async function loadAllEvidence() {
  isLoadingEvidence.value = true
  try {
    // Collect evidence from all cases
    const allEv = []
    for (const c of allCases.value) {
      try {
        const data = await api.get(`/evidence/case/${c.id}?page_size=100`)
        allEv.push(...(data.items || []))
      } catch {}
    }
    allEvidence.value = allEv
    stats.value.totalEvidence = allEv.length
  } catch {}
  isLoadingEvidence.value = false
}

async function loadAuditLog() {
  if (!auditCaseId.value) return
  selectedAuditCase.value = allCases.value.find(c => c.id === auditCaseId.value)
  isLoadingAudit.value = true
  try {
    const data = await api.get(`/cases/${auditCaseId.value}/audit-log?page_size=200`)
    auditLogs.value = data.logs || []
    stats.value.totalLogs = data.total || auditLogs.value.length
  } catch {}
  isLoadingAudit.value = false
}

function viewCaseAudit(c) {
  activeTab.value   = 'audit'
  auditCaseId.value = c.id
  loadAuditLog()
}

// ── Computed filters ───────────────────────────────────────────────────────
const filteredCases = computed(() => {
  if (!caseSearch.value) return allCases.value
  const q = caseSearch.value.toLowerCase()
  return allCases.value.filter(c =>
    c.case_number.toLowerCase().includes(q) ||
    c.title.toLowerCase().includes(q)
  )
})

const filteredEvidence = computed(() => {
  if (!evidenceSearch.value) return allEvidence.value
  const q = evidenceSearch.value.toLowerCase()
  return allEvidence.value.filter(e =>
    e.file_name.toLowerCase().includes(q) ||
    (e.sha256_hash || '').toLowerCase().includes(q)
  )
})

const filteredAuditLogs = computed(() => {
  if (!auditActionFilter.value) return auditLogs.value
  return auditLogs.value.filter(l => l.action === auditActionFilter.value)
})

// ── Helpers ────────────────────────────────────────────────────────────────
function fileIcon(mime = '') {
  if (mime.startsWith('image/')) return '🖼'
  if (mime.startsWith('video/')) return '🎥'
  if (mime.startsWith('audio/')) return '🎙'
  if (mime.includes('pdf'))      return '📄'
  return '💾'
}

function actionIcon(action = '') {
  const map = {
    upload: '⬆', view: '👁', download: '⬇',
    verify: '✓', custody_transfer: '↔',
    case_created: '📁', case_closed: '🔒',
    officer_assigned: '👮', analyst_assigned: '🔬',
    report_submission: '📋', analysis: '🔍',
  }
  return map[action] || '⬡'
}

function priorityBadge(p) {
  return { critical:'badge--tampered', high:'badge--tampered',
           medium:'badge--pending',    low:'badge--closed' }[p] || 'badge--closed'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    day:'2-digit', month:'short', year:'numeric'
  })
}

function formatDateFull(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', {
    day:'2-digit', month:'short', year:'numeric',
    hour:'2-digit', minute:'2-digit', second:'2-digit'
  })
}
</script>

<style scoped>
.auditor-view { padding: 32px 24px; }

.auditor-view__header {
  display: flex; justify-content: space-between;
  align-items: flex-start; margin-bottom: 24px;
}
.auditor-view__sub { font-size:0.78rem; color:var(--text-muted); margin-top:4px; }
.auditor-view__badge { padding-top: 8px; }

/* Stats */
.auditor-view__stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.astat {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 18px 20px;
  display: flex; flex-direction: column; gap: 4px;
}
.astat__val {
  font-family: var(--font-display); font-size: 2.2rem;
  font-weight: 700; color: var(--amber); line-height: 1;
}
.astat__label {
  font-size: 0.65rem; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--text-muted);
}

/* Tabs */
.auditor-view__tabs {
  display: flex; gap: 4px; margin-bottom: 20px;
  border-bottom: 1px solid var(--border); padding-bottom: 0;
}
.tab-btn {
  background: transparent; border: none;
  font-family: var(--font-display); font-size: 0.82rem;
  font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted); padding: 10px 20px;
  cursor: pointer; border-bottom: 2px solid transparent;
  transition: all 0.2s;
}
.tab-btn:hover { color: var(--text-primary); }
.tab-btn--active {
  color: var(--amber);
  border-bottom-color: var(--amber);
}

/* Tab content */
.tab-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px;
}
.tab-header h2 { font-size: 1rem; }
.tab-search { width: 220px; padding: 7px 12px; font-size: 0.78rem; }
.tab-loading, .tab-empty {
  display: flex; align-items: center; gap: 10px;
  padding: 40px; color: var(--text-muted); font-size: 0.82rem;
  justify-content: center;
}
.spinner {
  width: 24px; height: 24px;
  border: 2px solid var(--border);
  border-top-color: var(--amber);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Table helpers */
.amber-text { color: var(--amber); }
.bold-text  { color: var(--text-primary); font-weight: 500; }
.muted-text { color: var(--text-secondary); font-size: 0.78rem; }
.hash-text  { font-size: 0.7rem; }
.small-text { font-size: 0.7rem; }
.small-btn  { padding: 4px 10px; font-size: 0.7rem; }
.ev-icon    { margin-right: 6px; }

.chain-confirmed { color: var(--green-ok); font-size: 0.72rem; }
.chain-pending   { color: var(--text-muted); font-size: 0.72rem; }

/* Audit timeline */
.audit-timeline { display: flex; flex-direction: column; gap: 0; max-height: 600px; overflow-y: auto; }
.audit-entry {
  display: flex; gap: 14px;
  padding: 14px 8px;
  border-bottom: 1px solid var(--border);
}
.audit-entry:last-child { border-bottom: none; }

.audit-entry__dot {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.9rem; flex-shrink: 0;
  background: var(--bg-secondary); border: 1px solid var(--border);
}

.audit-dot--upload            { border-color: var(--amber);     color: var(--amber); }
.audit-dot--download          { border-color: #a78bfa;          color: #a78bfa; }
.audit-dot--view              { border-color: var(--text-muted); }
.audit-dot--verify            { border-color: var(--green-ok);  color: var(--green-ok); }
.audit-dot--custody_transfer  { border-color: var(--blue-info); color: var(--blue-info); }
.audit-dot--case_created      { border-color: var(--amber);     color: var(--amber); }
.audit-dot--case_closed       { border-color: var(--red-alert); color: var(--red-alert); }
.audit-dot--officer_assigned  { border-color: var(--blue-info); color: var(--blue-info); }
.audit-dot--analyst_assigned  { border-color: var(--green-ok);  color: var(--green-ok); }
.audit-dot--report_submission { border-color: var(--green-ok);  color: var(--green-ok); }

.audit-entry__content { flex: 1; }
.audit-entry__top {
  display: flex; align-items: center; gap: 10px; margin-bottom: 6px; flex-wrap: wrap;
}

.audit-badge {
  font-family: var(--font-display); font-size: 0.62rem;
  font-weight: 700; letter-spacing: 0.1em;
  padding: 2px 8px; border-radius: 2px; border: 1px solid;
}

.audit-badge--upload           { background:rgba(245,158,11,0.1);  color:var(--amber);      border-color:rgba(245,158,11,0.3); }
.audit-badge--download         { background:rgba(167,139,250,0.1); color:#a78bfa;           border-color:rgba(167,139,250,0.3);}
.audit-badge--view             { background:rgba(100,116,139,0.1); color:#94a3b8;           border-color:rgba(100,116,139,0.3);}
.audit-badge--verify           { background:rgba(16,185,129,0.1);  color:var(--green-ok);   border-color:rgba(16,185,129,0.3); }
.audit-badge--custody_transfer { background:rgba(59,130,246,0.1);  color:var(--blue-info);  border-color:rgba(59,130,246,0.3); }
.audit-badge--case_created     { background:rgba(245,158,11,0.1);  color:var(--amber);      border-color:rgba(245,158,11,0.3); }
.audit-badge--case_closed      { background:rgba(239,68,68,0.1);   color:var(--red-alert);  border-color:rgba(239,68,68,0.3);  }
.audit-badge--report_submission{ background:rgba(16,185,129,0.1);  color:var(--green-ok);   border-color:rgba(16,185,129,0.3); }
.audit-badge--officer_assigned { background:rgba(59,130,246,0.1);  color:var(--blue-info);  border-color:rgba(59,130,246,0.3); }
.audit-badge--analyst_assigned { background:rgba(16,185,129,0.1);  color:var(--green-ok);   border-color:rgba(16,185,129,0.3); }

.audit-entry__role {
  font-size: 0.65rem; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.08em;
  background: var(--bg-elevated); padding: 2px 7px;
  border-radius: 10px; border: 1px solid var(--border);
}
.audit-entry__time { font-size: 0.68rem; color: var(--text-muted); margin-left: auto; }

.audit-entry__details {
  display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 4px;
}
.audit-detail { font-size: 0.68rem; color: var(--text-muted); }
.audit-detail code { color: var(--amber); font-size: 0.65rem; }
.audit-entry__notes { font-size: 0.74rem; color: var(--text-secondary); margin-top: 4px; }
.audit-entry__tx { font-size: 0.65rem; color: var(--amber); margin-top: 4px; }
.audit-entry__tx code { font-size: 0.65rem; word-break: break-all; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
