<template>
  <div
    class="uploader"
    :class="{
      'uploader--dragging': isDragging,
      'uploader--has-file': selectedFile,
      'uploader--uploading': isUploading,
    }"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="onDrop"
    @click="!selectedFile && $refs.fileInput.click()"
  >
    <input
      ref="fileInput"
      type="file"
      class="uploader__input"
      @change="onFileSelect"
    />

    <!-- Empty state -->
    <template v-if="!selectedFile && !isUploading">
      <div class="uploader__icon">⬡</div>
      <p class="uploader__headline">Drop evidence file here</p>
      <p class="uploader__sub">or click to browse — max {{ maxSizeMb }} MB</p>
      <div class="uploader__formats">
        <span v-for="f in acceptedFormats" :key="f" class="uploader__fmt">{{ f }}</span>
      </div>
    </template>

    <!-- File selected -->
    <template v-else-if="selectedFile && !isUploading">
      <div class="uploader__selected">
        <div class="uploader__file-icon">{{ fileIcon }}</div>
        <div class="uploader__file-meta">
          <span class="uploader__file-name">{{ selectedFile.name }}</span>
          <span class="uploader__file-size">{{ formattedSize }}</span>
        </div>
        <button class="uploader__remove" @click.stop="clearFile" title="Remove file">✕</button>
      </div>

      <div class="form-group" style="width:100%; margin-top:16px;" @click.stop>
        <label class="form-label">Evidence Description</label>
        <textarea
          v-model="description"
          class="form-input uploader__desc"
          placeholder="Describe this evidence item, its relevance, and collection context…"
          rows="3"
        />
      </div>

      <button
        class="btn btn--primary uploader__submit"
        :disabled="!description.trim()"
        @click.stop="$emit('upload', { file: selectedFile, description })"
      >
        <span>⬡</span> Register on Blockchain
      </button>
    </template>

    <!-- Uploading -->
    <template v-else-if="isUploading">
      <div class="uploader__progress">
        <div class="uploader__spinner" />
        <p class="uploader__progress-text">{{ uploadStatus }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  isUploading:  { type: Boolean, default: false },
  uploadStatus: { type: String, default: 'Uploading…' },
  maxSizeMb:    { type: Number, default: 500 },
  acceptedFormats: {
    type: Array,
    default: () => ['PDF', 'Images', 'Video', 'Audio', 'Documents'],
  },
})

const emit = defineEmits(['upload'])

const isDragging   = ref(false)
const selectedFile = ref(null)
const description  = ref('')
const fileInput    = ref(null)

const ICONS = {
  'image/':       '🖼',
  'video/':       '🎥',
  'audio/':       '🎙',
  'application/pdf': '📄',
  'text/':        '📝',
}

const fileIcon = computed(() => {
  if (!selectedFile.value) return '📁'
  const mime = selectedFile.value.type
  for (const [prefix, icon] of Object.entries(ICONS)) {
    if (mime.startsWith(prefix)) return icon
  }
  return '💾'
})

const formattedSize = computed(() => {
  if (!selectedFile.value) return ''
  const bytes = selectedFile.value.size
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
})

function onDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) applyFile(file)
}

function onFileSelect(e) {
  const file = e.target.files[0]
  if (file) applyFile(file)
}

function applyFile(file) {
  const maxBytes = props.maxSizeMb * 1024 * 1024
  if (file.size > maxBytes) {
    alert(`File exceeds the ${props.maxSizeMb} MB limit.`)
    return
  }
  selectedFile.value = file
  description.value  = ''
}

function clearFile() {
  selectedFile.value = null
  description.value  = ''
  if (fileInput.value) fileInput.value.value = ''
}
</script>

<style scoped>
.uploader {
  position: relative;
  border: 2px dashed var(--border);
  border-radius: var(--radius-lg);
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  min-height: 200px;
  justify-content: center;
  text-align: center;
}

.uploader:hover,
.uploader--dragging {
  border-color: var(--amber);
  background: var(--amber-glow);
}

.uploader--has-file {
  cursor: default;
  border-style: solid;
  border-color: var(--border-amber);
  background: var(--bg-elevated);
}

.uploader__input {
  display: none;
}

.uploader__icon {
  font-size: 2.5rem;
  color: var(--amber);
  line-height: 1;
}

.uploader__headline {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-primary);
}

.uploader__sub {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.uploader__formats {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 4px;
}

.uploader__fmt {
  font-size: 0.65rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 2px 8px;
  border: 1px solid var(--border);
  border-radius: 2px;
  color: var(--text-muted);
}

.uploader__selected {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 16px;
}

.uploader__file-icon { font-size: 1.6rem; }

.uploader__file-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  min-width: 0;
}

.uploader__file-name {
  font-size: 0.85rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 320px;
}

.uploader__file-size {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.uploader__remove {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 4px;
  transition: color 0.2s;
  flex-shrink: 0;
}
.uploader__remove:hover { color: var(--red-alert); }

.uploader__desc {
  resize: vertical;
  min-height: 72px;
}

.uploader__submit { margin-top: 8px; }

/* Progress */
.uploader__progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.uploader__spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--amber);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.uploader__progress-text {
  font-size: 0.8rem;
  color: var(--amber);
  letter-spacing: 0.06em;
}
</style>
