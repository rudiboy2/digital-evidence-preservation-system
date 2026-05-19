<template>
  <div class="upload-view container">

    <div class="upload-view__back">
      <RouterLink :to="{ name: 'case-detail', params: { id: caseId } }" class="back-link">
        ← Back to Case
      </RouterLink>
    </div>

    <div class="upload-view__header fade-up">
      <h1>Upload Evidence</h1>
      <p class="upload-view__case-id" v-if="caseInfo">
        Case: <code>{{ caseInfo.case_number }}</code> — {{ caseInfo.title }}
      </p>
    </div>

    <!-- Error banner -->
    <div v-if="uploadError" class="upload-view__error fade-up">
      <div>
        <strong>Upload Failed:</strong> {{ uploadError }}
      </div>
      <button class="upload-view__error-close" @click="uploadError = ''">✕</button>
    </div>

    <!-- Success banner -->
    <div v-if="lastUpload" class="upload-view__success fade-up">
      <div class="upload-view__success-icon">✓</div>
      <div>
        <strong>Evidence Registered Successfully</strong>
        <div class="upload-view__success-details">
          <span>SHA-256: <code>{{ lastUpload.sha256_hash }}</code></span>
          <span v-if="lastUpload.blockchain_tx_hash">
            TX: <code>{{ lastUpload.blockchain_tx_hash }}</code>
          </span>
          <span :class="['badge', `badge--${lastUpload.status}`]">{{ lastUpload.status }}</span>
        </div>
      </div>
    </div>

    <div class="upload-view__grid">

      <!-- Left: File + Description -->
      <div class="upload-view__left">
        <FileUploader
          :is-uploading="isUploading"
          :upload-status="uploadStatus"
          @upload="handleUpload"
        />
      </div>

      <!-- Right: Metadata + Steps -->
      <div class="upload-view__right">

        <!-- Upload Process Steps -->
        <div class="card upload-view__steps-card fade-up" style="animation-delay:0.1s">
          <h3 class="upload-view__steps-title">Upload Process</h3>
          <ol class="upload-view__steps">
            <li v-for="(step, i) in uploadSteps" :key="i"
              :class="{
                'step--done':   completedSteps > i,
                'step--active': completedSteps === i && isUploading
              }"
            >
              <span class="step__num">{{ completedSteps > i ? '✓' : i + 1 }}</span>
              <span class="step__text">{{ step }}</span>
            </li>
          </ol>
        </div>

        <!-- Officer Collection Metadata -->
        <div class="card upload-view__meta-card fade-up" style="animation-delay:0.15s">
          <div class="meta-card__header" @click="showMetadata = !showMetadata">
            <h3 class="meta-card__title">
              👮 Collection Metadata
              <span class="meta-card__badge">Tanzania Forensic Compliance</span>
            </h3>
            <span class="meta-card__toggle">{{ showMetadata ? '▲' : '▼' }}</span>
          </div>
          <p class="meta-card__sub">
            Required by TPF-SOP-DE-2021 and Tanzania Evidence Act for court admissibility.
          </p>

          <div v-if="showMetadata" class="meta-card__fields">

            <!-- Evidence Source -->
            <div class="form-group">
              <label class="form-label">Evidence Source Type *</label>
              <select v-model="meta.evidence_source_type" class="form-input">
                <option value="">— Select Source —</option>
                <option value="phone">📱 Mobile Phone</option>
                <option value="laptop">💻 Laptop / Computer</option>
                <option value="usb">🖥 USB Drive / Storage</option>
                <option value="cctv">📹 CCTV Recording</option>
                <option value="sd_card">💾 SD Card / Memory Card</option>
                <option value="cloud">☁ Cloud / Online Account</option>
                <option value="network">🌐 Network Traffic Capture</option>
                <option value="email">📧 Email Records</option>
                <option value="bank_records">🏦 Bank / Financial Records</option>
                <option value="digital_file">📄 Digital File (already digital)</option>
                <option value="other">Other</option>
              </select>
            </div>

            <!-- Device Info -->
            <div class="meta-card__section-title">📱 Device Information</div>
            <div class="meta-card__row">
              <div class="form-group">
                <label class="form-label">Device Type</label>
                <input v-model="meta.device_type" class="form-input" placeholder="e.g. Smartphone, Laptop, CCTV DVR" />
              </div>
              <div class="form-group">
                <label class="form-label">Device Make</label>
                <input v-model="meta.device_make" class="form-input" placeholder="e.g. Samsung, Apple, Hikvision" />
              </div>
            </div>
            <div class="meta-card__row">
              <div class="form-group">
                <label class="form-label">Device Model</label>
                <input v-model="meta.device_model" class="form-input" placeholder="e.g. Galaxy A53, iPhone 14" />
              </div>
              <div class="form-group">
                <label class="form-label">Serial Number</label>
                <input v-model="meta.device_serial_number" class="form-input" placeholder="Device serial number" />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">IMEI Number (phones only)</label>
              <input v-model="meta.device_imei" class="form-input" placeholder="15-digit IMEI number" maxlength="15" />
            </div>

            <!-- Collection Details -->
            <div class="meta-card__section-title">📍 Collection Details</div>
            <div class="form-group">
              <label class="form-label">Collection Method</label>
              <select v-model="meta.collection_method" class="form-input">
                <option value="">— Select Method —</option>
                <option value="physical_seizure">Physical Seizure at Scene</option>
                <option value="network_capture">Network Traffic Capture</option>
                <option value="cctv_extraction">CCTV/DVR Extraction</option>
                <option value="mobile_extraction">Mobile Device Extraction</option>
                <option value="cloud_download">Cloud/Online Account Download</option>
                <option value="voluntarily_submitted">Voluntarily Submitted</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Collection Location</label>
              <input v-model="meta.collection_location" class="form-input"
                placeholder="e.g. Kariakoo Market, Msimbazi Street, Dar es Salaam" />
            </div>
            <div class="meta-card__row">
              <div class="form-group">
                <label class="form-label">GPS Latitude</label>
                <input v-model="meta.collection_gps_lat" type="number" step="0.000001"
                  class="form-input" placeholder="-6.7924" @click="getGPS" />
              </div>
              <div class="form-group">
                <label class="form-label">GPS Longitude</label>
                <input v-model="meta.collection_gps_lng" type="number" step="0.000001"
                  class="form-input" placeholder="39.2083" />
              </div>
            </div>
            <button class="btn btn--ghost meta-card__gps-btn" @click="getGPS" :disabled="gettingGPS">
              <span v-if="gettingGPS" class="meta-spinner" />
              {{ gettingGPS ? 'Getting location…' : '📍 Auto-detect GPS Location' }}
            </button>

            <div class="form-group">
              <label class="form-label">Collection Date & Time</label>
              <input v-model="meta.collection_date" type="datetime-local" class="form-input" />
            </div>

            <!-- Witness & Seal -->
            <div class="meta-card__section-title">🔒 Witness & Chain of Custody Sealing</div>
            <div class="meta-card__row">
              <div class="form-group">
                <label class="form-label">Witness Full Name</label>
                <input v-model="meta.witness_name" class="form-input"
                  placeholder="Name of witness at collection" />
              </div>
              <div class="form-group">
                <label class="form-label">Witness Badge Number</label>
                <input v-model="meta.witness_badge_number" class="form-input"
                  placeholder="e.g. B-1042" />
              </div>
            </div>
            <div class="meta-card__row">
              <div class="form-group">
                <label class="form-label">Physical Seal Number</label>
                <input v-model="meta.physical_seal_number" class="form-input"
                  placeholder="Tamper-evident seal ID" />
              </div>
              <div class="form-group">
                <label class="form-label">Evidence Bag Number</label>
                <input v-model="meta.evidence_bag_number" class="form-input"
                  placeholder="Evidence bag tag ID" />
              </div>
            </div>
            <div class="meta-card__row">
              <div class="form-group">
                <label class="form-label">Exhibit Tag Number</label>
                <input v-model="meta.exhibit_tag_number" class="form-input"
                  placeholder="Court exhibit tag" />
              </div>
              <div class="form-group">
                <label class="form-label">Witness Statement Ref</label>
                <input v-model="meta.witness_statement_ref" class="form-input"
                  placeholder="Statement reference number" />
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import FileUploader from '../components/FileUploader.vue'

