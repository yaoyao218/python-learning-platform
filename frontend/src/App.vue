<template>
  <div class="app">
    <header class="topbar">
      <span class="topbar-brand">
        <span class="brand-pip">◈</span>
        <span class="brand-text">Python 學習平台</span>
      </span>
      <span class="topbar-tag">LeetCode #3</span>
    </header>

    <div class="main-layout">
      <div class="left-col">
        <ProblemStatement :problem="problem" />
        <CodeEditor v-model="code" />
        <div class="submit-row">
          <button class="submit-btn" :disabled="loading" @click="handleSubmit">
            <span class="btn-icon">{{ loading ? '⟳' : '▶' }}</span>
            <span>{{ loading ? '執行中...' : '提交程式碼' }}</span>
          </button>
          <span v-if="loading && warmingUp" class="warming-msg">
            ☕ 伺服器冷啟動中，請稍候約 30 秒…
          </span>
          <span v-else-if="loading" class="loading-dots">
            <span></span><span></span><span></span>
          </span>
        </div>
        <div v-if="error" class="error-banner">
          <span class="error-icon">✕</span> {{ error }}
        </div>
      </div>

      <div class="right-col">
        <ResultPanel :results="results" :hint="hint" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ProblemStatement from './components/ProblemStatement.vue'
import CodeEditor from './components/CodeEditor.vue'
import ResultPanel from './components/ResultPanel.vue'
import { submitCode } from './api.js'

const STARTER_CODE = `class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        # 在此撰寫你的解法
        pass
`

const problem = {
  title: 'Longest Substring Without Repeating Characters',
  description: '給定一個字串 <code>s</code>，請找出不含重複字元的<strong>最長子字串</strong>的長度。',
  examples: [
    { input: 'abcabcbb', output: 3, explanation: '最長不重複子字串為 "abc"，長度為 3' },
    { input: 'bbbbb',    output: 1, explanation: '最長子字串為 "b"，長度為 1' },
    { input: 'pwwkew',   output: 3, explanation: '最長不重複子字串為 "wke"，長度為 3' },
  ],
}

const code      = ref(STARTER_CODE)
const results   = ref([])
const hint      = ref(null)
const loading   = ref(false)
const warmingUp = ref(false)
const error     = ref(null)

async function handleSubmit() {
  loading.value   = true
  warmingUp.value = false
  results.value   = []
  hint.value      = null
  error.value     = null

  const warmTimer = setTimeout(() => { warmingUp.value = true }, 5000)

  try {
    const data    = await submitCode(code.value)
    results.value = data.results
    hint.value    = data.hint
  } catch (err) {
    console.error('Submit error:', err)
    error.value = '無法連線到後端，請稍後再試'
  } finally {
    clearTimeout(warmTimer)
    loading.value   = false
    warmingUp.value = false
  }
}
</script>

<style>
:root {
  --bg:        #0c0b09;
  --surface:   #141210;
  --surface-hi:#1d1b17;
  --border:    #252220;
  --border-hi: #36322c;
  --text:      #ede4d0;
  --text-2:    #9a9080;
  --text-3:    #5a544c;
  --amber:     #dfa050;
  --amber-dim: #3a2b16;
  --green:     #5cb87c;
  --green-dim: #192e22;
  --red:       #d96870;
  --red-dim:   #391820;
  --teal:      #5ab8b2;
  --teal-dim:  #163230;
  --font-mono: 'IBM Plex Mono', monospace;
  --font-sans: 'IBM Plex Sans', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  height: 100%;
}

body {
  background-color: var(--bg);
  background-image:
    radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size: 28px 28px;
  font-family: var(--font-sans);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
}

code {
  font-family: var(--font-mono);
  font-size: 0.875em;
  background: var(--surface-hi);
  color: var(--amber);
  padding: 2px 7px;
  border-radius: 3px;
  border: 1px solid var(--border-hi);
}

strong { font-weight: 600; }

.app { min-height: 100vh; display: flex; flex-direction: column; }

/* ── Topbar ── */
.topbar {
  height: 52px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.topbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.brand-pip {
  color: var(--amber);
  font-size: 18px;
  line-height: 1;
}

.brand-text { color: var(--text); }

.topbar-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-3);
  border: 1px solid var(--border);
  padding: 3px 10px;
  border-radius: 2px;
}

/* ── Layout ── */
.main-layout {
  display: flex;
  flex: 1;
  align-items: flex-start;
  min-height: 0;
}

.left-col {
  flex: 1;
  min-width: 0;
  border-right: 1px solid var(--border);
}

.right-col {
  width: 500px;
  flex-shrink: 0;
  height: calc(100vh - 52px);
  overflow-y: auto;
  position: sticky;
  top: 52px;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}

/* ── Submit row ── */
.submit-row {
  padding: 20px 32px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 20px;
}

.submit-btn {
  display: flex;
  align-items: center;
  gap: 9px;
  background: var(--amber);
  color: var(--bg);
  border: none;
  padding: 11px 28px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
}

.submit-btn:hover:not(:disabled) { background: #f0b060; }
.submit-btn:active:not(:disabled) { transform: scale(0.98); }
.submit-btn:disabled { background: var(--surface-hi); color: var(--text-3); cursor: not-allowed; }

.btn-icon { font-size: 12px; }

/* Loading dots */
.loading-dots {
  display: flex;
  gap: 5px;
  align-items: center;
}
.loading-dots span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--text-3);
  animation: dot-pulse 1.2s ease-in-out infinite;
}
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-pulse {
  0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

/* ── Error ── */
.error-banner {
  padding: 12px 32px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--red);
  background: var(--red-dim);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
}
.error-icon { font-size: 10px; }

.warming-msg {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--amber);
}
</style>
