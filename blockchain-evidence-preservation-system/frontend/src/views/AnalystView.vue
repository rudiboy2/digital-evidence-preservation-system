<template>
  <div class="analyst-view container">

    <div class="analyst-view__header fade-up">
      <div>
        <h1>🔬 Forensic Analysis</h1>
        <p class="analyst-view__sub">
          Assigned cases — view evidence, download for offline analysis, submit court-ready reports.
        </p>
      </div>
    </div>

    <!-- Loading / empty -->
    <div v-if="isLoading" class="analyst-view__loading">
      <div class="spinner" /> Loading assigned cases…
    </div>

    <div v-else-if="cases.length === 0" class="card analyst-view__empty">
      <span style="font-size:2rem">🔬</span>
      <p>No cases assigned to you yet.</p>
      <p style="font-size:0.72rem;color:var(--text-muted)">
        Contact your investigator to be assigned to a case.
      </p>
    </div>

    <div v-else class="analyst-view__layout">

      <!-- Case list -->
      <div class="analyst-view__cases">
        <div
          v-for="c in cases" :key="c.id"
          class="case-card card"
          :class="{ 'case-card--active': selectedCase?.id === c.id }"
          @click="selectCase(c)"
        >
          <div class="case-card__header">
            <code class="case-card__num">{{ c.case_number }}</code>
            <span :class="['badge', `badge--${c.status}`]">{{ c.status }}</span>
          </div>
          <h3 class="case-card__title">{{ c.title }}</h3>
          <p v-if="c.description" class="case-card__desc">{{ c.description }}</p>
          <div class="case-card__meta">
            <span>📁 {{ evidenceCounts[c.id] || 0 }} evidence</span>
            <span>📋 {{ reportCounts[c.id] || 0 }} reports</span>
            <span v-if="c.warrant_number">🔏 Warrant: {{ c.warrant_number }}</span>
          </div>
        </div>
      </div>

      <!-- Case detail panel -->
      <div v-if="selectedCase" class="analyst-view__panel">

        <!-- Evidence list -->
        <div class="card panel-section">
          <div class="panel-header">
            <h2>Evidence Items</h2>
            <span class="panel-header__sub">
              Download for offline forensic analysis — all downloads are audit-logged
            </span>
          </div>

          <div v-if="isLoadingEvidence" class="loading-row"><div class="spinner" /></div>
          <div v-else-if="evidence.length === 0" class="empty-row">No evidence uploaded yet.</div>
          <div v-else class="evidence-list">
            <div v-for="ev in evidence" :key="ev.id" class="ev-row-wrapper">
              <div class="ev-row">
                <span class="ev-row__icon">{{ fileIcon(ev.mime_type) }}</span>
                <div class="ev-row__info">
                  <span class="ev-row__name">{{ ev.file_name }}</span>
                  <div class="ev-row__meta-grid">
                    <span>{{ formatSize(ev.file_size) }}</span>
                    <span>{{ ev.evidence_type }}</span>
                    <span :class="['badge', `badge--${ev.status}`]">{{ ev.status }}</span>
                  </div>
                  <code class="ev-row__hash">SHA-256: {{ ev.sha256_hash?.slice(0,32) }}…</code>
                  <!-- Device metadata if available -->
                  <div v-if="ev.device_type || ev.device_make" class="ev-row__device">
                    🔍 {{ [ev.device_make, ev.device_model, ev.device_type].filter(Boolean).join(' · ') }}
                    <span v-if="ev.device_serial_number">| S/N: {{ ev.device_serial_number }}</span>
                    <span v-if="ev.device_imei">| IMEI: {{ ev.device_imei }}</span>
                  </div>
                  <div v-if="ev.collection_location" class="ev-row__location">
                    📍 {{ ev.collection_location }}
                    <span v-if="ev.collection_gps_lat"> ({{ ev.collection_gps_lat }}, {{ ev.collection_gps_lng }})</span>
                  </div>
                  <div v-if="ev.witness_name" class="ev-row__witness">
                    👤 Witness: {{ ev.witness_name }}
                    <span v-if="ev.witness_badge_number">({{ ev.witness_badge_number }})</span>
                    <span v-if="ev.physical_seal_number">| Seal: {{ ev.physical_seal_number }}</span>
                    <span v-if="ev.evidence_bag_number">| Bag: {{ ev.evidence_bag_number }}</span>
                  </div>
                </div>
                <div class="ev-row__actions">
                  <button
                    class="btn ev-row__download-btn"
                    :disabled="downloadingIds.has(ev.id)"
                    @click="downloadEvidence(ev)"
                  >
                    <span v-if="downloadingIds.has(ev.id)" class="ev-spinner" />
                    <span v-else>⬇</span>
                    {{ downloadingIds.has(ev.id) ? 'Downloading…' : `Download (${formatSize(ev.file_size)})` }}
                  </button>
                  <button class="btn btn--ghost ev-row__btn" @click="verifyEvidence(ev)">✓ Verify</button>
                </div>
              </div>
              <!-- Download message -->
              <div
                v-if="downloadMessages[ev.id]"
                :class="['ev-row__dl-msg', `ev-row__dl-msg--${downloadMessages[ev.id].type}`]"
              >
                {{ downloadMessages[ev.id].text }}
              </div>
            </div>
          </div>
        </div>

        <!-- Reports section -->
        <div class="card panel-section" style="margin-top:20px">
          <div class="panel-header">
            <h2>Forensic Analysis Reports</h2>
            <button class="btn btn--primary" @click="showReportModal = true">
              + Submit Report
            </button>
          </div>

          <div v-if="reports.length === 0" class="empty-row">
            No reports submitted yet for this case.
          </div>

          <div v-else class="report-list">
            <div v-for="r in reports" :key="r.id" class="report-card">
              <div class="report-card__header">
                <span class="report-card__title">{{ r.title }}</span>
                <span :class="['badge', r.status === 'submitted' ? 'badge--verified' : 'badge--pending']">
                  {{ r.status }}
                </span>
              </div>
              <p class="report-card__summary">{{ r.summary }}</p>
              <div class="report-card__meta">
                <span v-if="r.forensic_tool_name">🔧 {{ r.forensic_tool_name }} {{ r.forensic_tool_version }}</span>
                <span v-if="r.lab_reference_number">🏛 Lab Ref: {{ r.lab_reference_number }}</span>
                <span v-if="r.analyst_certification_number">🎓 Cert: {{ r.analyst_certification_number }}</span>
                <span v-if="r.is_expert_witness" class="badge badge--verified">Expert Witness</span>
                <span>{{ formatDate(r.submitted_at || r.created_at) }}</span>
              </div>
              <div v-if="r.blockchain_tx_hash" class="report-card__chain">
                ⬡ On-chain: <code>{{ r.blockchain_tx_hash?.slice(0,20) }}…</code>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- No case selected -->
      <div v-else class="analyst-view__select-hint card">
        <span style="font-size:2rem">👈</span>
        <p>Select a case from the list to view evidence and submit reports.</p>
      </div>

    </div>

    <!-- ── REPORT MODAL ───────────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="showReportModal" class="modal-overlay" @click.self="showReportModal = false">
        <div class="modal modal--wide card fade-up">
          <h2 class="modal__title">🔬 Submit Forensic Analysis Report</h2>
          <p class="modal__subtitle">
            Case: <strong>{{ selectedCase?.case_number }}</strong> — {{ selectedCase?.title }}<br/>
            All fields marked * are required by TDFL-STD-2023 for court admissibility.
          </p>

          <div v-if="reportError"   class="modal__error">{{ reportError }}</div>
          <div v-if="reportSuccess" class="modal__success">
            ✓ Report submitted and recorded on audit trail.
          </div>

          <div v-if="!reportSuccess" class="modal__form">

            <!-- Core content -->
            <div class="modal__section-title">📄 Report Content</div>
            <div class="form-group">
              <label class="form-label">Report Title *</label>
              <input v-model="reportForm.title" class="form-input" required
                placeholder="e.g. Digital Forensics Analysis — Case BEPS-2026..." />
            </div>
            <div class="form-group">
              <label class="form-label">Executive Summary *</label>
              <textarea v-model="reportForm.summary" class="form-input" rows="3" required
                placeholder="Brief overview of findings and conclusions…" />
            </div>
            <div class="form-group">
              <label class="form-label">Methodology *</label>
              <textarea v-model="reportForm.methodology" class="form-input" rows="3"
                placeholder="Tools used, approach taken, standards followed (e.g. ACPO Guidelines)…" />
            </div>
            <div class="form-group">
              <label class="form-label">Findings *</label>
              <textarea v-model="reportForm.findings" class="form-input" rows="4"
                placeholder="Detailed findings from forensic examination…" />
            </div>
            <div class="form-group">
              <label class="form-label">Conclusion *</label>
              <textarea v-model="reportForm.conclusion" class="form-input" rows="3"
                placeholder="Overall conclusion and recommendations to the investigator…" />
            </div>

            <!-- TDFL mandatory fields -->
            <div class="modal__section-title">🏛 TDFL-STD-2023 Mandatory Fields</div>

            <div class="modal__row">
              <div class="form-group">
                <label class="form-label">TCRA Certification Number *</label>
                <input v-model="reportForm.analyst_certification_number" class="form-input"
                  placeholder="e.g. TCRA-DFE-2024-001" />
              </div>
              <div class="form-group">
                <label class="form-label">Lab Reference Number</label>
                <input v-model="reportForm.lab_reference_number" class="form-input"
                  placeholder="TDFL lab case number" />
              </div>
            </div>

            <div class="modal__row">
              <div class="form-group">
                <label class="form-label">Forensic Tool(s) Used *</label>
                <input v-model="reportForm.forensic_tool_name" class="form-input"
                  placeholder="e.g. Autopsy, Cellebrite UFED, FTK" />
              </div>
              <div class="form-group">
                <label class="form-label">Tool Version(s) *</label>
                <input v-model="reportForm.forensic_tool_version" class="form-input"
                  placeholder="e.g. Autopsy 4.21.0, UFED 7.68" />
              </div>
            </div>

            <div class="modal__row">
              <div class="form-group">
                <label class="form-label">Examination Start Date *</label>
                <input v-model="reportForm.examination_start_date" type="datetime-local" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">Examination End Date *</label>
                <input v-model="reportForm.examination_end_date" type="datetime-local" class="form-input" />
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Work Copy Hash (SHA-256 of forensic copy) *</label>
              <input v-model="reportForm.work_copy_hash" class="form-input"
                placeholder="SHA-256 hash of the forensic work copy (not the original)" />
            </div>

            <div class="modal__row">
              <div class="form-group">
                <label class="form-label">Number of Copies Made</label>
                <input v-model="reportForm.copies_made" type="number" class="form-input" min="0" placeholder="0" />
              </div>
              <div class="form-group">
                <label class="form-label">Copies Location</label>
                <input v-model="reportForm.copies_location" class="form-input"
                  placeholder="Where copies are stored" />
              </div>
            </div>

            <!-- Expert witness -->
            <div class="form-group">
              <label class="modal__checkbox-label">
                <input v-model="reportForm.is_expert_witness" type="checkbox" />
                <span>I am designated as Expert Witness for this case</span>
              </label>
            </div>
            <div v-if="reportForm.is_expert_witness" class="form-group">
              <label class="form-label">Court Designation</label>
              <input v-model="reportForm.expert_witness_court_designation" class="form-input"
                placeholder="e.g. High Court of Tanzania, Criminal Division" />
            </div>

            <!-- Independence statement -->
            <div class="modal__section-title">⚖️ Statement of Independence</div>
            <div class="form-group">
              <label class="modal__checkbox-label">
                <input v-model="reportForm.independence_statement" type="checkbox" />
                <span>I declare that I have no personal interest in this case and have conducted
                  this examination independently and impartially.</span>
              </label>
            </div>

            <!-- Declaration -->
            <div class="form-group">
              <label class="form-label">Analyst Declaration *</label>
              <textarea v-model="reportForm.analyst_declaration" class="form-input" rows="3"
                placeholder="I, [Full Name], TCRA Certified Digital Forensics Examiner No. [Cert], hereby declare that the above report is true and accurate to the best of my knowledge and belief…" />
            </div>

            <div class="modal__actions">
              <button class="btn btn--ghost" @click="showReportModal = false">Cancel</button>
              <button
                class="btn btn--primary"
                :disabled="!isReportValid || isSubmittingReport"
                @click="submitReport"
              >
                <span v-if="isSubmittingReport" class="modal__spinner" />
                {{ isSubmittingReport ? 'Submitting…' : 'Submit Report' }}
              </button>
            </div>
          </div>

          <div v-else class="modal__actions">
            <button class="btn btn--primary" @click="closeReportModal">Close</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Verify Modal -->
    <Teleport to="body">
      <div v-if="verifyResult" class="modal-overlay" @click.self="verifyResult = null">
        <div class="modal card fade-up" style="text-align:center">
          <div class="modal__icon" :class="verifyResult.is_valid ? 'modal__icon--ok' : 'modal__icon--fail'">
            {{ verifyResult.is_valid ? '✓' : '✕' }}
          </div>
          <h2 class="modal__title">{{ verifyResult.is_valid ? 'Integrity Verified' : '⚠ Tampered!' }}</h2>
          <p class="modal__message">{{ verifyResult.message }}</p>
          <button class="btn btn--ghost" style="width:100%;justify-content:center" @click="verifyResult = null">Close</button>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

