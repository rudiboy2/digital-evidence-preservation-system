<template>
  <div class="ev-card" :class="`ev-card--${evidence.status}`">
    <!-- Status stripe -->
    <div class="ev-card__stripe" />

    <!-- Header -->
    <div class="ev-card__header">
      <span class="ev-card__type-icon">{{ typeIcon }}</span>
      <div class="ev-card__title-block">
        <h3 class="ev-card__filename" :title="evidence.file_name">{{ evidence.file_name }}</h3>
        <div class="ev-card__meta-row">
          <span class="ev-card__size">{{ formattedSize }}</span>
          <span class="ev-card__dot-sep">·</span>
          <span class="ev-card__type">{{ evidence.evidence_type }}</span>
          <span class="ev-card__dot-sep">·</span>
          <span class="ev-card__mime">{{ evidence.mime_type }}</span>
        </div>
      </div>
      <span :class="['badge', `badge--${evidence.status}`]">{{ evidence.status }}</span>
    </div>

    <!-- Description -->
    <p v-if="evidence.description" class="ev-card__description">
      {{ evidence.description }}
    </p>

    <!-- Custodian -->
    <div class="ev-card__custodian">
      <span class="ev-card__custodian-icon">👮</span>
      <span class="ev-card__custodian-label">Custodian:</span>
      <span class="ev-card__custodian-val">{{ custodianName }}</span>
    </div>

    <!-- Hash -->
    <div class="ev-card__hash">
      <span class="ev-card__hash-label">SHA-256</span>
      <code class="ev-card__hash-value" :title="evidence.sha256_hash">{{ truncatedHash }}</code>
      <button class="ev-card__copy" @click="copyHash" :title="hashCopied ? 'Copied!' : 'Copy full hash'">
        {{ hashCopied ? '✓' : '⎘' }}
      </button>
    </div>

    <!-- Blockchain -->
    <div class="ev-card__chain">
      <span class="ev-card__chain-icon">⬡</span>
      <span v-if="evidence.blockchain_tx_hash" class="ev-card__chain-tx">
        TX: <code>{{ truncatedTx }}</code>
        <span class="ev-card__chain-confirmed">● On-chain</span>
      </span>
      <span v-else class="ev-card__chain-pending">Awaiting blockchain confirmation…</span>
    </div>

    <!-- IPFS -->
    <div v-if="evidence.ipfs_cid" class="ev-card__ipfs">
      <span class="ev-card__ipfs-label">IPFS</span>
      <a :href="`https://ipfs.io/ipfs/${evidence.ipfs_cid}`" target="_blank" class="ev-card__ipfs-link">
        {{ evidence.ipfs_cid.slice(0, 20) }}…
      </a>
    </div>

    <!-- ── Download Section (prominent — analyst primary action) ── -->
    <div class="ev-card__download-section">
      <div class="ev-card__download-info">
        <span class="ev-card__download-label">⬇ Download for offline forensic analysis</span>
        <span class="ev-card__download-note">
          Download is logged in the chain of custody audit trail
        </span>
      </div>
      <button
        class="btn ev-card__download-btn"
        :class="downloading ? 'ev-card__download-btn--loading' : ''"
        :disabled="downloading"
        @click="downloadEvidence"
      >
        <span v-if="downloading" class="ev-card__dl-spinner" />
        <span v-else>⬇</span>
        {{ downloading ? 'Downloading…' : `Download (${formattedSize})` }}
      </button>
    </div>

    <!-- Footer actions -->
    <div class="ev-card__footer">
      <span class="ev-card__date">Uploaded: {{ formattedDate }}</span>
      <div class="ev-card__actions">
        <!-- Verify — all roles -->
        <button class="btn btn--ghost ev-card__btn" @click="$emit('verify', evidence.id)" title="Verify file integrity against blockchain">
          ✓ Verify
        </button>
        <!-- Custody Chain — all roles -->
        <button class="btn btn--ghost ev-card__btn" @click="$emit('custody', evidence.id)" title="View chain of custody">
          ⛓ Custody
        </button>
        <!-- Transfer — investigator, officer, admin only -->
        <button
          v-if="canTransfer"
          class="btn btn--ghost ev-card__btn ev-card__btn--transfer"
          @click="$emit('transfer', evidence.id)"
          title="Transfer custody to another officer or analyst"
        >
          ↔ Transfer
        </button>
      </div>
    </div>

    <!-- Download success message -->
    <div v-if="downloadMsg" class="ev-card__dl-msg" :class="`ev-card__dl-msg--${downloadMsg.type}`">
      {{ downloadMsg.text }}
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  evidence: { type: Object, required: true },
})

