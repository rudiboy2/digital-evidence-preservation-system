<template>
  <div class="custody-view container">

    <!-- Back -->
    <div class="custody-view__back">
      <RouterLink :to="{ name: 'case-detail', params: { id: caseId } }" class="back-link">
        ← Back to Case
      </RouterLink>
    </div>

    <!-- Header -->
    <div class="custody-view__header fade-up">
      <div>
        <div class="custody-view__case-num" v-if="caseData">
          {{ caseData.case_number }} — {{ caseData.title }}
        </div>
        <h1>Chain of Custody</h1>
        <p class="custody-view__sub">
          Complete tamper-proof audit trail of every action performed on evidence.
          All entries are recorded on the blockchain and cannot be altered.
        </p>
      </div>
      <div class="custody-view__stats">
        <div class="cstat">
          <span class="cstat__val">{{ totalEvents }}</span>
          <span class="cstat__label">Total Events</span>
        </div>
        <div class="cstat">
          <span class="cstat__val">{{ evidence.length }}</span>
          <span class="cstat__label">Evidence Items</span>
        </div>
        <div class="cstat">
          <span class="cstat__val">{{ onChainCount }}</span>
          <span class="cstat__label">On Blockchain</span>
        </div>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="custody-view__filters card fade-up" style="animation-delay:0.1s">
      <div class="filter-group">
        <label class="form-label">Filter by Action</label>
        <div class="filter-chips">
          <button
            v-for="action in actionFilters"
            :key="action.value"
            :class="['chip', selectedAction === action.value ? 'chip--active' : '']"
            @click="selectedAction = action.value"
          >
            <span class="chip__icon">{{ action.icon }}</span>
            {{ action.label }}
          </button>
        </div>
      </div>
      <div class="filter-group">
        <label class="form-label">Filter by Evidence</label>
        <select v-model="selectedEvidence" class="form-input filter-select">
          <option value="">All Evidence Items</option>
          <option v-for="ev in evidence" :key="ev.id" :value="ev.id">
            {{ ev.file_name }}
          </option>
        </select>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="custody-view__loading">
      <div class="custody-view__spinner" />
      <p>Loading custody records…</p>
    </div>

    <!-- Empty -->
    <div v-else-if="filteredTimeline.length === 0" class="custody-view__empty card">
      <span style="font-size:2.5rem">⛓</span>
      <p>No custody events found.</p>
      <p style="font-size:0.72rem; color:var(--text-muted)">
        Events are recorded automatically when evidence is uploaded, verified, or transferred.
      </p>
    </div>

    <!-- Timeline -->
    <div v-else class="custody-timeline fade-up" style="animation-delay:0.2s">

      <!-- Group by evidence item -->
      <div
        v-for="group in groupedTimeline"
        :key="group.evidenceId"
        class="evidence-group"
      >
        <!-- Evidence header -->
        <div class="evidence-group__header">
          <div class="evidence-group__icon">{{ fileIcon(group.mimeType) }}</div>
          <div class="evidence-group__info">
            <span class="evidence-group__name">{{ group.fileName }}</span>
            <code class="evidence-group__hash">SHA-256: {{ group.hash?.slice(0, 20) }}…{{ group.hash?.slice(-8) }}</code>
          </div>
          <span class="evidence-group__count">{{ group.events.length }} events</span>
        </div>

        <!-- Events timeline -->
        <div class="events-list">
          <div
            v-for="(event, index) in group.events"
            :key="event.id"
            class="event-item"
            :class="`event-item--${event.action}`"
          >
            <!-- Connector line -->
            <div class="event-item__connector">
              <div class="event-item__line" v-if="index < group.events.length - 1" />
              <div :class="['event-item__dot', `event-item__dot--${event.action}`]">
                <span class="event-item__dot-icon">{{ actionIcon(event.action) }}</span>
              </div>
            </div>

            <!-- Content -->
            <div class="event-item__content">
              <div class="event-item__top">
                <div class="event-item__left">
                  <span :class="['event-badge', `event-badge--${event.action}`]">
                    {{ event.action.toUpperCase() }}
                  </span>
                  <span class="event-item__time">{{ formatDate(event.timestamp) }}</span>
                </div>
                <div class="event-item__chain" v-if="event.blockchain_tx_hash">
                  <span class="event-item__chain-icon">⬡</span>
                  <span class="event-item__chain-label">On-chain</span>
                </div>
                <div class="event-item__chain event-item__chain--pending" v-else>
                  <span class="event-item__chain-label">Pending chain</span>
                </div>
              </div>

              <!-- Officer info -->
              <div class="event-item__officer" v-if="event.performed_by">
                <span class="event-item__officer-label">Officer:</span>
                <code class="event-item__officer-id">{{ event.performed_by }}</code>
              </div>

              <!-- Transfer info -->
              <div class="event-item__transfer" v-if="event.action === 'transferred'">
                <div class="transfer-row">
                  <div class="transfer-from">
                    <span class="transfer-label">FROM</span>
                    <code>{{ event.from_officer || 'Unknown' }}</code>
                  </div>
                  <span class="transfer-arrow">→</span>
                  <div class="transfer-to">
                    <span class="transfer-label">TO</span>
                    <code>{{ event.to_officer || 'Unknown' }}</code>
                  </div>
                </div>
              </div>

              <!-- Notes -->
              <div class="event-item__notes" v-if="event.notes">
                <span class="event-item__notes-icon">📝</span>
                {{ event.notes }}
              </div>

              <!-- Location -->
              <div class="event-item__location" v-if="event.location">
                <span>📍</span> {{ event.location }}
              </div>

              <!-- Blockchain TX -->
              <div class="event-item__tx" v-if="event.blockchain_tx_hash">
                <span class="event-item__tx-label">TX Hash:</span>
                <code class="event-item__tx-hash">{{ event.blockchain_tx_hash }}</code>
                <button class="event-item__copy" @click="copyTx(event.blockchain_tx_hash)" title="Copy TX hash">
                  ⎘
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/apiService'

