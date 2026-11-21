<template>
  <div class="app">
    <AppHeader
      :problems="problemList"
      :current-id="problemId"
      :solved="solved"
      :theme="theme"
      :streak="streak"
      @select="selectProblem"
      @toggle-theme="toggleTheme"
      @help="tourOpen = true"
    />
    <Tour :open="tourOpen" @close="closeTour" />
    <Confetti :fire="confettiFire" />

    <main class="workspace" :class="{ dragging: leftResizer.dragging.value || bottomResizer.dragging.value }">
      <div class="col-left" :style="leftStyle">
        <ProblemStatement v-if="problem" :problem="problem" />
        <div v-else class="placeholder">
          <Loader2 v-if="!error" :size="20" class="spin" />
          <span>{{ error ? '' : '載入題目中…' }}</span>
        </div>
      </div>

      <div
        class="gutter gutter-x"
        role="separator"
        aria-orientation="vertical"
        tabindex="0"
        title="拖曳調整寬度，雙擊還原"
        @pointerdown.prevent="leftResizer.start"
        @dblclick="leftResizer.reset"
        @keydown.left.prevent="leftResizer.nudge(-24)"
        @keydown.right.prevent="leftResizer.nudge(24)"
      ></div>

      <div class="col-right">
        <div class="editor-box">
          <CodeEditor
            v-model="code"
            :theme="theme"
            @submit="handleSubmit"
            @reset="resetCode"
          >
            <template #actions>
              <button class="btn-sticker submit" :disabled="loading || !problemId" @click="handleSubmit">
                <Loader2 v-if="loading" :size="16" class="spin" />
                <Play v-else :size="14" fill="currentColor" />
                <span>{{ loading ? '檢查中…' : '提交' }}</span>
              </button>
            </template>
          </CodeEditor>
        </div>

        <div
          class="gutter gutter-y"
          role="separator"
          aria-orientation="horizontal"
          tabindex="0"
          title="拖曳調整高度，雙擊還原"
          @pointerdown.prevent="bottomResizer.start"
          @dblclick="bottomResizer.reset"
          @keydown.up.prevent="bottomResizer.nudge(24)"
          @keydown.down.prevent="bottomResizer.nudge(-24)"
        ></div>

        <div class="result-box" :style="bottomStyle">
          <div v-if="error" class="error-banner" role="alert">
            <AlertCircle :size="15" />
            <span>{{ error }}</span>
            <button class="close" aria-label="關閉" @click="error = null"><X :size="14" /></button>
          </div>
          <ResultPanel
            :results="results"
            :hint="hint"
            :loading="loading"
            :has-next="hasNext"
            @next="goNext"
          >
            <ClozePanel
              v-if="!loading"
              :streak="currentStreak"
              :threshold="CLOZE_AFTER"
              :cloze="clozeByProblem[problemId] ?? null"
            />
          </ResultPanel>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { Play, Loader2, X, AlertCircle } from 'lucide-vue-next'
import AppHeader from './components/AppHeader.vue'
import ProblemStatement from './components/ProblemStatement.vue'
import CodeEditor from './components/CodeEditor.vue'
import ResultPanel from './components/ResultPanel.vue'
import ClozePanel from './components/ClozePanel.vue'
import Tour from './components/Tour.vue'
import Confetti from './components/Confetti.vue'
import { useStats } from './composables/useStats.js'
import { fetchProblemList, fetchProblem, submitCode, fetchCloze } from './api.js'
import { useTheme } from './composables/useTheme.js'
import { useResizer } from './composables/useResizer.js'
import { loadItem, saveItem, removeItem } from './composables/storage.js'

const { theme, toggle: toggleTheme } = useTheme()
const { streak, markToday } = useStats()

// 新手導覽：第一次進來自動打開，之後從右上角「？」再開
const tourOpen = ref(!loadItem('pylp:tour-done', false))
function closeTour() {
  tourOpen.value = false
  saveItem('pylp:tour-done', true)
}

// 全部通過時噴紙花
const confettiFire = ref(0)

// ── 版面：左欄寬度、下方結果面板高度（可拖曳，記在瀏覽器）──
const leftResizer = useResizer({
  key: 'pylp:left-w', initial: 520, min: 320,
  max: () => Math.max(360, window.innerWidth - 440),
})
const bottomResizer = useResizer({
  key: 'pylp:bottom-h', initial: Math.max(300, Math.round(window.innerHeight * 0.42)), min: 160, axis: 'y', invert: true,
  max: () => Math.max(200, window.innerHeight - 56 - 220),
})
const leftStyle = computed(() => ({ '--left-w': leftResizer.size.value + 'px' }))
const bottomStyle = computed(() => ({ '--bottom-h': bottomResizer.size.value + 'px' }))

// ── 資料狀態 ──
const problemList = ref([])   // [{ id, title, difficulty }]
const problemId   = ref(null)
const problem     = ref(null) // 目前選中題目的完整內容
const code        = ref('')
const results     = ref([])
const hint        = ref(null)
const loading     = ref(false)
const error       = ref(null)

