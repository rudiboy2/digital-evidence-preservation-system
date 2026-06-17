<template>
  <div id="beps-app">
    <Navbar v-if="isAuthenticated" />
    <main class="main-content">
      <RouterView />
    </main>

    <!-- ── Floating Theme Toggle ── -->
    <button
      class="theme-fab"
      :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
      @click="toggleTheme"
      aria-label="Toggle colour theme"
    >
      <span v-if="isDark">☀</span>
      <span v-else>☽</span>
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Navbar from './components/Navbar.vue'

const isAuthenticated = computed(() => !!localStorage.getItem('access_token'))

// ── Theme ──────────────────────────────────────────────────────────────────
const isDark = ref(true)

function applyTheme(dark) {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
  localStorage.setItem('theme', dark ? 'dark' : 'light')
  isDark.value = dark
}

function toggleTheme() {
  applyTheme(!isDark.value)
}

onMounted(() => {
  const saved = localStorage.getItem('theme')
  applyTheme(saved !== 'light') // default to dark
})
</script>

<style>
/* ============================================================
   BEPS Global Styles — Industrial Forensic Aesthetic
   Typefaces: "Courier Prime" (mono data) + "Barlow Condensed" (display)
   Palette (dark):  Near-black background, amber accents, cool greys
   Palette (light): Oceanic blue — soft blue-whites, deep teal accents
   ============================================================ */

@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700&family=Courier+Prime:wght@400;700&family=IBM+Plex+Mono:wght@300;400;500&display=swap');

/* ── Dark theme (default) ─────────────────────────────────── */
:root,
[data-theme="dark"] {
  --bg-primary:    #0a0c0f;
  --bg-secondary:  #111318;
  --bg-card:       #161a21;
  --bg-elevated:   #1c2029;

  --amber:         #f59e0b;
  --amber-dim:     #b45309;
  --amber-glow:    rgba(245, 158, 11, 0.12);

  --green-ok:      #10b981;
  --red-alert:     #ef4444;
  --blue-info:     #3b82f6;

  --text-primary:  #e8eaf0;
  --text-secondary:#8b95a8;
  --text-muted:    #4a5568;

  --border:        rgba(255,255,255,0.07);
  --border-amber:  rgba(245, 158, 11, 0.3);

  --shadow-card:   0 4px 24px rgba(0,0,0,0.5);
  --shadow-glow:   0 0 20px rgba(245, 158, 11, 0.15);

  /* FAB */
  --fab-bg:        #1c2029;
  --fab-border:    rgba(255,255,255,0.1);
  --fab-color:     #f59e0b;
  --fab-hover-bg:  #252c38;
}

/* ── Light / Oceanic Blue theme ───────────────────────────── */
[data-theme="light"] {
  --bg-primary:    #e8f4f8;
  --bg-secondary:  #d0e8f0;
  --bg-card:       #f0f8fc;
  --bg-elevated:   #ffffff;

  /* Keep the accent teal-leaning to feel "oceanic" */
  --amber:         #0e7490;   /* deep teal replaces amber as primary accent  */
  --amber-dim:     #0a5c73;
  --amber-glow:    rgba(14, 116, 144, 0.12);

  --green-ok:      #0d9488;
  --red-alert:     #dc2626;
  --blue-info:     #2563eb;

  --text-primary:  #0f2d3d;
  --text-secondary:#2e5f74;
  --text-muted:    #6b9aaa;

  --border:        rgba(14, 116, 144, 0.15);
  --border-amber:  rgba(14, 116, 144, 0.35);

  --shadow-card:   0 4px 16px rgba(14,116,144,0.1);
  --shadow-glow:   0 0 20px rgba(14, 116, 144, 0.15);

  /* FAB */
  --fab-bg:        #f0f8fc;
  --fab-border:    rgba(14, 116, 144, 0.25);
  --fab-color:     #0e7490;
  --fab-hover-bg:  #d0e8f0;
}

