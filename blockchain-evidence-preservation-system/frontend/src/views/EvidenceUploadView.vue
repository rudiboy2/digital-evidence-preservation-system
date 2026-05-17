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

    <div class="upload-view__grid">
      <!-- Uploader -->
      <div class="fade-up" style="animation-delay:0.1s">
        <FileUploader
          :is-uploading="isUploading"
          :upload-status="uploadStatus"
          @upload="handleUpload"
        />
      </div>

      <!-- Error display -->
      <div v-if="uploadError" class="upload-view__error fade-up">
        <strong>Upload Failed:</strong> {{ uploadError }}
        <button class="upload-view__error-close" @click="uploadError = ''">✕</button>
      </div>

      <!-- Info Panel -->
      <div class="upload-view__info fade-up" style="animation-delay:0.2s">
        <div class="card">
          <h3 class="upload-view__info-title">Upload Process</h3>
          <ol class="upload-view__steps">
            <li v-for="(step, i) in uploadSteps" :key="i" :class="{ 'step--done': completedSteps > i, 'step--active': completedSteps === i && isUploading }">
              <span class="step__num">{{ completedSteps > i ? '✓' : i + 1 }}</span>
              <span class="step__text">{{ step }}</span>
            </li>
          </ol>
        </div>

        <!-- Success block -->
        <div v-if="lastUpload" class="card upload-view__success">
          <h3 class="upload-view__success-title">⬡ Evidence Registered</h3>
          <div class="upload-view__result-row">
            <span class="upload-view__result-label">SHA-256</span>
            <code class="upload-view__result-val">{{ lastUpload.sha256_hash }}</code>
          </div>
          <div v-if="lastUpload.blockchain_tx_hash" class="upload-view__result-row">
            <span class="upload-view__result-label">TX Hash</span>
            <code class="upload-view__result-val">{{ lastUpload.blockchain_tx_hash }}</code>
          </div>
          <div class="upload-view__result-row">
            <span class="upload-view__result-label">Status</span>
            <span :class="['badge', `badge--${lastUpload.status}`]">{{ lastUpload.status }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import FileUploader from '../components/FileUploader.vue'
import { api } from '../services/apiService'

const route = useRoute()
const caseId = route.params.id

const caseInfo = ref(null)
const isUploading = ref(false)
const uploadStatus = ref('')
const completedSteps = ref(0)
const lastUpload = ref(null)
const uploadError = ref('')

const uploadSteps = [
  'Validate file type & size',
  'Compute SHA-256 hash',
  'Store file securely',
  'Pin to IPFS (optional)',
  'Register on blockchain',
  'Record custody entry',
]

onMounted(async () => {
  try {
    caseInfo.value = await api.get(`/cases/${caseId}`)
  } catch {}
})

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
  }, 600)

  try {
    const token = localStorage.getItem('access_token')

    // Build FormData — file MUST be named 'file' to match FastAPI parameter
    const formData = new FormData()
    formData.append('file', file, file.name)

    // Send request directly with fetch (bypasses apiService issues)
    const response = await fetch(
      `http://localhost:8000/api/v1/evidence/upload?case_id=${caseId}&description=${encodeURIComponent(description || '')}`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
          // DO NOT set Content-Type — browser sets it with correct boundary for multipart
        },
        body: formData,
      }
    )

    clearInterval(interval)

    if (!response.ok) {
      // Extract readable error message from backend response
      let errorMsg = `Upload failed (HTTP ${response.status})`
      try {
        const errData = await response.json()
        if (typeof errData.detail === 'string') {
          errorMsg = errData.detail
        } else if (Array.isArray(errData.detail)) {
          errorMsg = errData.detail.map(e => e.msg || JSON.stringify(e)).join(', ')
        } else if (errData.message) {
          errorMsg = errData.message
        }
      } catch {}
      throw new Error(errorMsg)
    }

    const data = await response.json()
    completedSteps.value = uploadSteps.length
    uploadStatus.value   = 'Complete!'
    lastUpload.value     = data

  } catch (err) {
    clearInterval(interval)
    // Extract the actual string message — never show [object Object]
    const msg = (err && err.message) ? err.message : String(err)
    uploadError.value = msg
  } finally {
    isUploading.value = false
  }
}
</script>

<style scoped>
.upload-view { padding: 32px 24px; }

.upload-view__back { margin-bottom: 20px; }
.back-link { font-size: 0.78rem; color: var(--text-muted); letter-spacing: 0.06em; }
.back-link:hover { color: var(--amber); text-decoration: none; }

.upload-view__header { margin-bottom: 32px; }
.upload-view__case-id {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 6px;
}
.upload-view__case-id code { color: var(--amber); }

.upload-view__grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
  align-items: start;
}

/* Steps */
.upload-view__info-title {
  font-size: 0.85rem;
  margin-bottom: 18px;
}

.upload-view__steps {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.upload-view__steps li {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.78rem;
  color: var(--text-muted);
  transition: color 0.3s;
}

.step--done  { color: var(--green-ok) !important; }
.step--active { color: var(--amber) !important; }

.step__num {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: 50%;
  font-size: 0.65rem;
  flex-shrink: 0;
  transition: all 0.3s;
}

.step--done .step__num {
  background: var(--green-ok);
  border-color: var(--green-ok);
  color: #fff;
}

.step--active .step__num {
  border-color: var(--amber);
  color: var(--amber);
  animation: pulse-amber 1.5s infinite;
}

/* Success */
.upload-view__success {
  margin-top: 16px;
  border-color: var(--border-amber);
  background: var(--amber-glow);
}

.upload-view__success-title {
  font-size: 0.9rem;
  color: var(--amber);
  margin-bottom: 16px;
}

.upload-view__result-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.upload-view__result-label {
  font-size: 0.62rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  width: 70px;
  flex-shrink: 0;
}

.upload-view__result-val {
  font-size: 0.68rem;
  color: var(--text-secondary);
  word-break: break-all;
}

@media (max-width: 768px) {
  .upload-view__grid { grid-template-columns: 1fr; }
}

.upload-view__error {
  background: rgba(239,68,68,0.1);
  border: 1px solid rgba(239,68,68,0.4);
  color: var(--red-alert);
  padding: 14px 16px;
  border-radius: var(--radius-lg);
  font-size: 0.82rem;
  line-height: 1.6;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  justify-content: space-between;
  margin-bottom: 16px;
}
.upload-view__error-close {
  background: none; border: none; color: var(--red-alert);
  cursor: pointer; font-size: 1rem; padding: 0 4px;
  flex-shrink: 0; opacity: 0.7;
}
.upload-view__error-close:hover { opacity: 1; }
</style>