const cases           = ref([])
const selectedCase    = ref(null)
const evidence        = ref([])
const reports         = ref([])
const evidenceCounts  = ref({})
const reportCounts    = ref({})
const isLoading       = ref(true)
const isLoadingEvidence = ref(false)
const showReportModal   = ref(false)
const reportError       = ref('')
const reportSuccess     = ref(false)
const isSubmittingReport = ref(false)
const verifyResult      = ref(null)
const downloadingIds    = ref(new Set())
const downloadMessages  = ref({})

const reportForm = reactive({
  title: '', summary: '', findings: '', methodology: '', conclusion: '',
  analyst_certification_number: '', forensic_tool_name: '', forensic_tool_version: '',
  lab_reference_number: '', examination_start_date: '', examination_end_date: '',
  work_copy_hash: '', independence_statement: false, independence_statement_text: '',
  copies_made: '', copies_location: '', is_expert_witness: false,
  expert_witness_court_designation: '', analyst_declaration: '',
})

const isReportValid = computed(() =>
  reportForm.title && reportForm.summary && reportForm.findings &&
  reportForm.methodology && reportForm.conclusion &&
  reportForm.analyst_certification_number && reportForm.forensic_tool_name &&
  reportForm.forensic_tool_version && reportForm.analyst_declaration &&
  reportForm.independence_statement
)

