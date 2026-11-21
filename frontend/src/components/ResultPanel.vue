<template>
  <section class="panel">
    <div class="panel-head">
      <span class="head-title">檢查結果</span>
      <span v-if="results.length" class="count" :class="allPassed ? 'ok' : 'warn'">
        {{ passCount }} / {{ results.length }}
      </span>
      <span v-else class="shortcut"><kbd>Ctrl</kbd> + <kbd>Enter</kbd> 也能提交</span>
    </div>

    <div class="body">
      <!-- 派派說話 -->
      <div class="say-row">
        <Mascot :mood="state.mood" :size="84" />
        <div class="bubble" :key="state.say">{{ state.say }}</div>
      </div>

      <!-- 判題中的骨架 -->
      <div v-if="loading" class="progress-wait" aria-hidden="true"><i></i></div>

      <template v-if="results.length">
        <!-- 每個測資一格 -->
        <div class="segments" aria-label="每個測資的結果">
          <span
            v-for="r in results"
            :key="r.index"
            class="seg"
            :class="r.passed ? 'seg-pass' : (r.skipped ? 'seg-skip' : 'seg-fail')"
          ></span>
        </div>

        <!-- 哪裡不對：用白話對照第一個沒過的測資 -->
        <div v-if="fail && !fail.hasError" class="card diff">
          <div class="card-title">第 {{ fail.index }} 筆測資哪裡不一樣</div>
          <dl>
            <div><dt>給的輸入</dt><dd class="v-in">{{ fail.input }}</dd></div>
            <div><dt>正確答案</dt><dd class="v-ok">{{ fail.expected }}</dd></div>
            <div><dt>你的程式</dt><dd class="v-bad">{{ fail.actual }}</dd></div>
          </dl>
        </div>

        <!-- 錯誤訊息：語法錯誤 / 執行錯誤 / 沒有回傳值時，直接給學生看 -->
        <div v-if="errorDetail" class="card err">
          <div class="card-title">{{ errorDetail.label }}<span class="err-case">第 {{ errorDetail.index }} 筆測資</span></div>
          <pre class="err-body">{{ errorDetail.message }}</pre>
        </div>

        <!-- 測資清單（到第一個失敗為止） -->
        <details class="card list" :open="!allPassed && visibleResults.length <= 6">
          <summary>看每一筆測資 <span class="muted">（{{ visibleResults.length }} 筆）</span></summary>
          <ul>
            <li
              v-for="(r, i) in visibleResults"
              :key="r.index"
              :class="[r.passed ? 'pass' : 'fail']"
              :style="{ animationDelay: `${Math.min(i, 14) * 45}ms` }"
            >
              <span class="mark">{{ r.passed ? '✓' : '✗' }}</span>
              <span class="no">#{{ r.index }}</span>
              <code class="inp" :title="String(r.input)">{{ r.input }}</code>
              <span class="exp">→ {{ r.expected }}</span>
            </li>
          </ul>
        </details>

        <!-- AI 提示沒拿到（API 失敗或額度用完），讓學生知道不是自己的問題 -->
        <p v-if="!allPassed && !hint && !loading" class="notice">
          派派的提示暫時送不過來（不是你的問題），先看上面的對照自己找找看。
        </p>

        <!-- 全過：下一題 -->
        <div v-if="allPassed" class="done">
          <p>試試看能不能讓解法更有效率？</p>
          <button v-if="hasNext" class="btn-sticker" @click="$emit('next')">
            下一關 <ArrowRight :size="16" />
          </button>
          <p v-else class="all-done">五題全部破關，太厲害了！</p>
        </div>

        <!-- AI 提示 -->
        <div v-if="hint" class="note hint">
          <div class="note-title">派派的提示</div>
          <div class="hint-body" v-html="hintHtml"></div>
        </div>
      </template>

      <slot />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowRight } from 'lucide-vue-next'
import Mascot from './Mascot.vue'
import { renderLite } from '../markdown.js'
import { summarize, describeFirstFail } from '../explain.js'

const props = defineProps({
  results: { type: Array,    default: () => [] },
  hint:    { type: [String, null], default: null },
  loading: { type: Boolean,  default: false },
  hasNext: { type: Boolean,  default: false },
})
defineEmits(['next'])

