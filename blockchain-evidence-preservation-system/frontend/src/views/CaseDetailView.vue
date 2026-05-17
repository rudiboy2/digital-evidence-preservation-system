<template>
  <div class="case-detail container" v-if="caseData">

    <!-- Back -->
    <div class="case-detail__back">
      <RouterLink to="/dashboard" class="back-link">← Dashboard</RouterLink>
    </div>

    <!-- Header -->
    <div class="case-detail__header fade-up">
      <div class="case-detail__header-left">
        <code class="case-detail__number">{{ caseData.case_number }}</code>
        <h1 class="case-detail__title">{{ caseData.title }}</h1>
        <p v-if="caseData.description" class="case-detail__description">
          {{ caseData.description }}
        </p>
      </div>
      <div class="case-detail__header-right">
        <span :class="['badge', `badge--${caseData.status}`]">{{ caseData.status }}</span>
        <span :class="['badge', `badge--${priorityClass(caseData.priority)}`]">{{ caseData.priority }}</span>
        <RouterLink :to="{ name: 'chain-of-custody', params: { id: caseId } }" class="btn btn--ghost">
          ⛓ Chain of Custody
        </RouterLink>
        <RouterLink
          v-if="caseData.status !== 'closed' && canUpload"
          :to="{ name: 'evidence-upload', params: { id: caseId } }"
          class="btn btn--primary"
        >
          + Upload Evidence
        </RouterLink>
      </div>
    </div>

    <!-- Meta grid -->
    <div class="case-detail__meta card fade-up" style="animation-delay:0.1s">
      <div class="meta-item">
        <span class="meta-item__label">Jurisdiction</span>
        <span class="meta-item__val">{{ caseData.jurisdiction || '—' }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-item__label">Created</span>
        <span class="meta-item__val">{{ formatDate(caseData.created_at) }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-item__label">Incident Date</span>
        <span class="meta-item__val">{{ formatDate(caseData.incident_date) }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-item__label">Evidence Items</span>
        <span class="meta-item__val meta-item__val--accent">{{ evidence.length }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-item__label">Status</span>
        <span :class="['badge', `badge--${caseData.status}`]">{{ caseData.status }}</span>
      </div>
    </div>

    <!-- ================================================================ -->
    <!-- ASSIGNMENT PANEL — Investigator and Admin only                    -->
    <!-- ================================================================ -->
    <div v-if="canAssign" class="assignment-panel card fade-up" style="animation-delay:0.15s">
      <div class="assignment-panel__header">
        <h2 class="assignment-panel__title">👥 Case Team Assignment</h2>
        <p class="assignment-panel__sub">
          Assign officers to upload evidence and analysts to perform forensic analysis.
        </p>
      </div>

      <div class="assignment-panel__grid">

        <!-- Officers Column -->
        <div class="assignment-col">
          <div class="assignment-col__header">
            <span class="assignment-col__icon">👮</span>
            <div>
              <h3 class="assignment-col__title">Officers</h3>
              <p class="assignment-col__desc">Can upload evidence to this case</p>
            </div>
          </div>

          <!-- Assigned officers list -->
          <div class="assigned-list">
            <div
              v-for="officer in caseData.assigned_officers"
              :key="officer.id"
              class="assigned-chip"
            >
              <div class="assigned-chip__avatar">{{ officer.full_name?.charAt(0) }}</div>
              <div class="assigned-chip__info">
                <span class="assigned-chip__name">{{ officer.full_name }}</span>
                <span class="assigned-chip__badge">{{ officer.badge_number || 'No badge' }}</span>
              </div>
              <span class="assigned-chip__role-tag assigned-chip__role-tag--officer">Officer</span>
            </div>
            <div v-if="!caseData.assigned_officers?.length" class="assigned-empty">
              No officers assigned yet
            </div>
          </div>

          <!-- Assign officer form -->
          <div class="assignment-form">
            <select v-model="newOfficerId" class="form-input assignment-select">
              <option value="">— Select officer to assign —</option>
              <option
                v-for="u in availableOfficers"
                :key="u.id"
                :value="u.id"
              >
                {{ u.full_name }} {{ u.badge_number ? `(${u.badge_number})` : '' }} — {{ u.department || 'No dept' }}
              </option>
            </select>
            <button
              class="btn btn--primary assignment-btn"
              :disabled="!newOfficerId || isAssigningOfficer"
              @click="assignOfficer"
            >
              <span v-if="isAssigningOfficer" class="btn-spinner" />
              {{ isAssigningOfficer ? 'Assigning…' : '+ Assign Officer' }}
            </button>
            <div v-if="officerAssignMsg" :class="['assign-msg', officerAssignMsg.type === 'error' ? 'assign-msg--error' : 'assign-msg--ok']">
              {{ officerAssignMsg.text }}
            </div>
          </div>
        </div>

        <!-- Divider -->
        <div class="assignment-divider" />

        <!-- Analysts Column -->
        <div class="assignment-col">
          <div class="assignment-col__header">
            <span class="assignment-col__icon">🔬</span>
            <div>
              <h3 class="assignment-col__title">Forensic Analysts</h3>
              <p class="assignment-col__desc">Can analyze evidence and submit reports</p>
            </div>
          </div>

          <!-- Assigned analysts list -->
          <div class="assigned-list">
            <div
              v-for="analyst in caseData.assigned_analysts"
              :key="analyst.id"
              class="assigned-chip"
            >
              <div class="assigned-chip__avatar assigned-chip__avatar--analyst">
                {{ analyst.full_name?.charAt(0) }}
              </div>
              <div class="assigned-chip__info">
                <span class="assigned-chip__name">{{ analyst.full_name }}</span>
                <span class="assigned-chip__badge">{{ analyst.department || 'Forensics' }}</span>
              </div>
              <span class="assigned-chip__role-tag assigned-chip__role-tag--analyst">Analyst</span>
            </div>
            <div v-if="!caseData.assigned_analysts?.length" class="assigned-empty">
              No analysts assigned yet
            </div>
          </div>

          <!-- Assign analyst form -->
          <div class="assignment-form">
            <select v-model="newAnalystId" class="form-input assignment-select">
              <option value="">— Select analyst to assign —</option>
              <option
                v-for="u in availableAnalysts"
                :key="u.id"
                :value="u.id"
              >
                {{ u.full_name }} — {{ u.department || 'Forensics' }}
              </option>
            </select>
            <button
              class="btn btn--primary assignment-btn assignment-btn--analyst"
              :disabled="!newAnalystId || isAssigningAnalyst"
              @click="assignAnalyst"
            >
              <span v-if="isAssigningAnalyst" class="btn-spinner" />
              {{ isAssigningAnalyst ? 'Assigning…' : '+ Assign Analyst' }}
            </button>
            <div v-if="analystAssignMsg" :class="['assign-msg', analystAssignMsg.type === 'error' ? 'assign-msg--error' : 'assign-msg--ok']">
              {{ analystAssignMsg.text }}
            </div>
          </div>
        </div>

      </div>

      <!-- Workflow hint -->
      <div class="workflow-hint">
        <div class="workflow-step">
          <span class="workflow-step__num">1</span>
          <span>Investigator creates case</span>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step">
          <span class="workflow-step__num">2</span>
          <span>Assign officers to upload evidence</span>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step">
          <span class="workflow-step__num">3</span>
          <span>Assign analysts for forensic analysis</span>
        </div>
        <div class="workflow-arrow">→</div>
        <div class="workflow-step">
          <span class="workflow-step__num">4</span>
          <span>Analyst submits report</span>
        </div>
      </div>
    </div>

    <!-- Evidence section -->
    <section class="case-detail__section fade-up" style="animation-delay:0.2s">
      <h2 class="case-detail__section-title">Evidence Items</h2>

      <div v-if="isLoadingEvidence" class="case-detail__loading">
        <div class="case-detail__spinner" />
      </div>

      <div v-else-if="evidence.length === 0" class="case-detail__empty">
        <span style="font-size:2rem">⬡</span>
        <p>No evidence uploaded yet.</p>
        <p v-if="canAssign" style="font-size:0.75rem;color:var(--text-muted)">
          Assign an officer above, then they can upload evidence to this case.
        </p>
        <RouterLink
          v-if="caseData.status !== 'closed' && canUpload"
          :to="{ name: 'evidence-upload', params: { id: caseId } }"
          class="btn btn--primary"
        >
          Upload First Evidence
        </RouterLink>
      </div>

      <div v-else class="evidence-grid">
        <EvidenceCard
          v-for="ev in evidence"
          :key="ev.id"
          :evidence="ev"
          @verify="verifyEvidence"
          @custody="showCustodyChain"
          @transfer="openTransferModal"
        />
      </div>
    </section>

    <!-- ================================================================ -->
    <!-- TRANSFER CUSTODY MODAL                                             -->
    <!-- ================================================================ -->
    <Teleport to="body">
      <div v-if="transferModal.show" class="modal-overlay" @click.self="closeTransfer">
        <div class="modal card fade-up">
          <h2 class="modal__title">↔ Transfer Custody</h2>
          <p class="modal__subtitle">
            Transfer custody of this evidence to another officer or analyst.
            Permanently recorded on the blockchain.
          </p>

          <div class="modal__evidence-info" v-if="transferModal.evidence">
            <span class="modal__evidence-icon">{{ fileIcon(transferModal.evidence.mime_type) }}</span>
            <div>
              <div class="modal__evidence-name">{{ transferModal.evidence.file_name }}</div>
              <code class="modal__evidence-hash">{{ transferModal.evidence.sha256_hash?.slice(0,24) }}…</code>
            </div>
          </div>

          <div v-if="transferModal.error"   class="modal__error">{{ transferModal.error }}</div>
          <div v-if="transferModal.success" class="modal__success">
            ✓ Custody transferred and recorded on blockchain.
          </div>

          <div v-if="!transferModal.success" class="modal__form">
            <div class="form-group">
              <label class="form-label">Transfer To *</label>
              <select v-model="transferModal.toUserId" class="form-input">
                <option value="">— Select recipient —</option>
                <optgroup label="Officers">
                  <option v-for="u in officersAndAnalysts.filter(u => u.role?.name === 'officer')" :key="u.id" :value="u.id">
                    👮 {{ u.full_name }} {{ u.badge_number ? `(${u.badge_number})` : '' }}
                  </option>
                </optgroup>
                <optgroup label="Analysts">
                  <option v-for="u in officersAndAnalysts.filter(u => u.role?.name === 'analyst')" :key="u.id" :value="u.id">
                    🔬 {{ u.full_name }} — {{ u.department || 'Forensics' }}
                  </option>
                </optgroup>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Location</label>
              <input v-model="transferModal.location" class="form-input" placeholder="e.g. Forensic Lab, Evidence Room B" />
            </div>
            <div class="form-group">
              <label class="form-label">Notes / Reason</label>
              <textarea v-model="transferModal.notes" class="form-input" rows="3"
                placeholder="e.g. Transferred to forensic analyst for DNA examination" />
            </div>
            <div class="modal__actions">
              <button class="btn btn--ghost" @click="closeTransfer">Cancel</button>
              <button class="btn btn--primary" :disabled="!transferModal.toUserId || transferModal.isLoading" @click="submitTransfer">
                <span v-if="transferModal.isLoading" class="modal__spinner" />
                {{ transferModal.isLoading ? 'Transferring…' : '↔ Transfer Custody' }}
              </button>
            </div>
          </div>
          <div v-else class="modal__actions">
            <button class="btn btn--primary" @click="closeTransfer">Close</button>
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
          <h2 class="modal__title">{{ verifyResult.is_valid ? 'Evidence Verified' : 'Integrity Warning' }}</h2>
          <p class="modal__message">{{ verifyResult.message }}</p>
          <div class="modal__data">
            <div class="modal__data-row"><span>Stored Hash</span><code>{{ verifyResult.db_hash?.slice(0,24) }}…</code></div>
            <div class="modal__data-row"><span>Computed Hash</span><code>{{ verifyResult.computed_hash?.slice(0,24) }}…</code></div>
          </div>
          <button class="btn btn--ghost" style="width:100%;justify-content:center" @click="verifyResult = null">Close</button>
        </div>
      </div>
    </Teleport>

    <!-- Custody Chain Modal -->
    <Teleport to="body">
      <div v-if="custodyChain" class="modal-overlay" @click.self="custodyChain = null">
        <div class="modal modal--wide card fade-up">
          <h2 class="modal__title">⛓ Chain of Custody</h2>
          <div class="custody-timeline">
            <div v-for="(entry, i) in custodyChain" :key="entry.id" class="custody-item">
              <div class="custody-item__line" v-if="i < custodyChain.length - 1" />
              <div class="custody-item__dot" />
              <div class="custody-item__content">
                <div class="custody-item__header">
                  <span class="custody-item__action">{{ entry.action }}</span>
                  <span class="custody-item__role" v-if="entry.performed_by_role">{{ entry.performed_by_role }}</span>
                  <span class="custody-item__time">{{ formatDate(entry.timestamp) }}</span>
                </div>
                <p v-if="entry.notes" class="custody-item__notes">{{ entry.notes }}</p>
                <div v-if="entry.ip_address" class="custody-item__ip">IP: {{ entry.ip_address }}</div>
                <code v-if="entry.blockchain_tx_hash" class="custody-item__tx">TX: {{ entry.blockchain_tx_hash }}</code>
              </div>
            </div>
          </div>
          <button class="btn btn--ghost" style="width:100%;justify-content:center;margin-top:16px" @click="custodyChain = null">Close</button>
        </div>
      </div>
    </Teleport>

  </div>

  <div v-else class="container" style="padding:60px 24px;text-align:center;color:var(--text-muted);">
    <div v-if="isLoadingCase">Loading case…</div>
    <div v-else>Case not found.</div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import EvidenceCard from '../components/EvidenceCard.vue'

const route  = useRoute()
const caseId = route.params.id

// ── Role permissions ───────────────────────────────────────────────────────
const userRole    = computed(() => localStorage.getItem('user_role') || '')
const canUpload   = computed(() => ['admin', 'investigator', 'officer'].includes(userRole.value))
const canAssign   = computed(() => ['admin', 'investigator'].includes(userRole.value))

// ── State ──────────────────────────────────────────────────────────────────
const caseData          = ref(null)
const evidence          = ref([])
const allUsers          = ref([])
const isLoadingCase     = ref(true)
const isLoadingEvidence = ref(true)
const verifyResult      = ref(null)
const custodyChain      = ref(null)

// Assignment state
const newOfficerId       = ref('')
const newAnalystId       = ref('')
const isAssigningOfficer = ref(false)
const isAssigningAnalyst = ref(false)
const officerAssignMsg   = ref(null)
const analystAssignMsg   = ref(null)

// Transfer modal
const transferModal = reactive({
  show: false, evidence: null,
  toUserId: '', location: '', notes: '',
  isLoading: false, error: '', success: false,
})

// ── Computed user lists ────────────────────────────────────────────────────
const availableOfficers = computed(() => {
  const assignedIds = (caseData.value?.assigned_officers || []).map(u => u.id)
  return allUsers.value.filter(u =>
    u.role?.name === 'officer' && !assignedIds.includes(u.id)
  )
})

const availableAnalysts = computed(() => {
  const assignedIds = (caseData.value?.assigned_analysts || []).map(u => u.id)
  return allUsers.value.filter(u =>
    u.role?.name === 'analyst' && !assignedIds.includes(u.id)
  )
})

const officersAndAnalysts = computed(() =>
  allUsers.value.filter(u => ['officer', 'analyst'].includes(u.role?.name))
)

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  await loadCase()
  await loadEvidence()
  if (canAssign.value) await loadUsers()
})

async function loadCase() {
  isLoadingCase.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(`http://localhost:8000/api/v1/cases/${caseId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (resp.ok) caseData.value = await resp.json()
  } catch {} finally { isLoadingCase.value = false }
}

async function loadEvidence() {
  isLoadingEvidence.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(`http://localhost:8000/api/v1/evidence/case/${caseId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      evidence.value = data.items || []
    }
  } catch {} finally { isLoadingEvidence.value = false }
}

async function loadUsers() {
  try {
    const token = localStorage.getItem('access_token')

    // Fetch officers and analysts separately using dedicated endpoints
    const [officersResp, analystsResp] = await Promise.all([
      fetch('http://localhost:8000/api/v1/users/officers', {
        headers: { 'Authorization': `Bearer ${token}` }
      }),
      fetch('http://localhost:8000/api/v1/users/analysts', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
    ])

    const officers = officersResp.ok ? (await officersResp.json()).items || [] : []
    const analysts = analystsResp.ok ? (await analystsResp.json()).items || [] : []

    // Merge into allUsers
    allUsers.value = [...officers, ...analysts]

    console.log(`Loaded ${officers.length} officers and ${analysts.length} analysts`)
  } catch (err) {
    console.error('Failed to load users:', err)
  }
}

// ── Assign Officer ─────────────────────────────────────────────────────────
async function assignOfficer() {
  officerAssignMsg.value = null
  isAssigningOfficer.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(
      `http://localhost:8000/api/v1/cases/${caseId}/assign-officer/${newOfficerId.value}`,
      { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } }
    )
    const data = await resp.json()
    if (!resp.ok) {
      officerAssignMsg.value = { type: 'error', text: data.detail || 'Assignment failed.' }
    } else {
      officerAssignMsg.value = { type: 'ok', text: data.message || 'Officer assigned successfully.' }
      newOfficerId.value = ''
      await loadCase() // Refresh to show new assignment
      setTimeout(() => { officerAssignMsg.value = null }, 4000)
    }
  } catch (err) {
    officerAssignMsg.value = { type: 'error', text: 'Failed to assign officer.' }
  } finally {
    isAssigningOfficer.value = false
  }
}