onMounted(async () => {
  const token = localStorage.getItem('access_token')
  try {
    const resp = await fetch('http://localhost:8000/api/v1/cases/?page_size=100', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      cases.value = data.items || []
    }
  } catch {}
  isLoading.value = false
})

async function selectCase(c) {
  selectedCase.value = c
  isLoadingEvidence.value = true
  evidence.value = []
  reports.value  = []
  const token = localStorage.getItem('access_token')
  try {
    const evResp = await fetch(`http://localhost:8000/api/v1/evidence/case/${c.id}?page_size=100`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (evResp.ok) {
      const d = await evResp.json()
      evidence.value = d.items || []
      evidenceCounts.value[c.id] = d.total || evidence.value.length
    }
  } catch {}
  try {
    const repResp = await fetch(`http://localhost:8000/api/v1/cases/${c.id}/reports`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (repResp.ok) {
      const d = await repResp.json()
      reports.value = d.items || []
      reportCounts.value[c.id] = reports.value.length
    }
  } catch {}
  isLoadingEvidence.value = false
}

async function downloadEvidence(ev) {
  downloadingIds.value = new Set([...downloadingIds.value, ev.id])
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch(
      `http://localhost:8000/api/v1/evidence/${ev.id}/download`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    )
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || `Download failed: HTTP ${response.status}`)
    }
    const disposition = response.headers.get('Content-Disposition')
    let filename = ev.file_name
    if (disposition) {
      const m = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (m) filename = m[1].replace(/['"]/g, '')
    }
    const blob = await response.blob()
    const url  = window.URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = filename
    document.body.appendChild(a); a.click()
    document.body.removeChild(a); window.URL.revokeObjectURL(url)
    downloadMessages.value = { ...downloadMessages.value, [ev.id]: { type:'ok', text:`✓ "${filename}" downloaded. Logged in audit trail.` } }
    setTimeout(() => {
      const m = { ...downloadMessages.value }
      delete m[ev.id]
      downloadMessages.value = m
    }, 5000)
  } catch (err) {
    downloadMessages.value = { ...downloadMessages.value, [ev.id]: { type:'error', text:`Download failed: ${err.message}` } }
  } finally {
    const s = new Set(downloadingIds.value)
    s.delete(ev.id)
    downloadingIds.value = s
  }
}

async function verifyEvidence(ev) {
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(`http://localhost:8000/api/v1/evidence/${ev.id}/verify`, {
      method: 'POST', headers: { 'Authorization': `Bearer ${token}` }
    })
    verifyResult.value = await resp.json()
  } catch { alert('Verification failed.') }
}