const route  = useRoute()
const caseId = route.params.id

const caseData       = ref(null)
const evidence       = ref([])
const allCustodyData = ref({}) // evidenceId -> custody chain array
const isLoading      = ref(true)
const selectedAction   = ref('')
const selectedEvidence = ref('')

// ── Action filter options ──────────────────────────────────────────────────
const actionFilters = [
  { value: '',           label: 'All',       icon: '⬡' },
  { value: 'uploaded',   label: 'Uploaded',  icon: '⬆' },
  { value: 'verified',   label: 'Verified',  icon: '✓' },
  { value: 'transferred',label: 'Transferred',icon: '↔' },
  { value: 'accessed',   label: 'Accessed',  icon: '👁' },
  { value: 'exported',   label: 'Exported',  icon: '⬇' },
]

// ── Computed ───────────────────────────────────────────────────────────────
const flatTimeline = computed(() => {
  const events = []
  for (const ev of evidence.value) {
    const chain = allCustodyData.value[ev.id] || []
    for (const entry of chain) {
      events.push({
        ...entry,
        evidenceId: ev.id,
        fileName:   ev.file_name,
        mimeType:   ev.mime_type,
        hash:       ev.sha256_hash,
      })
    }
  }
  return events.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
})

const filteredTimeline = computed(() => {
  return flatTimeline.value.filter(e => {
    const actionMatch   = !selectedAction.value   || e.action === selectedAction.value
    const evidenceMatch = !selectedEvidence.value || e.evidenceId === selectedEvidence.value
    return actionMatch && evidenceMatch
  })
})

const groupedTimeline = computed(() => {
  const groups = {}
  for (const event of filteredTimeline.value) {
    if (!groups[event.evidenceId]) {
      groups[event.evidenceId] = {
        evidenceId: event.evidenceId,
        fileName:   event.fileName,
        mimeType:   event.mimeType,
        hash:       event.hash,
        events:     [],
      }
    }
    groups[event.evidenceId].events.push(event)
  }
  // Sort events within each group oldest first
  for (const g of Object.values(groups)) {
    g.events.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
  }
  return Object.values(groups)
})