// ── Assign Analyst ─────────────────────────────────────────────────────────
async function assignAnalyst() {
  analystAssignMsg.value = null
  isAssigningAnalyst.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(
      `http://localhost:8000/api/v1/cases/${caseId}/assign-analyst/${newAnalystId.value}`,
      { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } }
    )
    const data = await resp.json()
    if (!resp.ok) {
      analystAssignMsg.value = { type: 'error', text: data.detail || 'Assignment failed.' }
    } else {
      analystAssignMsg.value = { type: 'ok', text: data.message || 'Analyst assigned successfully.' }
      newAnalystId.value = ''
      await loadCase()
      setTimeout(() => { analystAssignMsg.value = null }, 4000)
    }
  } catch {
    analystAssignMsg.value = { type: 'error', text: 'Failed to assign analyst.' }
  } finally {
    isAssigningAnalyst.value = false
  }
}

// ── Verify ─────────────────────────────────────────────────────────────────
async function verifyEvidence(evidenceId) {
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(`http://localhost:8000/api/v1/evidence/${evidenceId}/verify`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    verifyResult.value = await resp.json()
  } catch (err) {
    alert('Verification failed.')
  }
}

// ── Custody Chain ──────────────────────────────────────────────────────────
async function showCustodyChain(evidenceId) {
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(`http://localhost:8000/api/v1/evidence/${evidenceId}/custody-chain`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await resp.json()
    custodyChain.value = data.custody_chain
  } catch {
    alert('Could not load custody chain.')
  }
}