const route  = useRoute()
const caseId = route.params.id

const caseInfo       = ref(null)
const isUploading    = ref(false)
const uploadStatus   = ref('')
const completedSteps = ref(0)
const lastUpload     = ref(null)
const uploadError    = ref('')
const showMetadata   = ref(true)
const gettingGPS     = ref(false)

const uploadSteps = [
  'Validate file type & size',
  'Compute SHA-256 hash',
  'Store file securely',
  'Pin to IPFS (optional)',
  'Register on blockchain',
  'Record custody entry',
]

// Officer collection metadata
const meta = reactive({
  evidence_source_type: '',
  device_type: '',
  device_make: '',
  device_model: '',
  device_serial_number: '',
  device_imei: '',
  collection_method: '',
  collection_location: '',
  collection_gps_lat: '',
  collection_gps_lng: '',
  collection_date: '',
  witness_name: '',
  witness_badge_number: '',
  physical_seal_number: '',
  evidence_bag_number: '',
  exhibit_tag_number: '',
  witness_statement_ref: '',
})

onMounted(async () => {
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(`http://localhost:8000/api/v1/cases/${caseId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (resp.ok) caseInfo.value = await resp.json()
  } catch {}
  // Set collection date to now by default
  const now = new Date()
  meta.collection_date = now.toISOString().slice(0, 16)
})

async function getGPS() {
  if (!navigator.geolocation) {
    alert('Geolocation is not supported by your browser.')
    return
  }
  gettingGPS.value = true
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      meta.collection_gps_lat = pos.coords.latitude.toFixed(6)
      meta.collection_gps_lng = pos.coords.longitude.toFixed(6)
      gettingGPS.value = false
    },
    (err) => {
      alert(`Could not get location: ${err.message}`)
      gettingGPS.value = false
    },
    { timeout: 10000 }
  )
}

async function handleUpload({ file, description }) {
  isUploading.value    = true
  completedSteps.value = 0
  lastUpload.value     = null
  uploadError.value    = ''

  const statuses = [
    'Validating file…',
    'Computing SHA-256 hash…',
    'Storing file securely…',
    'Pinning to IPFS…',
    'Registering on blockchain…',
    'Recording custody log…',
  ]

  const interval = setInterval(() => {
    if (completedSteps.value < statuses.length - 1) {
      uploadStatus.value = statuses[completedSteps.value]
      completedSteps.value++
    }
  }, 700)

  try {
    const token = localStorage.getItem('access_token')
    const formData = new FormData()
    formData.append('file', file, file.name)

    // Build query params including all metadata
    const params = new URLSearchParams({
      case_id:                caseId,
      description:            description || '',
      evidence_source_type:   meta.evidence_source_type,
      device_type:            meta.device_type,
      device_make:            meta.device_make,
      device_model:           meta.device_model,
      device_serial_number:   meta.device_serial_number,
      device_imei:            meta.device_imei,
      collection_method:      meta.collection_method,
      collection_location:    meta.collection_location,
      collection_gps_lat:     meta.collection_gps_lat || '',
      collection_gps_lng:     meta.collection_gps_lng || '',
      collection_date:        meta.collection_date,
      witness_name:           meta.witness_name,
      witness_badge_number:   meta.witness_badge_number,
      physical_seal_number:   meta.physical_seal_number,
      evidence_bag_number:    meta.evidence_bag_number,
      exhibit_tag_number:     meta.exhibit_tag_number,
      witness_statement_ref:  meta.witness_statement_ref,
    })

    const response = await fetch(
      `http://localhost:8000/api/v1/evidence/upload?${params}`,
      {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      }
    )

    clearInterval(interval)

    if (!response.ok) {
      let errorMsg = `Upload failed (HTTP ${response.status})`
      try {
        const errData = await response.json()
        if (typeof errData.detail === 'string') errorMsg = errData.detail
        else if (Array.isArray(errData.detail))
          errorMsg = errData.detail.map(e => e.msg || JSON.stringify(e)).join(', ')
      } catch {}
      throw new Error(errorMsg)
    }

    const data = await response.json()
    completedSteps.value = uploadSteps.length
    uploadStatus.value   = 'Complete!'
    lastUpload.value     = data

    // Reset metadata
    Object.keys(meta).forEach(k => {
      if (k !== 'collection_date') meta[k] = ''
    })

  } catch (err) {
    clearInterval(interval)
    uploadError.value = (err && err.message) ? err.message : String(err)
  } finally {
    isUploading.value = false
  }
}
</script>