const emit = defineEmits(['verify', 'custody', 'transfer'])

const hashCopied  = ref(false)
const downloading = ref(false)
const downloadMsg = ref(null)

// Role permissions
const userRole    = computed(() => localStorage.getItem('user_role') || '')
const canTransfer = computed(() =>
  ['admin', 'investigator', 'officer'].includes(userRole.value)
)

// Evidence type icons
const TYPE_ICONS = {
  image: '🖼', video: '🎥', audio: '🎙',
  document: '📄', binary: '💾', other: '📁',
}
const typeIcon = computed(() => TYPE_ICONS[props.evidence.evidence_type] || '📁')

// Custodian display
const custodianName = computed(() =>
  props.evidence.uploader?.full_name || 'Unknown Officer'
)

// Formatted size
const formattedSize = computed(() => {
  const b = props.evidence.file_size || 0
  if (b < 1024)           return `${b} B`
  if (b < 1024 * 1024)    return `${(b / 1024).toFixed(1)} KB`
  if (b < 1024 ** 3)      return `${(b / (1024 * 1024)).toFixed(2)} MB`
  return `${(b / 1024 ** 3).toFixed(2)} GB`
})

// Truncated hash
const truncatedHash = computed(() => {
  const h = props.evidence.sha256_hash || ''
  return h.length > 28 ? `${h.slice(0, 14)}…${h.slice(-10)}` : h
})

// Truncated TX
const truncatedTx = computed(() => {
  const tx = props.evidence.blockchain_tx_hash || ''
  return tx.length > 22 ? `${tx.slice(0, 10)}…${tx.slice(-8)}` : tx
})