// ── Transfer Modal ─────────────────────────────────────────────────────────
function openTransferModal(evidenceId) {
  const ev = evidence.value.find(e => e.id === evidenceId)
  Object.assign(transferModal, {
    show: true, evidence: ev,
    toUserId: '', location: '', notes: '',
    isLoading: false, error: '', success: false,
  })
}

function closeTransfer() {
  transferModal.show = false
  if (transferModal.success) loadEvidence()
}

async function submitTransfer() {
  transferModal.error     = ''
  transferModal.isLoading = true
  try {
    const token = localStorage.getItem('access_token')
    const params = new URLSearchParams({
      to_officer_id: transferModal.toUserId,
      notes:         transferModal.notes || '',
      location:      transferModal.location || '',
    })
    const resp = await fetch(
      `http://localhost:8000/api/v1/evidence/${transferModal.evidence.id}/transfer?${params}`,
      { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } }
    )
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || 'Transfer failed.')
    }
    transferModal.success = true
  } catch (err) {
    transferModal.error = err.message || 'Transfer failed.'
  } finally {
    transferModal.isLoading = false
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function fileIcon(mime = '') {
  if (mime?.startsWith('image/')) return '🖼'
  if (mime?.startsWith('video/')) return '🎥'
  if (mime?.startsWith('audio/')) return '🎙'
  if (mime?.includes('pdf'))      return '📄'
  return '💾'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function priorityClass(p) {
  return { critical: 'tampered', high: 'tampered', medium: 'pending', low: 'closed' }[p] || 'closed'
}
</script>

<style scoped>
.case-detail { padding: 32px 24px; }

.case-detail__back { margin-bottom: 20px; }
.back-link { font-size: 0.78rem; color: var(--text-muted); }
.back-link:hover { color: var(--amber); text-decoration: none; }

.case-detail__header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 24px; margin-bottom: 24px; flex-wrap: wrap;
}
.case-detail__number { font-size: 0.78rem; color: var(--amber); display: block; margin-bottom: 8px; }
.case-detail__title  { font-size: 2rem; }
.case-detail__description { font-size: 0.82rem; color: var(--text-secondary); margin-top: 8px; max-width: 600px; }

.case-detail__header-right {
  display: flex; align-items: center; gap: 10px;
  flex-shrink: 0; flex-wrap: wrap; justify-content: flex-end;
}

/* Meta */
.case-detail__meta {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px,1fr));
  gap: 0; padding: 0; margin-bottom: 20px;
}
.meta-item { padding: 16px 20px; display: flex; flex-direction: column; gap: 4px; border-right: 1px solid var(--border); }
.meta-item:last-child { border-right: none; }
.meta-item__label { font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-muted); }
.meta-item__val { font-size: 0.88rem; color: var(--text-primary); }
.meta-item__val--accent { color: var(--amber); font-weight: 700; }