const state = computed(() => summarize({ results: props.results, loading: props.loading }))
const fail = computed(() => describeFirstFail(props.results))

const visibleResults = computed(() => {
  const firstFailIdx = props.results.findIndex((r) => !r.passed)
  if (firstFailIdx === -1) return props.results
  return props.results.slice(0, firstFailIdx + 1)
})

const passCount = computed(() => props.results.filter((r) => r.passed).length)

const ERROR_LABELS = {
  syntax_error:  '語法錯誤',
  runtime_error: '執行錯誤',
  timeout:       '執行超時',
  no_return:     '沒有回傳值',
}

const NO_RETURN_MESSAGE = '函式執行完回傳了 None。檢查看看：算出來的答案有沒有用 return 傳出去？'

// 只顯示第一個失敗的錯誤，跟測資清單「顯示到第一個失敗為止」一致
const errorDetail = computed(() => {
  const firstFail = props.results.find((r) => !r.passed)
  if (!firstFail || !firstFail.error_type) return null
  return {
    index:   firstFail.index,
    label:   ERROR_LABELS[firstFail.error_type] ?? '錯誤',
    message: firstFail.stderr || (firstFail.error_type === 'no_return' ? NO_RETURN_MESSAGE : ''),
  }
})

// AI 提示：先跳脫 HTML，再轉換 **粗體**、`程式`、程式碼區塊
const hintHtml = computed(() => renderLite(props.hint))

const allPassed = computed(() =>
  props.results.length > 0 && props.results.every((r) => r.passed)
)
</script>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: var(--surface);
  border: var(--bw) solid var(--ink);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-hard);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 42px;
  padding: 0 16px;
  background: var(--surface-2);
  border-bottom: var(--bw) solid var(--ink);
  flex-shrink: 0;
}
.head-title { font-family: var(--font-display); font-size: 15px; }
.count {
  font-family: var(--font-mono);
  font-size: 12.5px;
  font-weight: 600;
  padding: 1px 10px;
  border: 1.5px solid var(--ink);
  border-radius: 8px;
}
.count.ok   { background: var(--green-soft); color: var(--green); }
.count.warn { background: var(--amber-soft); color: var(--amber); }
.shortcut { font-size: 12px; color: var(--text-3); }
kbd {
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 1px 5px;
  border: 1.5px solid var(--text-3);
  border-bottom-width: 3px;
  border-radius: 5px;
}

.body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 14px 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 內容比面板高時要捲動，不能被 flex 壓扁 */
.body > :deep(*) { flex-shrink: 0; }

/* 派派 + 對話框 */
.say-row { display: flex; align-items: center; gap: 10px; }
.bubble {
  position: relative;
  flex: 1;
  min-width: 0;
  padding: 12px 16px;
  background: var(--surface);
  border: var(--bw) solid var(--ink);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  font-size: 14.5px;
  line-height: 1.7;
  animation: bubble-in 0.35s var(--spring) both;
}
.bubble::before, .bubble::after {
  content: '';
  position: absolute;
  top: 50%;
  border: 8px solid transparent;
  transform: translateY(-50%);
}
.bubble::before { left: -17px; border-right-color: var(--ink); }
.bubble::after  { left: -13px; border-right-color: var(--surface); }
@keyframes bubble-in {
  from { opacity: 0; transform: translateX(-8px) scale(0.96); }
  to   { opacity: 1; transform: none; }
}

.progress-wait { height: 8px; border: 1.5px solid var(--ink); border-radius: 6px; background: var(--surface-2); overflow: hidden; }
.progress-wait i { display: block; width: 40%; height: 100%; background: var(--sun); animation: slide 1.1s ease-in-out infinite; }
@keyframes slide { 0% { transform: translateX(-100%); } 100% { transform: translateX(260%); } }

/* 每個測資一格 */
.segments { display: flex; gap: 3px; height: 12px; }
.seg { flex: 1; min-width: 3px; border: 1.5px solid var(--ink); border-radius: 4px; }
.seg-pass { background: var(--green); }
.seg-fail { background: var(--red); }
.seg-skip { background: var(--surface-3); }

