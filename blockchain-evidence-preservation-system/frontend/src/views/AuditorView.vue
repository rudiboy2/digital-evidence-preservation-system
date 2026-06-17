<template>
  <div class="auditor-view container">

    <!-- Header -->
    <div class="auditor-view__header fade-up">
      <div>
        <h1>📋 Compliance Audit Dashboard</h1>
        <p class="auditor-view__sub">
          Full read-only access — all cases, evidence, audit logs and admissibility checks.
          Zero write permissions.
        </p>
      </div>
      <span class="badge badge--closed">📋 Auditor — Read Only</span>
    </div>

    <!-- Stats -->
    <div class="auditor-view__stats fade-up" style="animation-delay:0.05s">
      <div class="astat">
        <span class="astat__val">{{ stats.totalCases }}</span>
        <span class="astat__label">Total Cases</span>
      </div>
      <div class="astat">
        <span class="astat__val">{{ stats.openCases }}</span>
        <span class="astat__label">Open Cases</span>
      </div>
      <div class="astat">
        <span class="astat__val">{{ stats.totalEvidence }}</span>
        <span class="astat__label">Evidence Items</span>
      </div>
      <div class="astat">
        <span class="astat__val">{{ stats.courtReadyCases }}</span>
        <span class="astat__label">Court Ready</span>
      </div>
      <div class="astat">
        <span class="astat__val">{{ stats.totalLogs }}</span>
        <span class="astat__label">Audit Entries</span>
      </div>
    </div>

    <!-- Tabs -->
    <div class="auditor-view__tabs fade-up" style="animation-delay:0.1s">
      <button v-for="tab in tabs" :key="tab.id"
        :class="['tab-btn', activeTab === tab.id ? 'tab-btn--active' : '']"
        @click="switchTab(tab.id)"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </div>

    <!-- ── ALL CASES ─────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'cases'" class="card fade-up">
      <div class="tab-header">
        <h2>All Cases ({{ allCases.length }})</h2>
        <input v-model="caseSearch" class="form-input tab-search" placeholder="Search cases…" />
      </div>
      <div v-if="isLoadingCases" class="tab-loading"><div class="spinner" /> Loading…</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Case #</th>
            <th>Title</th>
            <th>Warrant</th>
            <th>OB #</th>
            <th>Status</th>
            <th>Court Status</th>
            <th>Priority</th>
            <th>Evidence</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in filteredCases" :key="c.id">
            <td><code class="amber">{{ c.case_number }}</code></td>
            <td class="bold">{{ c.title }}</td>
            <td>
              <span v-if="c.warrant_number" class="small green">✓ {{ c.warrant_number }}</span>
              <span v-else class="small red">✗ Missing</span>
            </td>
            <td>
              <span v-if="c.ob_number" class="small green">✓ {{ c.ob_number }}</span>
              <span v-else class="small red">✗ Missing</span>
            </td>
            <td><span :class="['badge', `badge--${c.status}`]">{{ c.status }}</span></td>
            <td>
              <span v-if="c.court_status" class="small amber">{{ c.court_status.replace('_',' ') }}</span>
              <span v-else class="small muted">—</span>
            </td>
            <td><span :class="['badge', priorityBadge(c.priority)]">{{ c.priority }}</span></td>
            <td class="amber bold">{{ evidenceCounts[c.id] ?? '—' }}</td>
            <td class="muted small">{{ formatDate(c.created_at) }}</td>
            <td>
              <button class="btn btn--ghost small-btn" @click="openAdmissibility(c)">
                Admissibility →
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── ALL EVIDENCE ──────────────────────────────────────────────── -->
    <div v-if="activeTab === 'evidence'" class="card fade-up">
      <div class="tab-header">
        <h2>All Evidence ({{ allEvidence.length }})</h2>
        <input v-model="evidenceSearch" class="form-input tab-search" placeholder="Search by filename or hash…" />
      </div>
      <div v-if="isLoadingEvidence" class="tab-loading"><div class="spinner" /> Loading…</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>File</th>
            <th>Source</th>
            <th>Device</th>
            <th>Seal #</th>
            <th>Witness</th>
            <th>SHA-256</th>
            <th>Status</th>
            <th>Blockchain</th>
            <th>Uploaded</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ev in filteredEvidence" :key="ev.id">
            <td>
              <span class="ev-icon">{{ fileIcon(ev.mime_type) }}</span>
              <span class="bold small">{{ ev.file_name }}</span>
            </td>
            <td class="small muted">{{ ev.evidence_source_type || '—' }}</td>
            <td class="small muted">
              {{ [ev.device_make, ev.device_model].filter(Boolean).join(' ') || '—' }}
            </td>
            <td>
              <span v-if="ev.physical_seal_number" class="small green">✓ {{ ev.physical_seal_number }}</span>
              <span v-else class="small muted">—</span>
            </td>
            <td>
              <span v-if="ev.witness_name" class="small green">✓ {{ ev.witness_name }}</span>
              <span v-else class="small red">✗ None</span>
            </td>
            <td><code class="amber small">{{ ev.sha256_hash?.slice(0,14) }}…</code></td>
            <td><span :class="['badge', `badge--${ev.status}`]">{{ ev.status }}</span></td>
            <td>
              <span v-if="ev.blockchain_tx_hash" class="small green">⬡ Confirmed</span>
              <span v-else class="small muted">⏳ Pending</span>
            </td>
            <td class="small muted">{{ formatDate(ev.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── AUDIT LOG ─────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'audit'" class="card fade-up">
      <div class="tab-header">
        <h2>{{ selectedAuditCase ? `Audit — ${selectedAuditCase.case_number}` : 'Audit Log' }}</h2>
        <div style="display:flex;gap:10px;flex-wrap:wrap">
          <select v-model="auditCaseId" class="form-input tab-search" @change="loadAuditLog">
            <option value="">— Select Case —</option>
            <option v-for="c in allCases" :key="c.id" :value="c.id">
              {{ c.case_number }} — {{ c.title }}
            </option>
          </select>
          <select v-model="auditActionFilter" class="form-input tab-search" style="width:160px">
            <option value="">All Actions</option>
            <option v-for="a in auditActions" :key="a" :value="a">{{ a.replace(/_/g,' ') }}</option>
          </select>
        </div>
      </div>
      <div v-if="isLoadingAudit" class="tab-loading"><div class="spinner" /> Loading…</div>
      <div v-else-if="!auditCaseId" class="tab-empty">Select a case to view its full audit trail.</div>
      <div v-else-if="filteredAuditLogs.length === 0" class="tab-empty">No entries found.</div>
      <div v-else class="audit-timeline">
        <div v-for="log in filteredAuditLogs" :key="log.id" class="audit-entry">
          <div :class="['audit-dot', `audit-dot--${log.action}`]">{{ actionIcon(log.action) }}</div>
          <div class="audit-entry__content">
            <div class="audit-entry__top">
              <span :class="['audit-badge', `audit-badge--${log.action}`]">
                {{ log.action.replace(/_/g,' ').toUpperCase() }}
              </span>
              <span class="audit-role">{{ log.performed_by_role || '?' }}</span>
              <span v-if="log.ip_address" class="audit-ip">IP: {{ log.ip_address }}</span>
              <span class="audit-time">{{ formatDateFull(log.timestamp) }}</span>
            </div>
            <div class="audit-details">
              <span v-if="log.evidence_id" class="audit-detail">
                Evidence: <code>{{ log.evidence_id?.slice(0,12) }}…</code>
              </span>
              <span class="audit-detail">
                User: <code>{{ log.performed_by?.slice(0,12) }}…</code>
              </span>
            </div>
            <p v-if="log.notes" class="audit-notes">{{ log.notes }}</p>
            <div v-if="log.blockchain_tx_hash" class="audit-tx">
              ⬡ TX: <code>{{ log.blockchain_tx_hash }}</code>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── ADMISSIBILITY CHECKER ─────────────────────────────────────── -->
    <div v-if="activeTab === 'admissibility'" class="fade-up">

      <div class="card" style="margin-bottom:20px">
        <div class="tab-header">
          <h2>Court Admissibility Checker</h2>
          <select v-model="admissibilityCaseId" class="form-input tab-search" @change="loadAdmissibility">
            <option value="">— Select Case to Check —</option>
            <option v-for="c in allCases" :key="c.id" :value="c.id">
              {{ c.case_number }} — {{ c.title }}
            </option>
          </select>
        </div>
        <p class="tab-sub">
          Automatically checks all mandatory requirements for digital evidence to be
          admissible in Tanzanian courts under the Electronic Evidence Act and TDFL-STD-2023.
        </p>
      </div>

      <div v-if="isLoadingAdmissibility" class="tab-loading card"><div class="spinner" /> Checking…</div>

      <div v-else-if="admissibilityResult" class="admissibility-result">

        <!-- Score card -->
        <div class="score-card card">
          <div class="score-card__left">
            <div :class="['score-circle', admissibilityResult.compliance_score >= 80 ? 'score-circle--pass' : 'score-circle--fail']">
              <span class="score-circle__num">{{ admissibilityResult.compliance_score }}%</span>
              <span class="score-circle__label">Compliance</span>
            </div>
          </div>
          <div class="score-card__right">
            <div class="score-card__case">{{ admissibilityResult.case_number }} — {{ admissibilityResult.case_title }}</div>
            <div :class="['score-card__verdict', admissibilityResult.is_court_ready ? 'verdict--ready' : 'verdict--not-ready']">
              {{ admissibilityResult.is_court_ready ? '✓ COURT READY' : '✕ NOT YET COURT READY' }}
            </div>
            <div class="score-card__stats">
              <span class="stat--pass">{{ admissibilityResult.passed }} checks passed</span>
              <span class="stat--fail">{{ admissibilityResult.total - admissibilityResult.passed }} checks failed</span>
            </div>
            <p v-if="admissibilityResult.missing_required_items?.length" class="score-card__missing">
              Missing required: {{ admissibilityResult.missing_required_items.join(', ') }}
            </p>
          </div>
        </div>

        <!-- Detailed checklist -->
        <div class="card checklist">
          <h3 class="checklist__title">Detailed Checklist</h3>
          <div v-for="check in admissibilityResult.checks" :key="check.label" class="check-item">
            <span :class="['check-icon', `check-icon--${check.status}`]">
              {{ check.status === 'pass' ? '✓' : check.status === 'warning' ? '⚠' : '✗' }}
            </span>
            <div class="check-content">
              <span class="check-label">{{ check.label }}</span>
              <span v-if="check.required" class="check-required">Required</span>
              <span v-else class="check-optional">Recommended</span>
              <p v-if="check.detail" class="check-detail">{{ check.detail }}</p>
            </div>
          </div>
        </div>

        <div class="checklist-footer">
          <span class="small muted">Generated: {{ formatDateFull(admissibilityResult.generated_at) }}</span>
          <span class="small muted">by {{ admissibilityResult.generated_by_role }}</span>
        </div>
      </div>

      <div v-else-if="admissibilityCaseId && !isLoadingAdmissibility" class="tab-empty card">
        Select a case above to run the admissibility check.
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const activeTab    = ref('cases')
const allCases     = ref([])
const allEvidence  = ref([])
const auditLogs    = ref([])
const evidenceCounts = ref({})
const caseSearch     = ref('')
const evidenceSearch = ref('')
const auditCaseId    = ref('')
const auditActionFilter = ref('')
const selectedAuditCase = ref(null)
const admissibilityCaseId  = ref('')
const admissibilityResult  = ref(null)
const isLoadingCases       = ref(true)
const isLoadingEvidence    = ref(false)
const isLoadingAudit       = ref(false)
const isLoadingAdmissibility = ref(false)

const stats = ref({ totalCases:0, openCases:0, totalEvidence:0, courtReadyCases:0, totalLogs:0 })

const tabs = [
  { id:'cases',         label:'All Cases',    icon:'📁' },
  { id:'evidence',      label:'All Evidence', icon:'⬡'  },
  { id:'audit',         label:'Audit Logs',   icon:'📋' },
  { id:'admissibility', label:'Court Checker', icon:'⚖️' },
]

const auditActions = [
  'case_created','case_viewed','case_updated','case_closed','case_submitted_to_court',
  'officer_assigned','analyst_assigned','upload','view','download','verify',
  'custody_transfer','report_submission','evidence_submitted_to_court',
]

onMounted(loadCases)

watch(activeTab, async (tab) => {
  if (tab === 'evidence' && allEvidence.value.length === 0) await loadAllEvidence()
})

async function switchTab(id) {
  activeTab.value = id
}

const token = () => localStorage.getItem('access_token')

async function loadCases() {
  isLoadingCases.value = true
  try {
    const resp = await fetch('http://localhost:8000/api/v1/cases/?page_size=200', {
      headers: { 'Authorization': `Bearer ${token()}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      allCases.value = data.items || []
      stats.value.totalCases = data.total || allCases.value.length
      stats.value.openCases  = allCases.value.filter(c => c.status === 'open').length
    }
  } catch {}
  isLoadingCases.value = false
}

async function loadAllEvidence() {
  isLoadingEvidence.value = true
  const all = []
  for (const c of allCases.value) {
    try {
      const resp = await fetch(`http://localhost:8000/api/v1/evidence/case/${c.id}?page_size=100`, {
        headers: { 'Authorization': `Bearer ${token()}` }
      })
      if (resp.ok) {
        const d = await resp.json()
        all.push(...(d.items || []))
        evidenceCounts.value[c.id] = d.total || (d.items||[]).length
      }
    } catch {}
  }
  allEvidence.value = all
  stats.value.totalEvidence = all.length
  isLoadingEvidence.value = false
}

async function loadAuditLog() {
  if (!auditCaseId.value) return
  selectedAuditCase.value = allCases.value.find(c => c.id === auditCaseId.value)
  isLoadingAudit.value = true
  try {
    const resp = await fetch(`http://localhost:8000/api/v1/cases/${auditCaseId.value}/audit-log?page_size=200`, {
      headers: { 'Authorization': `Bearer ${token()}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      auditLogs.value = data.logs || []
      stats.value.totalLogs = data.total || auditLogs.value.length
    }
  } catch {}
  isLoadingAudit.value = false
}

async function loadAdmissibility() {
  if (!admissibilityCaseId.value) return
  isLoadingAdmissibility.value = true
  admissibilityResult.value = null
  try {
    const resp = await fetch(
      `http://localhost:8000/api/v1/cases/${admissibilityCaseId.value}/admissibility-check`,
      { headers: { 'Authorization': `Bearer ${token()}` } }
    )
    if (resp.ok) {
      admissibilityResult.value = await resp.json()
      // Count court-ready cases
      if (admissibilityResult.value.is_court_ready) stats.value.courtReadyCases++
    }
  } catch {}
  isLoadingAdmissibility.value = false
}

function openAdmissibility(c) {
  activeTab.value = 'admissibility'
  admissibilityCaseId.value = c.id
  loadAdmissibility()
}

// Computed filters
const filteredCases = computed(() => {
  if (!caseSearch.value) return allCases.value
  const q = caseSearch.value.toLowerCase()
  return allCases.value.filter(c =>
    c.case_number.toLowerCase().includes(q) || c.title.toLowerCase().includes(q)
  )
})

const filteredEvidence = computed(() => {
  if (!evidenceSearch.value) return allEvidence.value
  const q = evidenceSearch.value.toLowerCase()
  return allEvidence.value.filter(e =>
    e.file_name.toLowerCase().includes(q) || (e.sha256_hash||'').includes(q)
  )
})

const filteredAuditLogs = computed(() => {
  if (!auditActionFilter.value) return auditLogs.value
  return auditLogs.value.filter(l => l.action === auditActionFilter.value)
})

// Helpers
function fileIcon(mime='') {
  if (mime?.startsWith('image/')) return '🖼'
  if (mime?.startsWith('video/')) return '🎥'
  if (mime?.startsWith('audio/')) return '🎙'
  if (mime?.includes('pdf')) return '📄'
  return '💾'
}

function actionIcon(a='') {
  return { upload:'⬆', view:'👁', download:'⬇', verify:'✓',
           custody_transfer:'↔', case_created:'📁', case_closed:'🔒',
           officer_assigned:'👮', analyst_assigned:'🔬',
           report_submission:'📋', evidence_submitted_to_court:'⚖️' }[a] || '⬡'
}

function priorityBadge(p) {
  return { critical:'badge--tampered', high:'badge--tampered',
           medium:'badge--pending', low:'badge--closed' }[p] || 'badge--closed'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {day:'2-digit',month:'short',year:'numeric'})
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
.auditor-view { padding:32px 24px; }
.auditor-view__header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px; }
.auditor-view__sub { font-size:0.78rem; color:var(--text-muted); margin-top:4px; max-width:560px; }

.auditor-view__stats {
  display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
  gap:16px; margin-bottom:24px;
}
.astat { background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius-lg); padding:18px 20px; display:flex; flex-direction:column; gap:4px; }
.astat__val { font-family:var(--font-display); font-size:2rem; font-weight:700; color:var(--amber); line-height:1; }
.astat__label { font-size:0.65rem; letter-spacing:0.1em; text-transform:uppercase; color:var(--text-muted); }

.auditor-view__tabs { display:flex; gap:4px; margin-bottom:20px; border-bottom:1px solid var(--border); flex-wrap:wrap; }
.tab-btn { background:transparent; border:none; font-family:var(--font-display); font-size:0.8rem; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:var(--text-muted); padding:10px 18px; cursor:pointer; border-bottom:2px solid transparent; transition:all 0.2s; }
.tab-btn:hover { color:var(--text-primary); }
.tab-btn--active { color:var(--amber); border-bottom-color:var(--amber); }

.tab-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; flex-wrap:wrap; gap:10px; }
.tab-header h2 { font-size:1rem; }
.tab-search { width:220px; padding:7px 12px; font-size:0.78rem; }
.tab-sub { font-size:0.75rem; color:var(--text-muted); margin-bottom:16px; line-height:1.6; }
.tab-loading, .tab-empty { display:flex; align-items:center; justify-content:center; gap:10px; padding:40px; color:var(--text-muted); font-size:0.82rem; }

/* Table helpers */
.amber { color:var(--amber); }
.bold  { color:var(--text-primary); font-weight:500; }
.muted { color:var(--text-secondary); }
.small { font-size:0.72rem; }
.green { color:var(--green-ok); }
.red   { color:var(--red-alert); }
.small-btn { padding:4px 10px; font-size:0.7rem; }
.ev-icon { margin-right:6px; }

/* Audit timeline */
.audit-timeline { display:flex; flex-direction:column; max-height:600px; overflow-y:auto; }
.audit-entry { display:flex; gap:12px; padding:12px 8px; border-bottom:1px solid var(--border); }
.audit-entry:last-child { border-bottom:none; }
.audit-dot { width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.85rem; flex-shrink:0; background:var(--bg-secondary); border:1px solid var(--border); }
.audit-dot--upload           { border-color:var(--amber);     color:var(--amber); }
.audit-dot--download         { border-color:#a78bfa;          color:#a78bfa; }
.audit-dot--verify           { border-color:var(--green-ok);  color:var(--green-ok); }
.audit-dot--custody_transfer { border-color:var(--blue-info); color:var(--blue-info); }
.audit-dot--case_created     { border-color:var(--amber);     color:var(--amber); }
.audit-dot--report_submission{ border-color:var(--green-ok);  color:var(--green-ok); }
.audit-entry__content { flex:1; }
.audit-entry__top { display:flex; align-items:center; gap:8px; margin-bottom:4px; flex-wrap:wrap; }
.audit-badge { font-family:var(--font-display); font-size:0.6rem; font-weight:700; letter-spacing:0.1em; padding:2px 7px; border-radius:2px; border:1px solid; }
.audit-badge--upload            { background:rgba(245,158,11,0.1);  color:var(--amber);      border-color:rgba(245,158,11,0.3); }
.audit-badge--download          { background:rgba(167,139,250,0.1); color:#a78bfa;           border-color:rgba(167,139,250,0.3);}
.audit-badge--view              { background:rgba(100,116,139,0.1); color:#94a3b8;           border-color:rgba(100,116,139,0.3);}
.audit-badge--verify            { background:rgba(16,185,129,0.1);  color:var(--green-ok);   border-color:rgba(16,185,129,0.3); }
.audit-badge--report_submission { background:rgba(16,185,129,0.1);  color:var(--green-ok);   border-color:rgba(16,185,129,0.3); }
.audit-badge--custody_transfer  { background:rgba(59,130,246,0.1);  color:var(--blue-info);  border-color:rgba(59,130,246,0.3); }
.audit-badge--case_created      { background:rgba(245,158,11,0.1);  color:var(--amber);      border-color:rgba(245,158,11,0.3); }
.audit-badge--case_closed       { background:rgba(239,68,68,0.1);   color:var(--red-alert);  border-color:rgba(239,68,68,0.3);  }
.audit-badge--officer_assigned  { background:rgba(59,130,246,0.1);  color:var(--blue-info);  border-color:rgba(59,130,246,0.3); }
.audit-badge--analyst_assigned  { background:rgba(16,185,129,0.1);  color:var(--green-ok);   border-color:rgba(16,185,129,0.3); }
.audit-role { font-size:0.62rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.08em; background:var(--bg-elevated); padding:1px 6px; border-radius:8px; border:1px solid var(--border); }
.audit-ip { font-size:0.62rem; color:var(--text-muted); }
.audit-time { font-size:0.65rem; color:var(--text-muted); margin-left:auto; }
.audit-details { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:2px; }
.audit-detail { font-size:0.68rem; color:var(--text-muted); }
.audit-detail code { color:var(--amber); font-size:0.65rem; }
.audit-notes { font-size:0.72rem; color:var(--text-secondary); margin-top:2px; }
.audit-tx { font-size:0.65rem; color:var(--amber); margin-top:2px; }
.audit-tx code { font-size:0.65rem; word-break:break-all; }

/* Admissibility */
.admissibility-result { display:flex; flex-direction:column; gap:20px; }

.score-card { display:flex; gap:32px; align-items:center; padding:28px; }
.score-circle { width:110px; height:110px; border-radius:50%; display:flex; flex-direction:column; align-items:center; justify-content:center; border:4px solid; flex-shrink:0; }
.score-circle--pass { border-color:var(--green-ok); background:rgba(16,185,129,0.08); }
.score-circle--fail { border-color:var(--red-alert); background:rgba(239,68,68,0.08); }
.score-circle__num { font-family:var(--font-display); font-size:1.8rem; font-weight:700; line-height:1; }
.score-circle--pass .score-circle__num { color:var(--green-ok); }
.score-circle--fail .score-circle__num { color:var(--red-alert); }
.score-circle__label { font-size:0.6rem; letter-spacing:0.1em; text-transform:uppercase; color:var(--text-muted); }

.score-card__right { flex:1; display:flex; flex-direction:column; gap:8px; }
.score-card__case { font-size:0.82rem; color:var(--text-secondary); }
.score-card__verdict { font-family:var(--font-display); font-size:1.1rem; font-weight:700; letter-spacing:0.08em; }
.verdict--ready     { color:var(--green-ok); }
.verdict--not-ready { color:var(--red-alert); }
.score-card__stats { display:flex; gap:16px; }
.stat--pass { font-size:0.78rem; color:var(--green-ok); }
.stat--fail { font-size:0.78rem; color:var(--red-alert); }
.score-card__missing { font-size:0.72rem; color:var(--red-alert); }


.checklist__title { font-size:0.95rem; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--border); }
.check-item { display:flex; gap:12px; padding:10px 0; border-bottom:1px solid var(--border); }
.check-item:last-child { border-bottom:none; }
.check-icon { width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700; flex-shrink:0; }
.check-icon--pass    { background:rgba(16,185,129,0.15); color:var(--green-ok); }
.check-icon--fail    { background:rgba(239,68,68,0.15);  color:var(--red-alert); }
.check-icon--warning { background:rgba(245,158,11,0.15); color:var(--amber); }
.check-content { flex:1; }
.check-label { font-size:0.82rem; color:var(--text-primary); margin-right:8px; }
.check-required { font-size:0.6rem; letter-spacing:0.08em; text-transform:uppercase; color:var(--red-alert); background:rgba(239,68,68,0.1); padding:1px 6px; border-radius:4px; }
.check-optional { font-size:0.6rem; letter-spacing:0.08em; text-transform:uppercase; color:var(--text-muted); background:var(--bg-elevated); padding:1px 6px; border-radius:4px; }
.check-detail { font-size:0.72rem; color:var(--text-muted); margin-top:3px; font-style:italic; }
.checklist-footer { display:flex; gap:16px; font-size:0.7rem; color:var(--text-muted); padding:8px 0; }

.spinner { width:22px; height:22px; border:2px solid var(--border); border-top-color:var(--amber); border-radius:50%; animation:spin 0.8s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
</style>