/* ── Assignment Panel ──────────────────────────────────────────────────── */
.assignment-panel { margin-bottom: 24px; }

.assignment-panel__header { margin-bottom: 20px; }
.assignment-panel__title { font-size: 1rem; margin-bottom: 4px; }
.assignment-panel__sub { font-size: 0.75rem; color: var(--text-muted); }

.assignment-panel__grid {
  display: grid; grid-template-columns: 1fr auto 1fr; gap: 0;
  margin-bottom: 20px;
}

.assignment-divider {
  width: 1px; background: var(--border); margin: 0 24px;
}

.assignment-col { display: flex; flex-direction: column; gap: 14px; }

.assignment-col__header {
  display: flex; align-items: flex-start; gap: 12px;
}
.assignment-col__icon { font-size: 1.5rem; flex-shrink: 0; margin-top: 2px; }
.assignment-col__title { font-size: 0.88rem; font-family: var(--font-display); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-primary); }
.assignment-col__desc  { font-size: 0.72rem; color: var(--text-muted); margin-top: 2px; }

/* Assigned list */
.assigned-list { display: flex; flex-direction: column; gap: 8px; min-height: 60px; }

.assigned-chip {
  display: flex; align-items: center; gap: 10px;
  background: var(--bg-elevated); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 8px 12px;
}
.assigned-chip__avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--blue-info); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 0.8rem; font-weight: 700;
  flex-shrink: 0;
}
.assigned-chip__avatar--analyst { background: var(--green-ok); }
.assigned-chip__info { flex: 1; display: flex; flex-direction: column; gap: 1px; }
.assigned-chip__name  { font-size: 0.8rem; color: var(--text-primary); font-weight: 500; }
.assigned-chip__badge { font-size: 0.65rem; color: var(--text-muted); }
.assigned-chip__role-tag {
  font-size: 0.6rem; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; padding: 2px 8px;
  border-radius: 10px; border: 1px solid; flex-shrink: 0;
}
.assigned-chip__role-tag--officer { color: var(--blue-info); border-color: rgba(59,130,246,0.3); background: rgba(59,130,246,0.1); }
.assigned-chip__role-tag--analyst { color: var(--green-ok); border-color: rgba(16,185,129,0.3); background: rgba(16,185,129,0.1); }