// Formatted date
const formattedDate = computed(() => {
  if (!props.evidence.created_at) return ''
  return new Date(props.evidence.created_at).toLocaleString('en-GB', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
})

// ── Copy hash ──────────────────────────────────────────────────────────────
async function copyHash() {
  try {
    await navigator.clipboard.writeText(props.evidence.sha256_hash)
    hashCopied.value = true
    setTimeout(() => { hashCopied.value = false }, 2000)
  } catch {}
}

// ── Download evidence ──────────────────────────────────────────────────────
async function downloadEvidence() {
  if (downloading.value) return
  downloading.value = true
  downloadMsg.value = null

  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch(
      `http://localhost:8000/api/v1/evidence/${props.evidence.id}/download`,
      {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` },
      }
    )

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || `Download failed: HTTP ${response.status}`)
    }

    // Get filename from Content-Disposition header or use stored name
    const disposition = response.headers.get('Content-Disposition')
    let filename = props.evidence.file_name
    if (disposition) {
      const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match) filename = match[1].replace(/['"]/g, '')
    }

    // Create blob and trigger download
    const blob = await response.blob()
    const url  = window.URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    downloadMsg.value = {
      type: 'ok',
      text: `✓ "${filename}" downloaded successfully. This action has been logged in the audit trail.`,
    }
    setTimeout(() => { downloadMsg.value = null }, 5000)

  } catch (err) {
    downloadMsg.value = {
      type: 'error',
      text: `Download failed: ${err.message}`,
    }
    setTimeout(() => { downloadMsg.value = null }, 5000)
  } finally {
    downloading.value = false
  }
}
</script>

<style scoped>
.ev-card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 20px 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.ev-card:hover {
  border-color: rgba(255,255,255,0.12);
  box-shadow: var(--shadow-card);
}

/* Status stripe */
.ev-card__stripe {
  position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
}
.ev-card--verified .ev-card__stripe { background: var(--green-ok); }
.ev-card--pending  .ev-card__stripe { background: var(--amber); }
.ev-card--tampered .ev-card__stripe { background: var(--red-alert); }

/* Header */
.ev-card__header { display: flex; align-items: flex-start; gap: 12px; }
.ev-card__type-icon { font-size: 1.6rem; flex-shrink: 0; }
.ev-card__title-block { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.ev-card__filename {
  font-family: var(--font-mono); font-size: 0.85rem; font-weight: 500;
  text-transform: none; letter-spacing: 0; color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ev-card__meta-row {
  display: flex; align-items: center; gap: 6px;
  flex-wrap: wrap;
}
.ev-card__size  { font-size: 0.68rem; color: var(--amber); font-weight: 600; }
.ev-card__type  { font-size: 0.68rem; color: var(--text-muted); text-transform: capitalize; }
.ev-card__mime  { font-size: 0.65rem; color: var(--text-muted); }
.ev-card__dot-sep { color: var(--border); font-size: 0.6rem; }

/* Description */
.ev-card__description { font-size: 0.78rem; color: var(--text-secondary); line-height: 1.5; }

/* Custodian */
.ev-card__custodian {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.72rem; padding: 6px 10px;
  background: var(--bg-secondary); border: 1px solid var(--border);
  border-radius: var(--radius);
}
.ev-card__custodian-icon { font-size: 0.9rem; }
.ev-card__custodian-label { color: var(--text-muted); flex-shrink: 0; }
.ev-card__custodian-val { color: var(--amber); font-weight: 500; }

/* Hash */
.ev-card__hash {
  display: flex; align-items: center; gap: 8px;
  background: var(--bg-secondary); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 7px 12px;
}
.ev-card__hash-label {
  font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted); flex-shrink: 0;
}
.ev-card__hash-value {
  flex: 1; font-size: 0.75rem; color: var(--amber);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ev-card__copy {
  background: none; border: none; color: var(--text-muted);
  cursor: pointer; font-size: 0.9rem; padding: 2px 4px;
  transition: color 0.2s; flex-shrink: 0;
}
.ev-card__copy:hover { color: var(--amber); }

/* Chain */
.ev-card__chain { display: flex; align-items: center; gap: 8px; font-size: 0.75rem; }
.ev-card__chain-icon { color: var(--amber); }
.ev-card__chain-tx { display: flex; align-items: center; gap: 6px; }
.ev-card__chain-tx code { color: var(--text-secondary); font-size: 0.72rem; }
.ev-card__chain-confirmed { font-size: 0.65rem; color: var(--green-ok); letter-spacing: 0.06em; }
.ev-card__chain-pending { color: var(--text-muted); font-style: italic; }

/* IPFS */
.ev-card__ipfs { display: flex; align-items: center; gap: 8px; font-size: 0.72rem; }
.ev-card__ipfs-label {
  font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-muted);
}
.ev-card__ipfs-link { color: var(--blue-info); }

/* ── Download Section ─────────────────────────────────────────────────── */
.ev-card__download-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: var(--radius);
  padding: 12px 16px;
}

.ev-card__download-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ev-card__download-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--green-ok);
  letter-spacing: 0.03em;
}

.ev-card__download-note {
  font-size: 0.62rem;
  color: var(--text-muted);
  font-style: italic;
}

.ev-card__download-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 18px;
  background: var(--green-ok);
  color: #fff;
  border: 1px solid var(--green-ok);
  border-radius: var(--radius);
  font-family: var(--font-display);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.ev-card__download-btn:hover:not(:disabled) {
  background: #059669;
  box-shadow: 0 0 16px rgba(16, 185, 129, 0.35);
}

.ev-card__download-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.ev-card__download-btn--loading {
  background: #059669;
}

.ev-card__dl-spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

/* Download message */
.ev-card__dl-msg {
  font-size: 0.72rem;
  padding: 8px 12px;
  border-radius: var(--radius);
  border: 1px solid;
  line-height: 1.5;
}
.ev-card__dl-msg--ok {
  color: var(--green-ok);
  border-color: rgba(16,185,129,0.3);
  background: rgba(16,185,129,0.08);
}
.ev-card__dl-msg--error {
  color: var(--red-alert);
  border-color: rgba(239,68,68,0.3);
  background: rgba(239,68,68,0.08);
}

/* Footer */
.ev-card__footer {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 4px; padding-top: 12px; border-top: 1px solid var(--border);
}
.ev-card__date { font-size: 0.68rem; color: var(--text-muted); }
.ev-card__actions { display: flex; gap: 6px; flex-wrap: wrap; }
.ev-card__btn { padding: 5px 10px; font-size: 0.68rem; }
.ev-card__btn--transfer {
  color: var(--blue-info); border-color: rgba(59,130,246,0.3);
}
.ev-card__btn--transfer:hover {
  background: rgba(59,130,246,0.1); border-color: var(--blue-info);
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