async function submitReport() {
  reportError.value = ''
  isSubmittingReport.value = true
  try {
    const token = localStorage.getItem('access_token')
    const body = {
      ...reportForm,
      copies_made: reportForm.copies_made ? parseInt(reportForm.copies_made) : null,
    }
    const resp = await fetch(`http://localhost:8000/api/v1/cases/${selectedCase.value.id}/reports`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail))
    }
    reportSuccess.value = true
    const data = await resp.json()
    reports.value.unshift(data)
    reportCounts.value[selectedCase.value.id] = reports.value.length
  } catch (err) {
    reportError.value = err.message || 'Failed to submit report.'
  } finally {
    isSubmittingReport.value = false
  }
}

function closeReportModal() {
  showReportModal.value = false
  reportSuccess.value   = false
  reportError.value     = ''
  Object.keys(reportForm).forEach(k => {
    reportForm[k] = typeof reportForm[k] === 'boolean' ? false : ''
  })
}

function fileIcon(mime = '') {
  if (mime?.startsWith('image/')) return '🖼'
  if (mime?.startsWith('video/')) return '🎥'
  if (mime?.startsWith('audio/')) return '🎙'
  if (mime?.includes('pdf'))      return '📄'
  return '💾'
}

function formatSize(b = 0) {
  if (b < 1024) return `${b} B`
  if (b < 1024*1024) return `${(b/1024).toFixed(1)} KB`
  return `${(b/(1024*1024)).toFixed(2)} MB`
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', {
    day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit'
  })
}
</script>