.assigned-empty {
  font-size: 0.75rem; color: var(--text-muted);
  font-style: italic; padding: 10px 0;
}

/* Assignment form */
.assignment-form { display: flex; flex-direction: column; gap: 8px; }
.assignment-select { font-size: 0.78rem; padding: 8px 12px; }
.assignment-btn {
  font-size: 0.75rem; padding: 8px 14px; align-self: flex-start;
}
.assignment-btn--analyst { background: var(--green-ok); border-color: var(--green-ok); }
.assignment-btn--analyst:hover { background: #059669; }

.assign-msg {
  font-size: 0.72rem; padding: 6px 10px; border-radius: var(--radius); border: 1px solid;
}
.assign-msg--ok    { color: var(--green-ok); border-color: rgba(16,185,129,0.3); background: rgba(16,185,129,0.1); }
.assign-msg--error { color: var(--red-alert); border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.1); }

.btn-spinner {
  width: 12px; height: 12px; border: 2px solid rgba(0,0,0,0.3);
  border-top-color: #fff; border-radius: 50%;
  animation: spin 0.7s linear infinite; flex-shrink: 0;
}

/* Workflow hint */
.workflow-hint {
  display: flex; align-items: center; gap: 8px;
  flex-wrap: wrap; padding-top: 16px; margin-top: 4px;
  border-top: 1px solid var(--border);
}
.workflow-step {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.68rem; color: var(--text-muted);
}
.workflow-step__num {
  width: 18px; height: 18px; border-radius: 50%;
  background: var(--amber); color: var(--bg-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.6rem; font-weight: 700; flex-shrink: 0;
}
.workflow-arrow { color: var(--border); font-size: 1rem; }

/* Evidence section */
.case-detail__section { margin-bottom: 32px; }
.case-detail__section-title {
  font-size: 1rem; margin-bottom: 20px;
  padding-bottom: 12px; border-bottom: 1px solid var(--border);
}
.case-detail__loading, .case-detail__empty {
  display: flex; flex-direction: column; align-items: center;
  gap: 16px; padding: 60px; color: var(--text-muted); font-size: 0.82rem;
}
.case-detail__spinner {
  width: 28px; height: 28px; border: 2px solid var(--border);
  border-top-color: var(--amber); border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.evidence-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px,1fr)); gap: 16px; }