const totalEvents  = computed(() => flatTimeline.value.length)
const onChainCount = computed(() => flatTimeline.value.filter(e => e.blockchain_tx_hash).length)

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    caseData.value = await api.get(`/cases/${caseId}`)
  } catch {}

  try {
    const data = await api.get(`/evidence/case/${caseId}?page_size=100`)
    evidence.value = data.items || []

    // Fetch custody chain for each evidence item in parallel
    await Promise.all(
      evidence.value.map(async (ev) => {
        try {
          const chain = await api.get(`/evidence/${ev.id}/custody-chain`)
          allCustodyData.value[ev.id] = chain.custody_chain || []
        } catch {
          allCustodyData.value[ev.id] = []
        }
      })
    )
  } catch {}

  isLoading.value = false
})

// ── Helpers ────────────────────────────────────────────────────────────────
function actionIcon(action) {
  const icons = {
    uploaded:    '⬆',
    verified:    '✓',
    transferred: '↔',
    accessed:    '👁',
    exported:    '⬇',
    collected:   '📦',
    returned:    '↩',
  }
  return icons[action] || '⬡'
}

function fileIcon(mime = '') {
  if (mime.startsWith('image/'))       return '🖼'
  if (mime.startsWith('video/'))       return '🎥'
  if (mime.startsWith('audio/'))       return '🎙'
  if (mime.includes('pdf'))            return '📄'
  if (mime.startsWith('text/'))        return '📝'
  return '💾'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

async function copyTx(hash) {
  try {
    await navigator.clipboard.writeText(hash)
    alert('TX hash copied to clipboard')
  } catch {}
}
</script>

<style scoped>
.custody-view { padding: 32px 24px; }

.custody-view__back { margin-bottom: 20px; }
.back-link { font-size: 0.78rem; color: var(--text-muted); letter-spacing: 0.06em; }
.back-link:hover { color: var(--amber); text-decoration: none; }

/* Header */
.custody-view__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 32px;
  margin-bottom: 28px;
}

.custody-view__case-num {
  font-size: 0.72rem;
  color: var(--amber);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.custody-view__sub {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 8px;
  max-width: 560px;
  line-height: 1.6;
}

/* Stats */
.custody-view__stats {
  display: flex;
  gap: 24px;
  flex-shrink: 0;
}

.cstat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px 24px;
  min-width: 90px;
}

.cstat__val {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 700;
  color: var(--amber);
  line-height: 1;
}

.cstat__label {
  font-size: 0.62rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  text-align: center;
}

/* Filters */
.custody-view__filters {
  display: flex;
  gap: 32px;
  align-items: flex-end;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: transparent;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.04em;
}

.chip:hover { border-color: var(--amber); color: var(--amber); }

.chip--active {
  background: var(--amber-glow);
  border-color: var(--amber);
  color: var(--amber);
}

.chip__icon { font-size: 0.8rem; }

.filter-select {
  width: 240px;
  padding: 7px 12px;
  font-size: 0.78rem;
}

/* Loading / empty */
.custody-view__loading,
.custody-view__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 60px;
  color: var(--text-muted);
  font-size: 0.82rem;
  text-align: center;
}

.custody-view__spinner {
  width: 32px; height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--amber);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Evidence group */
.evidence-group {
  margin-bottom: 40px;
}

.evidence-group__header {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-amber);
  border-radius: var(--radius-lg);
  padding: 14px 20px;
  margin-bottom: 0;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.evidence-group__icon { font-size: 1.6rem; flex-shrink: 0; }

.evidence-group__info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.evidence-group__name {
  font-size: 0.88rem;
  color: var(--text-primary);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.evidence-group__hash {
  font-size: 0.65rem;
  color: var(--amber);
}

.evidence-group__count {
  font-size: 0.68rem;
  color: var(--text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  flex-shrink: 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  padding: 3px 10px;
  border-radius: 12px;
}

/* Events list */
.events-list {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-top: none;
  border-bottom-left-radius: var(--radius-lg);
  border-bottom-right-radius: var(--radius-lg);
  padding: 8px 20px 20px 20px;
}

.event-item {
  display: flex;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid var(--border);
}

.event-item:last-child { border-bottom: none; }

/* Connector */
.event-item__connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  position: relative;
  width: 36px;
}

.event-item__line {
  position: absolute;
  top: 36px;
  bottom: -16px;
  width: 2px;
  background: var(--border);
  left: 50%;
  transform: translateX(-50%);
}

.event-item__dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
  border: 2px solid;
  z-index: 1;
  background: var(--bg-primary);
}