<style scoped>
.analyst-view { padding: 32px 24px; }
.analyst-view__header { display:flex; justify-content:space-between; margin-bottom:24px; }
.analyst-view__sub { font-size:0.78rem; color:var(--text-muted); margin-top:4px; }
.analyst-view__loading, .analyst-view__empty {
  display:flex; flex-direction:column; align-items:center; gap:12px;
  padding:48px; color:var(--text-muted);
}
.analyst-view__layout {
  display: grid; grid-template-columns: 300px 1fr; gap: 20px; align-items: start;
}
.analyst-view__cases { display: flex; flex-direction: column; gap: 12px; }
.analyst-view__select-hint {
  display:flex; flex-direction:column; align-items:center; gap:12px;
  padding:48px; color:var(--text-muted); font-size:0.82rem;
}

/* Case cards */
.case-card { cursor:pointer; transition: border-color 0.2s; }
.case-card:hover { border-color: var(--amber); }
.case-card--active { border-color: var(--amber); box-shadow: var(--shadow-glow); }
.case-card__header { display:flex; justify-content:space-between; margin-bottom:8px; }
.case-card__num { font-size:0.7rem; color:var(--amber); }
.case-card__title { font-size:0.9rem; font-family:var(--font-display); margin-bottom:4px; }
.case-card__desc { font-size:0.72rem; color:var(--text-secondary); margin-bottom:8px; }
.case-card__meta { display:flex; flex-direction:column; gap:3px; font-size:0.68rem; color:var(--text-muted); }

/* Panel */
.panel-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--border); }
.panel-header h2 { font-size:0.95rem; }
.panel-header__sub { font-size:0.68rem; color:var(--text-muted); margin-top:2px; }
.loading-row, .empty-row { display:flex; align-items:center; gap:10px; padding:32px; color:var(--text-muted); font-size:0.8rem; justify-content:center; }