<style scoped>
.upload-view { padding: 32px 24px; }
.upload-view__back { margin-bottom: 20px; }
.back-link { font-size: 0.78rem; color: var(--text-muted); }
.back-link:hover { color: var(--amber); text-decoration: none; }
.upload-view__header { margin-bottom: 20px; }
.upload-view__case-id { font-size: 0.78rem; color: var(--text-muted); margin-top: 6px; }
.upload-view__case-id code { color: var(--amber); }

/* Error */
.upload-view__error {
  display: flex; justify-content: space-between; align-items: flex-start;
  background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.4);
  color: var(--red-alert); padding: 14px 16px; border-radius: var(--radius-lg);
  font-size: 0.82rem; line-height: 1.6; margin-bottom: 16px; gap: 12px;
}
.upload-view__error-close {
  background: none; border: none; color: var(--red-alert);
  cursor: pointer; font-size: 1rem; padding: 0 4px; flex-shrink: 0;
}

/* Success */
.upload-view__success {
  display: flex; align-items: flex-start; gap: 16px;
  background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.3);
  padding: 16px 20px; border-radius: var(--radius-lg); margin-bottom: 20px;
}
.upload-view__success-icon {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--green-ok); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; font-weight: 700; flex-shrink: 0;
}
.upload-view__success strong { font-size: 0.88rem; color: var(--green-ok); display: block; margin-bottom: 6px; }
.upload-view__success-details {
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
  font-size: 0.72rem; color: var(--text-muted);
}
.upload-view__success-details code { color: var(--amber); font-size: 0.65rem; }

