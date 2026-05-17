<template>
  <div class="analyst-view container">

    <div class="analyst-view__header fade-up">
      <div>
        <h1>Forensic Analysis</h1>
        <p class="analyst-view__sub">
          Your assigned cases — view evidence, download files, submit analysis reports.
        </p>
      </div>
    </div>

    <!-- Assigned Cases -->
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

    <div v-else class="analyst-view__cases">
      <div
        v-for="c in cases"
        :key="c.id"
        class="case-card card fade-up"
        @click="selectCase(c)"
        :class="{ 'case-card--active': selectedCase?.id === c.id }"
      >
        <div class="case-card__header">
          <code class="case-card__num">{{ c.case_number }}</code>
          <span :class="['badge', `badge--${c.status}`]">{{ c.status }}</span>
        </div>
        <h3 class="case-card__title">{{ c.title }}</h3>
        <p v-if="c.description" class="case-card__desc">{{ c.description }}</p>
        <div class="case-card__meta">
          <span>📁 {{ c.evidence?.length || 0 }} evidence items</span>
          <span>📋 {{ reportCounts[c.id] || 0 }} reports</span>
        </div>
      </div>
    </div>

    <!-- Case Detail Panel -->
    <div v-if="selectedCase" class="analyst-view__detail fade-up">

      <!-- Evidence List -->
      <div class="card">
        <div class="panel-header">
          <h2>Evidence Items</h2>
          <span class="panel-header__sub">Read-only — download for offline analysis</span>
        </div>

        <div v-if="isLoadingEvidence" class="loading-row">
          <div class="spinner" /> Loading evidence…
        </div>

        <div v-else-if="evidence.length === 0" class="empty-row">
          No evidence uploaded yet.
        </div>

        <div v-else class="evidence-list">
          <div v-for="ev in evidence" :key="ev.id" class="ev-row-wrapper">
            <div class="ev-row">
              <span class="ev-row__icon">{{ fileIcon(ev.mime_type) }}</span>
              <div class="ev-row__info">
                <span class="ev-row__name">{{ ev.file_name }}</span>
                <span class="ev-row__meta">
                  {{ formatSize(ev.file_size) }} · {{ ev.evidence_type }} ·
                  <span :class="['badge', `badge--${ev.status}`]">{{ ev.status }}</span>
                </span>
                <code class="ev-row__hash">SHA-256: {{ ev.sha256_hash?.slice(0,32) }}…</code>
              </div>
              <div class="ev-row__actions">
                <button
                  class="btn ev-row__download-btn"
                  :disabled="downloadingIds.has(ev.id)"
                  @click="downloadEvidence(ev)"
                >
                  <span v-if="downloadingIds.has(ev.id)" class="ev-row__spinner" />
                  <span v-else>⬇</span>
                  {{ downloadingIds.has(ev.id) ? 'Downloading…' : `Download (${formatSize(ev.file_size)})` }}
                </button>
                <button class="btn btn--ghost ev-row__btn" @click="verifyEvidence(ev)">
                  ✓ Verify
                </button>
              </div>
            </div>
            <div
              v-if="downloadMessages[ev.id]"
              :class="['ev-row__dl-msg', `ev-row__dl-msg--${downloadMessages[ev.id].type}`]"
            >
              {{ downloadMessages[ev.id].text }}
            </div>
          </div>
        </div>
      </div>

      <!-- Reports -->
      <div class="card" style="margin-top:20px">
        <div class="panel-header">
          <h2>Analysis Reports</h2>
          <button class="btn btn--primary" @click="showReportModal = true">
            + Submit Report
          </button>
        </div>

        <div v-if="reports.length === 0" class="empty-row">
          No reports submitted yet.
        </div>

        <div v-else class="report-list">
          <div v-for="r in reports" :key="r.id" class="report-row">
            <div class="report-row__header">
              <span class="report-row__title">{{ r.title }}</span>
              <span :class="['badge', r.status === 'submitted' ? 'badge--verified' : 'badge--pending']">
                {{ r.status }}
              </span>
            </div>
            <p class="report-row__summary">{{ r.summary }}</p>
            <span class="report-row__date">{{ formatDate(r.submitted_at || r.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Submit Report Modal -->
    <Teleport to="body">
      <div v-if="showReportModal" class="modal-overlay" @click.self="showReportModal = false">
        <div class="modal card fade-up">
          <h2 class="modal__title">🔬 Submit Analysis Report</h2>
          <p class="modal__subtitle">
            Case: <strong>{{ selectedCase?.case_number }}</strong> — {{ selectedCase?.title }}
          </p>

          <div v-if="reportError"   class="modal__error">{{ reportError }}</div>
          <div v-if="reportSuccess" class="modal__success">✓ Report submitted successfully.</div>

          <div v-if="!reportSuccess" class="modal__form">
            <div class="form-group">
              <label class="form-label">Report Title *</label>
              <input v-model="reportForm.title" class="form-input" required
                placeholder="e.g. Digital Forensics Analysis — Bank Robbery Case" />
            </div>
            <div class="form-group">
              <label class="form-label">Executive Summary *</label>
              <textarea v-model="reportForm.summary" class="form-input" rows="3" required
                placeholder="Brief overview of findings…" />
            </div>
            <div class="form-group">
              <label class="form-label">Methodology</label>
              <textarea v-model="reportForm.methodology" class="form-input" rows="3"
                placeholder="Tools used, analysis approach…" />
            </div>
            <div class="form-group">
              <label class="form-label">Findings</label>
              <textarea v-model="reportForm.findings" class="form-input" rows="4"
                placeholder="Detailed findings from forensic analysis…" />
            </div>
            <div class="form-group">
              <label class="form-label">Conclusion</label>
              <textarea v-model="reportForm.conclusion" class="form-input" rows="3"
                placeholder="Overall conclusion and recommendations…" />
            </div>
            <div class="modal__actions">
              <button class="btn btn--ghost" @click="showReportModal = false">Cancel</button>
              <button
                class="btn btn--primary"
                :disabled="!reportForm.title || !reportForm.summary || isSubmittingReport"
                @click="submitReport"
              >
                <span v-if="isSubmittingReport" class="modal__spinner" />
                {{ isSubmittingReport ? 'Submitting…' : 'Submit Report' }}
              </button>
            </div>
          </div>
          <div v-else class="modal__actions">
            <button class="btn btn--primary" @click="showReportModal = false; reportSuccess = false">
              Close
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Verify Result Modal -->
    <Teleport to="body">
      <div v-if="verifyResult" class="modal-overlay" @click.self="verifyResult = null">
        <div class="modal card fade-up" style="text-align:center">
          <div class="modal__icon" :class="verifyResult.is_valid ? 'modal__icon--ok' : 'modal__icon--fail'">
            {{ verifyResult.is_valid ? '✓' : '✕' }}
          </div>
          <h2 class="modal__title">{{ verifyResult.is_valid ? 'Verified' : 'Tampered!' }}</h2>
          <p class="modal__message">{{ verifyResult.message }}</p>
          <button class="btn btn--ghost" style="width:100%;justify-content:center" @click="verifyResult = null">
            Close
          </button>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api } from '../services/apiService'

const cases          = ref([])
const selectedCase   = ref(null)
const evidence       = ref([])
const reports        = ref([])
const reportCounts   = ref({})
const isLoading      = ref(true)
const isLoadingEvidence = ref(false)
const showReportModal   = ref(false)
const reportError    = ref('')
const reportSuccess  = ref(false)
const isSubmittingReport = ref(false)
const verifyResult      = ref(null)
const downloadingIds    = ref(new Set())
const downloadMessages  = ref({})

const reportForm = reactive({
  title: '', summary: '', methodology: '', findings: '', conclusion: ''
})

onMounted(async () => {
  try {
    const data = await api.get('/cases/')
    cases.value = data.items || []
  } catch {}
  isLoading.value = false
})

async function selectCase(c) {
  selectedCase.value = c
  isLoadingEvidence.value = true
  evidence.value = []
  reports.value  = []
  try {
    const evData = await api.get(`/evidence/case/${c.id}`)
    evidence.value = evData.items || []
  } catch {}
  try {
    const repData = await api.get(`/cases/${c.id}/reports`)
    reports.value = repData.items || []
    reportCounts.value[c.id] = reports.value.length
  } catch {}
  isLoadingEvidence.value = false
}

async function downloadEvidence(ev) {
  if (ev._downloading) return
  ev._downloading = true

  // Track download state per evidence item
  downloadingIds.value.add(ev.id)

  try {
    const token = localStorage.getItem('access_token')

    // Must use fetch with Authorization header — simple <a href> won't send the JWT
    const response = await fetch(
      `http://localhost:8000/api/v1/evidence/${ev.id}/download`,
      {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      }
    )

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || `Download failed: HTTP ${response.status}`)
    }

    // Get the correct filename from Content-Disposition header
    const disposition = response.headers.get('Content-Disposition')
    let filename = ev.file_name
    if (disposition) {
      const match = disposition.match(/filename[^;=\n]*=((['"]).+?\2|[^;\n]*)/)
      if (match) filename = match[1].replace(/['"]/g, '')
    }

    // Convert response to blob and trigger browser download
    const blob = await response.blob()
    const url  = window.URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    // Show success message
    downloadMessages.value[ev.id] = {
      type: 'ok',
      text: `✓ "${filename}" downloaded. Logged in audit trail.`
    }
    setTimeout(() => { delete downloadMessages.value[ev.id] }, 5000)

  } catch (err) {
    downloadMessages.value[ev.id] = {
      type: 'error',
      text: `Download failed: ${err.message}`
    }
    setTimeout(() => { delete downloadMessages.value[ev.id] }, 5000)
  } finally {
    downloadingIds.value.delete(ev.id)
    ev._downloading = false
  }
}

async function verifyEvidence(ev) {
  try {
    verifyResult.value = await api.post(`/evidence/${ev.id}/verify`)
  } catch (err) {
    alert(err.message || 'Verification failed')
  }
}

async function submitReport() {
  reportError.value   = ''
  isSubmittingReport.value = true
  try {
    await api.post(`/cases/${selectedCase.value.id}/reports`, { ...reportForm })
    reportSuccess.value = true
    Object.assign(reportForm, { title:'', summary:'', methodology:'', findings:'', conclusion:'' })
    // Refresh reports
    const data = await api.get(`/cases/${selectedCase.value.id}/reports`)
    reports.value = data.items || []
    reportCounts.value[selectedCase.value.id] = reports.value.length
  } catch (err) {
    reportError.value = err.message || 'Failed to submit report.'
  } finally {
    isSubmittingReport.value = false
  }
}

function fileIcon(mime = '') {
  if (mime.startsWith('image/')) return '🖼'
  if (mime.startsWith('video/')) return '🎥'
  if (mime.startsWith('audio/')) return '🎙'
  if (mime.includes('pdf'))      return '📄'
  return '💾'
}

function formatSize(bytes = 0) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024*1024) return `${(bytes/1024).toFixed(1)} KB`
  return `${(bytes/(1024*1024)).toFixed(2)} MB`
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
.analyst-view__header { display:flex; justify-content:space-between; margin-bottom:28px; }
.analyst-view__sub { font-size:0.78rem; color:var(--text-muted); margin-top:4px; }
.analyst-view__loading,
.analyst-view__empty {
  display:flex; flex-direction:column; align-items:center;
  gap:12px; padding:48px; color:var(--text-muted);
}
.analyst-view__cases {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}
.case-card { cursor:pointer; transition: border-color 0.2s; }
.case-card:hover { border-color: var(--amber); }
.case-card--active { border-color: var(--amber); box-shadow: var(--shadow-glow); }
.case-card__header { display:flex; justify-content:space-between; margin-bottom:8px; }
.case-card__num { font-size:0.72rem; color:var(--amber); }
.case-card__title { font-size:1rem; font-family:var(--font-display); margin-bottom:6px; }
.case-card__desc { font-size:0.75rem; color:var(--text-secondary); margin-bottom:8px; }
.case-card__meta { display:flex; gap:16px; font-size:0.7rem; color:var(--text-muted); }

.panel-header {
  display:flex; justify-content:space-between; align-items:center;
  margin-bottom:20px; padding-bottom:12px; border-bottom:1px solid var(--border);
}
.panel-header h2 { font-size:1rem; }
.panel-header__sub { font-size:0.7rem; color:var(--text-muted); }

.loading-row, .empty-row {
  display:flex; align-items:center; gap:10px;
  padding:24px; color:var(--text-muted); font-size:0.8rem;
}

.evidence-list { display:flex; flex-direction:column; gap:12px; }
.ev-row {
  display:flex; align-items:center; gap:14px;
  padding:12px 16px;
  background:var(--bg-secondary); border:1px solid var(--border);
  border-radius:var(--radius);
}
.ev-row__icon { font-size:1.4rem; flex-shrink:0; }
.ev-row__info { flex:1; display:flex; flex-direction:column; gap:2px; min-width:0; }
.ev-row__name { font-size:0.82rem; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.ev-row__meta { font-size:0.7rem; color:var(--text-muted); display:flex; align-items:center; gap:6px; }
.ev-row__hash { font-size:0.65rem; color:var(--amber); }
.ev-row__actions { display:flex; gap:8px; flex-shrink:0; align-items:center; flex-wrap:wrap; }
.ev-row__btn { padding:5px 10px; font-size:0.68rem; }

/* Download button — prominent green for analysts */
.ev-row__download-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--green-ok);
  color: #fff;
  border: 1px solid var(--green-ok);
  border-radius: var(--radius);
  font-family: var(--font-display);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.ev-row__download-btn:hover:not(:disabled) {
  background: #059669;
  box-shadow: 0 0 12px rgba(16,185,129,0.35);
}
.ev-row__download-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.ev-row__spinner {
  width: 12px; height: 12px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
.ev-row-wrapper { display: flex; flex-direction: column; gap: 6px; }
.ev-row__dl-msg {
  font-size: 0.7rem;
  padding: 6px 12px;
  border-radius: var(--radius);
  border: 1px solid;
  margin-left: 48px;
}
.ev-row__dl-msg--ok    { color:var(--green-ok);   border-color:rgba(16,185,129,0.3); background:rgba(16,185,129,0.08); }
.ev-row__dl-msg--error { color:var(--red-alert);  border-color:rgba(239,68,68,0.3);  background:rgba(239,68,68,0.08); }

.report-list { display:flex; flex-direction:column; gap:12px; }
.report-row {
  padding:14px 16px; background:var(--bg-secondary);
  border:1px solid var(--border); border-radius:var(--radius);
}
.report-row__header { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.report-row__title { font-size:0.88rem; color:var(--text-primary); font-weight:500; }
.report-row__summary { font-size:0.75rem; color:var(--text-secondary); margin-bottom:6px; }
.report-row__date { font-size:0.68rem; color:var(--text-muted); }

.spinner {
  width:22px; height:22px; border:2px solid var(--border);
  border-top-color:var(--amber); border-radius:50%;
  animation:spin 0.8s linear infinite;
}
.modal-overlay {
  position:fixed; inset:0; background:rgba(0,0,0,0.75);
  backdrop-filter:blur(6px); z-index:9999;
  display:flex; align-items:center; justify-content:center; padding:24px;
}
.modal { width:100%; max-width:560px; }
.modal__title { font-size:1.1rem; margin-bottom:4px; padding-bottom:16px; border-bottom:1px solid var(--border); }
.modal__subtitle { font-size:0.75rem; color:var(--text-muted); margin:12px 0 20px; }
.modal__error { background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:var(--red-alert); padding:10px 14px; border-radius:var(--radius); font-size:0.78rem; margin-bottom:16px; }
.modal__success { background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:var(--green-ok); padding:12px 16px; border-radius:var(--radius); font-size:0.82rem; margin-bottom:16px; }
.modal__form { display:flex; flex-direction:column; gap:16px; }
.modal__actions { display:flex; justify-content:flex-end; gap:12px; padding-top:16px; border-top:1px solid var(--border); }
.modal__icon { width:64px; height:64px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.8rem; margin:0 auto 20px; }
.modal__icon--ok   { background:rgba(16,185,129,0.2); color:var(--green-ok); border:2px solid var(--green-ok); }
.modal__icon--fail { background:rgba(239,68,68,0.2);  color:var(--red-alert); border:2px solid var(--red-alert); }
.modal__message { font-size:0.8rem; color:var(--text-secondary); margin-bottom:20px; text-align:center; }
.modal__spinner { width:13px; height:13px; border:2px solid rgba(0,0,0,0.3); border-top-color:var(--bg-primary); border-radius:50%; animation:spin 0.7s linear infinite; flex-shrink:0; }
@keyframes spin { to { transform:rotate(360deg); } }
</style>