/* ── Shared / static tokens ───────────────────────────────── */
:root {
  --font-display:  'Barlow Condensed', sans-serif;
  --font-mono:     'IBM Plex Mono', 'Courier Prime', monospace;
  --radius:        4px;
  --radius-lg:     8px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { font-size: 16px; scroll-behavior: smooth; }

body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 0.875rem;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
  transition: background-color 0.25s ease, color 0.25s ease;

  /* Subtle scanline — only in dark mode */
  background-image:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(255,255,255,0.013) 2px,
      rgba(255,255,255,0.013) 4px
    );
}

[data-theme="light"] body,
[data-theme="light"] #beps-app {
  background-image: none; /* remove scanlines in light mode */
}

#beps-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding-top: 64px; /* navbar height */
}

/* ---------- Typography ---------- */
h1, h2, h3, h4 {
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-primary);
}

h1 { font-size: 2.8rem; line-height: 1.1; }
h2 { font-size: 1.9rem; }
h3 { font-size: 1.4rem; }

a { color: var(--amber); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ---------- Utility Classes ---------- */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-card);
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px;
  border-radius: 2px;
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-family: var(--font-mono);
}

.badge--verified  { background: rgba(16,185,129,0.15); color: var(--green-ok);   border: 1px solid rgba(16,185,129,0.3); }
.badge--pending   { background: rgba(245,158,11,0.15);  color: var(--amber);      border: 1px solid var(--border-amber); }
.badge--tampered  { background: rgba(239,68,68,0.15);   color: var(--red-alert);  border: 1px solid rgba(239,68,68,0.3); }
.badge--open      { background: rgba(59,130,246,0.15);  color: var(--blue-info);  border: 1px solid rgba(59,130,246,0.3); }
.badge--closed    { background: rgba(100,116,139,0.15); color: #64748b;           border: 1px solid rgba(100,116,139,0.3); }

/* ---------- Buttons ---------- */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 1px solid transparent;
  border-radius: var(--radius);
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn--primary {
  background: var(--amber);
  color: var(--bg-elevated);
  border-color: var(--amber);
}
.btn--primary:hover { filter: brightness(1.1); box-shadow: var(--shadow-glow); }

.btn--ghost {
  background: transparent;
  color: var(--text-secondary);
  border-color: var(--border);
}
.btn--ghost:hover { border-color: var(--amber); color: var(--amber); }

.btn--danger {
  background: transparent;
  color: var(--red-alert);
  border-color: rgba(239,68,68,0.4);
}
.btn--danger:hover { background: rgba(239,68,68,0.1); }

.btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ---------- Form Elements ---------- */
.form-group { display: flex; flex-direction: column; gap: 6px; }

.form-label {
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.form-input {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 0.875rem;
  padding: 10px 14px;
  transition: border-color 0.2s;
  outline: none;
}
.form-input:focus { border-color: var(--amber); box-shadow: 0 0 0 3px var(--amber-glow); }
.form-input::placeholder { color: var(--text-muted); }

/* ---------- Tables ---------- */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  font-family: var(--font-display);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
  text-align: left;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
}
.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 0.82rem;
}
.data-table tr:hover td { background: var(--bg-elevated); }

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--text-muted); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--amber-dim); }

/* ---------- Animations ---------- */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse-amber {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245,158,11,0.4); }
  50%       { box-shadow: 0 0 0 8px rgba(245,158,11,0); }
}

.fade-up { animation: fadeUp 0.4s ease both; }

/* ---------- Floating Theme Toggle (FAB) ---------- */
.theme-fab {
  position: fixed;
  bottom: 28px;
  right: 28px;  
  z-index: 99999;

  width: 44px;
  height: 44px;
  border-radius: 50%;

  background: var(--fab-bg);
  border: 1px solid var(--fab-border);
  color: var(--fab-color);
  font-size: 1.15rem;
  line-height: 1;

  display: flex;
  align-items: center;
  justify-content: center;

  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0,0,0,0.25);
  transition: background 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
}

.theme-fab:hover {
  background: var(--fab-hover-bg);
  transform: scale(1.08);
  box-shadow: 0 6px 20px rgba(0,0,0,0.3);
}

.theme-fab:active {
  transform: scale(0.95);
}
</style>