/* Evidence rows */
.evidence-list { display:flex; flex-direction:column; gap:12px; }
.ev-row-wrapper { display:flex; flex-direction:column; gap:6px; }
.ev-row { display:flex; align-items:flex-start; gap:12px; background:var(--bg-secondary); border:1px solid var(--border); border-radius:var(--radius); padding:12px 14px; }
.ev-row__icon { font-size:1.4rem; flex-shrink:0; margin-top:2px; }
.ev-row__info { flex:1; display:flex; flex-direction:column; gap:4px; min-width:0; }
.ev-row__name { font-size:0.82rem; color:var(--text-primary); font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.ev-row__meta-grid { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.ev-row__meta-grid span { font-size:0.68rem; color:var(--text-muted); }
.ev-row__hash { font-size:0.65rem; color:var(--amber); }
.ev-row__device { font-size:0.68rem; color:var(--text-secondary); }
.ev-row__location { font-size:0.68rem; color:var(--blue-info); }
.ev-row__witness { font-size:0.68rem; color:var(--text-muted); }
.ev-row__actions { display:flex; flex-direction:column; gap:6px; flex-shrink:0; }
.ev-row__download-btn {
  display:inline-flex; align-items:center; gap:6px; padding:8px 14px;
  background:var(--green-ok); color:#fff; border:1px solid var(--green-ok);
  border-radius:var(--radius); font-family:var(--font-display); font-size:0.72rem;
  font-weight:600; letter-spacing:0.08em; text-transform:uppercase;
  cursor:pointer; transition:all 0.2s; white-space:nowrap;
}
.ev-row__download-btn:hover:not(:disabled) { background:#059669; box-shadow:0 0 12px rgba(16,185,129,0.3); }
.ev-row__download-btn:disabled { opacity:0.6; cursor:not-allowed; }
.ev-row__btn { padding:6px 10px; font-size:0.68rem; }
.ev-spinner { width:11px; height:11px; border:2px solid rgba(255,255,255,0.3); border-top-color:#fff; border-radius:50%; animation:spin 0.7s linear infinite; flex-shrink:0; }
.ev-row__dl-msg { font-size:0.7rem; padding:6px 12px; border-radius:var(--radius); border:1px solid; margin-left:50px; }
.ev-row__dl-msg--ok    { color:var(--green-ok);  border-color:rgba(16,185,129,0.3); background:rgba(16,185,129,0.08); }
.ev-row__dl-msg--error { color:var(--red-alert); border-color:rgba(239,68,68,0.3);  background:rgba(239,68,68,0.08); }

/* Reports */
.report-list { display:flex; flex-direction:column; gap:12px; }
.report-card { background:var(--bg-secondary); border:1px solid var(--border); border-radius:var(--radius); padding:14px 16px; }
.report-card__header { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.report-card__title { font-size:0.85rem; color:var(--text-primary); font-weight:500; }
.report-card__summary { font-size:0.75rem; color:var(--text-secondary); margin-bottom:8px; line-height:1.5; }
.report-card__meta { display:flex; flex-wrap:wrap; gap:10px; font-size:0.68rem; color:var(--text-muted); }
.report-card__chain { font-size:0.65rem; color:var(--amber); margin-top:6px; }
.report-card__chain code { font-size:0.65rem; }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.75); backdrop-filter:blur(6px); z-index:9999; display:flex; align-items:center; justify-content:center; padding:24px; overflow-y:auto; }
.modal { width:100%; max-width:640px; max-height:90vh; overflow-y:auto; }
.modal--wide { max-width:700px; }
.modal__title { font-size:1.1rem; margin-bottom:4px; padding-bottom:16px; border-bottom:1px solid var(--border); }
.modal__subtitle { font-size:0.75rem; color:var(--text-muted); margin:12px 0 20px; line-height:1.6; }
.modal__section-title { font-size:0.7rem; font-weight:600; letter-spacing:0.1em; text-transform:uppercase; color:var(--amber); padding-top:8px; border-top:1px solid var(--border); margin-top:4px; }
.modal__error { background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:var(--red-alert); padding:10px 14px; border-radius:var(--radius); font-size:0.78rem; margin-bottom:16px; }
.modal__success { background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:var(--green-ok); padding:12px 16px; border-radius:var(--radius); font-size:0.82rem; margin-bottom:16px; }
.modal__form { display:flex; flex-direction:column; gap:14px; }
.modal__row { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.modal__checkbox-label { display:flex; align-items:flex-start; gap:8px; font-size:0.78rem; color:var(--text-secondary); cursor:pointer; line-height:1.5; }
.modal__checkbox-label input { margin-top:3px; flex-shrink:0; accent-color:var(--amber); }
.modal__actions { display:flex; justify-content:flex-end; gap:12px; padding-top:16px; border-top:1px solid var(--border); }
.modal__icon { width:64px; height:64px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.8rem; margin:0 auto 20px; }
.modal__icon--ok   { background:rgba(16,185,129,0.2); color:var(--green-ok); border:2px solid var(--green-ok); }
.modal__icon--fail { background:rgba(239,68,68,0.2); color:var(--red-alert); border:2px solid var(--red-alert); }
.modal__message { font-size:0.8rem; color:var(--text-secondary); margin-bottom:20px; text-align:center; }
.modal__spinner { width:13px; height:13px; border:2px solid rgba(0,0,0,0.3); border-top-color:var(--bg-primary); border-radius:50%; animation:spin 0.7s linear infinite; flex-shrink:0; }
.spinner { width:22px; height:22px; border:2px solid var(--border); border-top-color:var(--amber); border-radius:50%; animation:spin 0.8s linear infinite; }

@keyframes spin { to { transform:rotate(360deg); } }
@media (max-width:900px) { .analyst-view__layout { grid-template-columns:1fr; } .modal__row { grid-template-columns:1fr; } }
</style>