/* 卡片 */
.card {
  border: var(--bw) solid var(--ink);
  border-radius: var(--radius);
  background: var(--surface);
  overflow: hidden;
}
.card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: var(--surface-2);
  border-bottom: var(--bw) solid var(--ink);
  font-family: var(--font-display);
  font-size: 14px;
}

.diff dl { display: flex; flex-direction: column; }
.diff dl > div { display: flex; align-items: baseline; gap: 14px; padding: 9px 14px; border-top: 1px dashed var(--line); }
.diff dl > div:first-child { border-top: none; }
.diff dt { width: 64px; flex-shrink: 0; font-size: 12.5px; color: var(--text-3); }
.diff dd { font-family: var(--font-mono); font-size: 13px; min-width: 0; word-break: break-all; }
.v-in  { color: var(--blue); }
.v-ok  { color: var(--green); font-weight: 600; }
.v-bad { color: var(--red); font-weight: 600; }

.err .card-title { background: var(--red-soft); color: var(--red); }
.err-case { font-family: var(--font-sans); font-size: 12px; opacity: 0.85; }
.err-body {
  padding: 12px 14px;
  font-family: var(--font-mono);
  font-size: 12.5px;
  line-height: 1.65;
  background: var(--code-bg);
  white-space: pre-wrap;
  overflow-x: auto;
}

/* 測資清單 */
.list summary {
  list-style: none;
  cursor: pointer;
  padding: 9px 14px;
  font-size: 13px;
  font-weight: 700;
  user-select: none;
}
.list summary::-webkit-details-marker { display: none; }
.list summary::before { content: '▸'; display: inline-block; margin-right: 8px; transition: transform 0.15s; }
.list[open] summary::before { transform: rotate(90deg); }
.list summary:hover { background: var(--surface-2); }
.muted { font-weight: 400; color: var(--text-3); }
.list ul { list-style: none; border-top: 1px dashed var(--line); }
.list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 14px;
  font-size: 12.5px;
  animation: row-in 0.25s var(--ease) both;
}
.list li + li { border-top: 1px dashed var(--line); }
.list .mark { width: 14px; font-weight: 700; }
.list .pass .mark { color: var(--green); }
.list .fail .mark { color: var(--red); }
.list .no { font-family: var(--font-mono); color: var(--text-3); }
.list .inp { flex: 1; min-width: 0; background: none; padding: 0; color: var(--blue); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.list .exp { font-family: var(--font-mono); color: var(--text-3); flex-shrink: 0; }
@keyframes row-in { from { opacity: 0; transform: translateX(-6px); } to { opacity: 1; transform: none; } }

.notice { font-size: 13px; line-height: 1.7; color: var(--text-2); padding: 0 4px; }

/* 過關 */
.done {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: var(--bw) dashed var(--green);
  border-radius: var(--radius);
  background: var(--green-soft);
  animation: bubble-in 0.4s var(--spring) both;
}
.done p { font-size: 13.5px; color: var(--text-2); }
.done .all-done { font-family: var(--font-display); font-size: 15px; color: var(--green); }

/* AI 提示：便利貼 */
.note {
  position: relative;
  padding: 14px 16px 14px;
  background: #fff3a8;
  color: #2b2a33;
  border: var(--bw) solid var(--ink);
  border-radius: 6px 6px 6px 18px;
  box-shadow: var(--shadow-sm);
  transform: rotate(-0.4deg);
  animation: bubble-in 0.4s var(--spring) both;
}
:root[data-theme='dark'] .note { background: #f3d96b; }
.note-title { font-family: var(--font-display); font-size: 14px; margin-bottom: 6px; }
.hint-body { font-size: 14px; line-height: 1.85; white-space: pre-wrap; }
.hint-body :deep(strong) { font-weight: 700; background: linear-gradient(transparent 60%, rgba(255, 140, 60, 0.45) 60%); }
.hint-body :deep(code) { background: rgba(43, 42, 51, 0.1); color: #2b2a33; }
.hint-body :deep(.md-code) {
  margin: 8px 0;
  padding: 10px 12px;
  background: rgba(43, 42, 51, 0.88);
  border-radius: 8px;
  overflow-x: auto;
  white-space: pre;
}
.hint-body :deep(.md-code code) { background: none; color: #fff3a8; padding: 0; }

@media (max-width: 900px) {
  .panel { height: auto; }
  .body { overflow: visible; }
}
</style>