/* Modals */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.75);
  backdrop-filter: blur(6px); z-index: 9999;
  display: flex; align-items: center; justify-content: center; padding: 24px;
}
.modal { width: 100%; max-width: 500px; }
.modal--wide { max-width: 640px; }
.modal__title { font-size: 1.1rem; margin-bottom: 4px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
.modal__subtitle { font-size: 0.75rem; color: var(--text-muted); margin: 12px 0 20px; line-height: 1.6; }
.modal__evidence-info {
  display: flex; align-items: center; gap: 12px;
  background: var(--bg-secondary); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 12px 16px; margin-bottom: 20px;
}
.modal__evidence-icon { font-size: 1.5rem; }
.modal__evidence-name { font-size: 0.82rem; color: var(--text-primary); font-weight: 500; }
.modal__evidence-hash { font-size: 0.65rem; color: var(--amber); display: block; margin-top: 2px; }
.modal__error   { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); color: var(--red-alert); padding: 10px 14px; border-radius: var(--radius); font-size: 0.78rem; margin-bottom: 16px; }
.modal__success { background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); color: var(--green-ok); padding: 12px 16px; border-radius: var(--radius); font-size: 0.82rem; margin-bottom: 16px; }
.modal__form { display: flex; flex-direction: column; gap: 16px; }
.modal__actions { display: flex; justify-content: flex-end; gap: 12px; padding-top: 16px; border-top: 1px solid var(--border); }
.modal__icon { width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; margin: 0 auto 20px; }
.modal__icon--ok   { background: rgba(16,185,129,0.2); color: var(--green-ok); border: 2px solid var(--green-ok); }
.modal__icon--fail { background: rgba(239,68,68,0.2); color: var(--red-alert); border: 2px solid var(--red-alert); }
.modal__message { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 20px; line-height: 1.6; }
.modal__data { background: var(--bg-secondary); border-radius: var(--radius); padding: 14px; margin-bottom: 20px; }
.modal__data-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 0.72rem; color: var(--text-muted); }
.modal__data-row:last-child { border-bottom: none; }
.modal__data-row code { color: var(--amber); font-size: 0.68rem; }
.modal__spinner { width: 13px; height: 13px; border: 2px solid rgba(0,0,0,0.3); border-top-color: var(--bg-primary); border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0; }

