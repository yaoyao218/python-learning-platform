<template>
  <div class="app">
    <header class="topbar">
      <span class="topbar-brand">
        <span class="brand-pip">◈</span>
        <span class="brand-text">Python 學習平台</span>
      </span>
      <select
        v-if="problemList.length"
        class="problem-select"
        :value="problemId"
        @change="onProblemChange"
      >
        <option v-for="p in problemList" :key="p.id" :value="p.id">
          {{ p.title }}（{{ diffLabel(p.difficulty) }}）
        </option>
      </select>
    </header>

    <div class="main-layout">
      <div class="left-col">
        <ProblemStatement v-if="problem" :problem="problem" />
        <CodeEditor v-model="code" />
        <div class="submit-row">
          <button class="submit-btn" :disabled="loading || !problemId" @click="handleSubmit">
            <Loader2 v-if="loading" :size="14" class="btn-spinner" />
            <Play v-else :size="14" />
            <span>{{ loading ? '執行中...' : '提交程式碼' }}</span>
          </button>
          <span v-if="loading" class="loading-dots">
            <span></span><span></span><span></span>
          </span>
        </div>
        <div v-if="error" class="error-banner">
          <X :size="12" />{{ error }}
        </div>
      </div>

      <div class="right-col">
        <ResultPanel :results="results" :hint="hint" :loading="loading" />
        <ClozePanel
          v-if="!loading"
          :streak="currentStreak"
          :threshold="CLOZE_AFTER"
          :cloze="clozeByProblem[problemId] ?? null"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Play, Loader2, X } from 'lucide-vue-next'
import ProblemStatement from './components/ProblemStatement.vue'
import CodeEditor from './components/CodeEditor.vue'
import ResultPanel from './components/ResultPanel.vue'
import ClozePanel from './components/ClozePanel.vue'
import { fetchProblemList, fetchProblem, submitCode, fetchCloze } from './api.js'

const DIFF_LABELS = { easy: '低', medium: '中', hard: '高' }
function diffLabel(difficulty) {
  return DIFF_LABELS[difficulty] ?? difficulty
}

const problemList = ref([])   // [{ id, title, difficulty }]
const problemId   = ref(null)
const problem     = ref(null) // 目前選中題目的完整內容
const code        = ref('')
const results     = ref([])
const hint        = ref(null)
const loading     = ref(false)
const error       = ref(null)

// 遮照填空：同一題連續 CLOZE_AFTER 次沒全部通過，就顯示標準答案挖洞的版本；通過就歸零。
// 這是最保守的「公佈答案」：必須在同一次開啟頁面時連續錯到門檻才出現，
// 所以次數只記在記憶體裡，重新整理就歸零（不存瀏覽器）。換題再換回來會保留。
const CLOZE_AFTER = 3
const failStreaks    = ref({})
const clozeByProblem = ref({})
const currentStreak  = computed(() => failStreaks.value[problemId.value] ?? 0)

function setStreak(id, n) {
  failStreaks.value = { ...failStreaks.value, [id]: n }
}

async function loadClozeIfNeeded(id) {
  if ((failStreaks.value[id] ?? 0) < CLOZE_AFTER || clozeByProblem.value[id]) return
  try {
    const data = await fetchCloze(id)
    clozeByProblem.value = { ...clozeByProblem.value, [id]: data }
  } catch (err) {
    console.error('Load cloze error:', err)   // 拿不到就不顯示填空，不打擾學生
  }
}

// 非同步請求的編號：回來時若編號已經不是最新的，代表使用者已經換題或
// 重新提交，結果直接丟掉，避免舊題的結果蓋到新題上
let problemSeq = 0
let submitSeq  = 0

function describeError(err, fallback) {
  if (err.code === 'ECONNABORTED') return '後端回應逾時（免費主機可能還在喚醒，請稍等幾十秒再試）'
  const status = err.response?.status
  if (status === 404) return '找不到這個題目'
  if (status === 422) return '送出的資料格式不正確'
  if (status) return `後端發生錯誤（HTTP ${status}），請稍後再試`
  return fallback
}

onMounted(async () => {
  try {
    problemList.value = await fetchProblemList()
    if (problemList.value.length) {
      await selectProblem(problemList.value[0].id)
    }
  } catch (err) {
    console.error('Load problem list error:', err)
    error.value = '無法載入題目清單'
  }
})

async function selectProblem(id) {
  const seq = ++problemSeq
  try {
    const data      = await fetchProblem(id)
    if (seq !== problemSeq) return
    submitSeq++            // 換題成功：丟棄還在跑的提交
    loading.value   = false
    problem.value   = data
    problemId.value = id
    code.value      = data.starter_code
    results.value   = []
    hint.value       = null
    error.value      = null
    loadClozeIfNeeded(id)
  } catch (err) {
    if (seq !== problemSeq) return
    console.error('Load problem error:', err)
    error.value = describeError(err, '無法載入題目')
  }
}

function onProblemChange(event) {
  selectProblem(event.target.value)
}

async function handleSubmit() {
  if (!problemId.value) return
  const seq = ++submitSeq
  loading.value = true
  results.value = []
  hint.value    = null
  error.value   = null

  try {
    const data    = await submitCode(code.value, problemId.value)
    if (seq !== submitSeq) return
    results.value = data.results
    hint.value    = data.hint
    if (data.results.length) {
      const id = problemId.value
      const allPassed = data.results.every((r) => r.passed)
      setStreak(id, allPassed ? 0 : (failStreaks.value[id] ?? 0) + 1)
      loadClozeIfNeeded(id)
    }
  } catch (err) {
    if (seq !== submitSeq) return
    console.error('Submit error:', err)
    error.value = describeError(err, '無法連線到後端，請稍後再試')
  } finally {
    if (seq === submitSeq) loading.value = false
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

.problem-select {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  background: var(--surface-hi);
  border: 1px solid var(--border);
  padding: 6px 10px;
  border-radius: 3px;
  cursor: pointer;
  max-width: 380px;
}

.problem-select:hover {
  border-color: var(--border-hi);
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

.btn-spinner {
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

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


/* 窄螢幕（手機、平板直向）：左右兩欄改成上下排，右欄不再固定 500px 寬與 sticky */
@media (max-width: 900px) {
  .topbar { padding: 0 16px; gap: 12px; }
  .problem-select { min-width: 0; max-width: none; flex: 1; }
  .main-layout { flex-direction: column; align-items: stretch; }
  .right-col {
    width: 100%;
    height: auto;
    position: static;
    overflow: visible;
    border-top: 1px solid var(--border);
  }
  .submit-row, .error-banner { padding-left: 16px; padding-right: 16px; }
}
@media (max-width: 480px) {
  .brand-text { display: none; }
}
</style>