/* Grid */
.upload-view__grid {
  display: grid; grid-template-columns: 1fr 480px; gap: 24px; align-items: start;
}
.upload-view__left { display: flex; flex-direction: column; gap: 16px; }
.upload-view__right { display: flex; flex-direction: column; gap: 16px; }

/* Steps card */
.upload-view__steps-card { padding: 20px; }
.upload-view__steps-title { font-size: 0.85rem; margin-bottom: 16px; }
.upload-view__steps { list-style: none; display: flex; flex-direction: column; gap: 10px; }
.upload-view__steps li {
  display: flex; align-items: center; gap: 12px;
  font-size: 0.78rem; color: var(--text-muted); transition: color 0.3s;
}
.step--done   { color: var(--green-ok) !important; }
.step--active { color: var(--amber) !important; }
.step__num {
  width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--border); border-radius: 50%; font-size: 0.65rem; flex-shrink: 0; transition: all 0.3s;
}
.step--done .step__num   { background: var(--green-ok); border-color: var(--green-ok); color: #fff; }
.step--active .step__num { border-color: var(--amber); color: var(--amber); }

/* Metadata card */
.upload-view__meta-card { padding: 0; overflow: hidden; }
.meta-card__header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; cursor: pointer; border-bottom: 1px solid var(--border);
  transition: background 0.2s;
}
.meta-card__header:hover { background: var(--bg-elevated); }
.meta-card__title {
  font-size: 0.88rem; display: flex; align-items: center; gap: 10px;
  font-family: var(--font-display); letter-spacing: 0.04em; text-transform: uppercase;
}
.meta-card__badge {
  font-size: 0.6rem; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--amber); background: var(--amber-glow); border: 1px solid var(--border-amber);
  padding: 2px 8px; border-radius: 10px;
}
.meta-card__toggle { color: var(--text-muted); font-size: 0.7rem; }
.meta-card__sub {
  font-size: 0.72rem; color: var(--text-muted); line-height: 1.5;
  padding: 10px 20px 0; font-style: italic;
}
.meta-card__fields {
  padding: 16px 20px 20px; display: flex; flex-direction: column; gap: 14px;
}
.meta-card__section-title {
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--amber); padding-top: 8px; border-top: 1px solid var(--border); margin-top: 4px;
}
.meta-card__row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.meta-card__gps-btn { font-size: 0.72rem; padding: 7px 12px; align-self: flex-start; }
.meta-spinner {
  width: 12px; height: 12px; border: 2px solid rgba(255,255,255,0.3);
  border-top-color: var(--amber); border-radius: 50%;
  animation: spin 0.7s linear infinite; flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 900px) {
  .upload-view__grid { grid-template-columns: 1fr; }
  .meta-card__row    { grid-template-columns: 1fr; }
}
</style>