// 通過過的題目（只記「通過」這件事，方便標勾勾；跟填空的連續失敗次數無關）
const solved = ref(loadItem('pylp:solved', []))

const currentIndex = computed(() => problemList.value.findIndex((p) => p.id === problemId.value))
const hasNext = computed(() => currentIndex.value >= 0 && currentIndex.value < problemList.value.length - 1)

function goNext() {
  if (hasNext.value) selectProblem(problemList.value[currentIndex.value + 1].id)
}

// ── 程式碼草稿：每題各存一份，重新整理不會丟 ──
const draftKey = (id) => `pylp:draft:${id}`
let draftTimer = null
watch(code, (val) => {
  if (!problemId.value || !problem.value) return
  const id = problemId.value
  clearTimeout(draftTimer)
  draftTimer = setTimeout(() => {
    if (val === problem.value?.starter_code) removeItem(draftKey(id))
    else saveItem(draftKey(id), val)
  }, 400)
})

function resetCode() {
  if (!problem.value) return
  if (code.value !== problem.value.starter_code && !window.confirm('要把程式碼還原成起始版本嗎？目前寫的內容會消失。')) return
  code.value = problem.value.starter_code
}

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
  if (id === problemId.value && problem.value) return
  const seq = ++problemSeq
  try {
    const data      = await fetchProblem(id)
    if (seq !== problemSeq) return
    submitSeq++            // 換題成功：丟棄還在跑的提交
    clearTimeout(draftTimer)
    loading.value   = false
    problem.value   = data
    problemId.value = id
    code.value      = loadItem(draftKey(id), null) ?? data.starter_code
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

async function handleSubmit() {
  if (!problemId.value || loading.value) return
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
      markToday()
      if (allPassed) confettiFire.value++
      setStreak(id, allPassed ? 0 : (failStreaks.value[id] ?? 0) + 1)
      if (allPassed && !solved.value.includes(id)) {
        solved.value = [...solved.value, id]
        saveItem('pylp:solved', solved.value)
      }
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

// 全域 Ctrl/⌘ + Enter（編輯器沒聚焦時也能提交；編輯器內由 Monaco 自己註冊）
function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault()
    handleSubmit()
  }
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.app { height: 100%; display: flex; flex-direction: column; min-height: 0; }

.workspace {
  flex: 1;
  min-height: 0;
  display: flex;
  padding: 16px 18px 18px;
  gap: 0;
}
.workspace.dragging :deep(.monaco-editor) { pointer-events: none; }

.col-left {
  width: var(--left-w, 520px);
  flex-shrink: 0;
  min-width: 0;
  min-height: 0;
}

.col-right { flex: 1; min-width: 0; min-height: 0; display: flex; flex-direction: column; }

.editor-box { flex: 1; min-height: 0; }
.result-box {
  height: var(--bottom-h, 340px);
  flex-shrink: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.result-box > :deep(.panel) { flex: 1; }

.placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--text-3);
  background: var(--surface);
  border: var(--bw) solid var(--ink);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-hard);
}

/* ── 分隔線 ── */
.gutter { flex-shrink: 0; position: relative; outline: none; }
.gutter::after {
  content: '';
  position: absolute;
  border-radius: 999px;
  background: var(--ink);
  opacity: 0;
  transition: opacity 0.15s, background 0.15s;
}
.gutter:hover::after, .gutter:focus-visible::after, .workspace.dragging .gutter::after { opacity: 0.8; background: var(--sun); outline: 1.5px solid var(--ink); }
.gutter-x { width: 18px; cursor: col-resize; }
.gutter-x::after { top: 50%; left: 6px; width: 6px; height: 52px; transform: translateY(-50%); }
.gutter-y { height: 18px; cursor: row-resize; }
.gutter-y::after { left: 50%; top: 6px; height: 6px; width: 52px; transform: translateX(-50%); }

/* ── 提交按鈕 ── */
.submit { height: 36px; padding: 0 20px; font-size: 15px; }

.spin { animation: spin 0.9s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 錯誤列 ── */
.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  border: var(--bw) solid var(--ink);
  border-radius: var(--radius);
  background: var(--red-soft);
  color: var(--red);
  font-size: 13px;
  flex-shrink: 0;
}
.error-banner span { flex: 1; min-width: 0; }
.close { display: grid; place-items: center; border: none; background: none; color: inherit; cursor: pointer; opacity: 0.7; }
.close:hover { opacity: 1; }

/* ── 窄螢幕：上下排，整頁捲動 ── */
@media (max-width: 900px) {
  .app { height: auto; min-height: 100%; }
  .workspace { flex-direction: column; padding: 10px; gap: 12px; }
  .col-left { width: 100%; }
  .col-right { gap: 12px; }
  .editor-box { flex: none; }
  .result-box { height: auto; }
  .gutter { display: none; }
}
</style>