/* Custody timeline */
.custody-timeline { display: flex; flex-direction: column; max-height: 420px; overflow-y: auto; }
.custody-item { display: flex; gap: 16px; position: relative; padding-bottom: 20px; }
.custody-item__line { position: absolute; left: 7px; top: 18px; bottom: 0; width: 1px; background: var(--border); }
.custody-item__dot { width: 14px; height: 14px; border-radius: 50%; background: var(--amber); flex-shrink: 0; margin-top: 4px; z-index: 1; }
.custody-item__content { flex: 1; }
.custody-item__header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; flex-wrap: wrap; }
.custody-item__action { font-family: var(--font-display); font-size: 0.78rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-primary); }
.custody-item__role { font-size: 0.62rem; color: var(--amber); background: var(--amber-glow); padding: 1px 7px; border-radius: 10px; border: 1px solid var(--border-amber); }
.custody-item__time { font-size: 0.68rem; color: var(--text-muted); margin-left: auto; }
.custody-item__notes { font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 4px; }
.custody-item__ip { font-size: 0.65rem; color: var(--text-muted); margin-bottom: 2px; }
.custody-item__tx { font-size: 0.65rem; color: var(--amber); display: block; word-break: break-all; }

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .assignment-panel__grid { grid-template-columns: 1fr; }
  .assignment-divider { width: 100%; height: 1px; margin: 16px 0; }
}
</style>