.event-item__dot--uploaded    { border-color: var(--amber);      color: var(--amber); }
.event-item__dot--verified    { border-color: var(--green-ok);   color: var(--green-ok); }
.event-item__dot--transferred { border-color: var(--blue-info);  color: var(--blue-info); }
.event-item__dot--accessed    { border-color: var(--text-muted); color: var(--text-muted); }
.event-item__dot--exported    { border-color: #a78bfa;           color: #a78bfa; }
.event-item__dot--collected   { border-color: var(--amber);      color: var(--amber); }

/* Content */
.event-item__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.event-item__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.event-item__left {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Action badges */
.event-badge {
  font-family: var(--font-display);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  padding: 3px 10px;
  border-radius: 2px;
  border: 1px solid;
}

.event-badge--uploaded    { background: rgba(245,158,11,0.1);   color: var(--amber);      border-color: rgba(245,158,11,0.3); }
.event-badge--verified    { background: rgba(16,185,129,0.1);   color: var(--green-ok);   border-color: rgba(16,185,129,0.3); }
.event-badge--transferred { background: rgba(59,130,246,0.1);   color: var(--blue-info);  border-color: rgba(59,130,246,0.3); }
.event-badge--accessed    { background: rgba(100,116,139,0.1);  color: #94a3b8;           border-color: rgba(100,116,139,0.3); }
.event-badge--exported    { background: rgba(167,139,250,0.1);  color: #a78bfa;           border-color: rgba(167,139,250,0.3); }
.event-badge--collected   { background: rgba(245,158,11,0.1);   color: var(--amber);      border-color: rgba(245,158,11,0.3); }

.event-item__time {
  font-size: 0.72rem;
  color: var(--text-muted);
}

/* Chain status */
.event-item__chain {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.65rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--green-ok);
}

.event-item__chain--pending { color: var(--text-muted); }
.event-item__chain-icon { color: var(--amber); }
.event-item__chain-label {}

/* Officer */
.event-item__officer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.72rem;
}

.event-item__officer-label {
  color: var(--text-muted);
  flex-shrink: 0;
}

.event-item__officer-id {
  color: var(--text-secondary);
  font-size: 0.68rem;
  word-break: break-all;
}

/* Transfer */
.event-item__transfer {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 14px;
}

.transfer-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.transfer-from, .transfer-to {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.transfer-label {
  font-size: 0.58rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.transfer-from code { color: var(--red-alert); font-size: 0.7rem; }
.transfer-to   code { color: var(--green-ok);  font-size: 0.7rem; }

.transfer-arrow {
  font-size: 1.2rem;
  color: var(--blue-info);
  flex-shrink: 0;
}

/* Notes */
.event-item__notes {
  font-size: 0.75rem;
  color: var(--text-secondary);
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-style: italic;
}

.event-item__notes-icon { flex-shrink: 0; }

/* Location */
.event-item__location {
  font-size: 0.72rem;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}

/* TX */
.event-item__tx {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px 12px;
  flex-wrap: wrap;
}

.event-item__tx-label {
  font-size: 0.62rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  flex-shrink: 0;
}

.event-item__tx-hash {
  flex: 1;
  font-size: 0.68rem;
  color: var(--amber);
  word-break: break-all;
}

.event-item__copy {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 2px 4px;
  transition: color 0.2s;
  flex-shrink: 0;
}
.event-item__copy:hover { color: var(--amber); }

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .custody-view__header { flex-direction: column; }
  .custody-view__stats  { width: 100%; justify-content: space-between; }
  .custody-view__filters { flex-direction: column; }
  .filter-select { width: 100%; }
}
</style>
