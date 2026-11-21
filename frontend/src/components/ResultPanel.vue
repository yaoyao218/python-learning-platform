<template>
  <section class="panel">
    <div class="panel-head">
      <div class="head-left">
        <ListChecks :size="16" />
        <span class="head-title">測試結果</span>
      </div>
      <span v-if="results.length" class="count" :class="allPassed ? 'ok' : 'warn'">
        {{ passCount }} / {{ results.length }} 通過
      </span>
      <span v-else class="shortcut">Ctrl + Enter 提交</span>
    </div>

    <div class="body">
      <!-- 還沒提交 -->
      <div v-if="results.length === 0 && !loading" class="empty">
        <div class="empty-icon"><Terminal :size="22" /></div>
        <p>提交程式碼後，測試結果會顯示在這裡</p>
      </div>

      <!-- 判題中（還沒有結果） -->
      <div v-else-if="results.length === 0 && loading" class="empty">
        <Loader2 :size="22" class="spin" />
        <p>正在執行你的程式…</p>
      </div>

      <template v-else>
        <!-- 總結橫幅 -->
        <div class="banner" :class="allPassed ? 'banner-ok' : 'banner-fail'">
          <div class="banner-icon">
            <CheckCircle2 v-if="allPassed" :size="22" />
            <XCircle v-else :size="22" />
          </div>
          <div class="banner-text">
            <strong>{{ allPassed ? '全部通過' : '還沒通過' }}</strong>
            <span>{{ allPassed ? `${results.length} 個測試案例都過了` : `通過 ${passCount} / ${results.length}，下面是第一個沒過的案例` }}</span>
          </div>
          <button v-if="allPassed && hasNext" class="next-btn" @click="$emit('next')">
            下一題<ArrowRight :size="14" />
          </button>
        </div>

        <!-- 每個測資一格的進度條 -->
        <div class="segments" aria-hidden="true">
          <span
            v-for="r in results"
            :key="r.index"
            class="seg"
            :class="r.passed ? 'seg-pass' : (r.skipped ? 'seg-skip' : 'seg-fail')"
          ></span>
        </div>

        <ul class="cases">
          <li
            v-for="(result, i) in visibleResults"
            :key="result.index"
            :class="['case', result.passed ? 'pass' : 'fail']"
            :style="{ animationDelay: `${Math.min(i, 12) * 40}ms` }"
          >
            <span class="case-badge">
              <Check v-if="result.passed" :size="12" :stroke-width="3.2" />
              <X v-else :size="12" :stroke-width="3.2" />
            </span>
            <span class="case-no">#{{ result.index }}</span>
            <code class="case-input" :title="String(result.input)">{{ result.input }}</code>
            <span class="case-values">
              <span class="val-expected">預期 {{ result.expected }}</span>
              <span v-if="!result.passed" class="val-got">
                實際 <strong>{{ result.actual ?? ERROR_LABELS[result.error_type] ?? 'Error' }}</strong>
              </span>
            </span>
          </li>
        </ul>

        <!-- 錯誤訊息：語法錯誤 / 執行錯誤 / 沒有回傳值時，直接給學生看 -->
        <div v-if="errorDetail" class="error">
          <div class="error-head">
            <Bug :size="15" />
            <strong>{{ errorDetail.label }}</strong>
            <span class="error-case">測資 #{{ errorDetail.index }}</span>
          </div>
          <pre class="error-body">{{ errorDetail.message }}</pre>
        </div>

        <!-- AI 提示沒拿到（API 失敗或額度用完），讓學生知道不是自己的問題 -->
        <div v-if="!allPassed && !hint && !loading" class="notice">
          <Info :size="15" />AI 提示暫時無法取得，可以先看上面的測資結果自己找找看。
        </div>

        <!-- 全部通過、沒有提示 -->
        <div v-if="allPassed && !hint" class="success">
          <PartyPopper :size="18" />
          <div>
            <strong>太棒了！</strong>你的解法通過了所有 {{ results.length }} 個測試案例。
            試試看能不能讓解法更有效率？
          </div>
        </div>

        <!-- AI 提示：骨架 -->
        <div v-if="loading && !hint" class="hint hint-loading">
          <div class="hint-head">
            <Sparkles :size="15" />
            <strong>AI 分析中</strong>
            <span class="dots"><span></span><span></span><span></span></span>
          </div>
          <div class="skeleton">
            <i style="width: 82%"></i><i style="width: 64%"></i><i style="width: 92%"></i><i style="width: 48%"></i>
          </div>
        </div>

        <!-- AI 提示 -->
        <div v-if="hint" class="hint">
          <div class="hint-head">
            <Sparkles :size="15" />
            <strong>AI 提示</strong>
          </div>
          <div class="hint-body" v-html="hintHtml"></div>
        </div>
      </template>

      <!-- 骨架：已有結果但 AI 還在跑時，上面的 hint-loading 會顯示；這裡放插槽給填空提示 -->
      <slot />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import {
  ListChecks, Terminal, Loader2, CheckCircle2, XCircle, ArrowRight,
  Check, X, Bug, Info, Sparkles, PartyPopper,
} from 'lucide-vue-next'
import { renderLite } from '../markdown.js'

const props = defineProps({
  results: { type: Array,    default: () => [] },
  hint:    { type: [String, null], default: null },
  loading: { type: Boolean,  default: false },
  hasNext: { type: Boolean,  default: false },
})
defineEmits(['next'])

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

// 只顯示第一個失敗的錯誤，跟測試結果列表「顯示到第一個失敗為止」一致
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
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 0 16px;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.head-left { display: flex; align-items: center; gap: 8px; color: var(--text-2); }
.head-title { font-size: 13px; font-weight: 700; color: var(--text); }

.count { font-family: var(--font-mono); font-size: 12px; font-weight: 600; padding: 2px 10px; border-radius: 999px; }
.count.ok   { color: var(--green); background: var(--green-soft); }
.count.warn { color: var(--amber); background: var(--amber-soft); }
.shortcut { font-family: var(--font-mono); font-size: 11.5px; color: var(--text-3); }

.body { flex: 1; min-height: 0; overflow-y: auto; padding: 14px 16px 18px; display: flex; flex-direction: column; gap: 14px; }

/* 空狀態 */
.empty {
  margin: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--text-3);
  font-size: 13px;
  padding: 24px 0;
}
.empty-icon {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--surface-3);
  color: var(--text-3);
}
.spin { animation: spin 0.9s linear infinite; color: var(--accent); }
@keyframes spin { to { transform: rotate(360deg); } }

/* 橫幅 */
.banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--radius);
  animation: pop-in 0.35s var(--ease) both;
}
.banner-ok   { background: var(--green-soft); color: var(--green); }
.banner-fail { background: var(--red-soft);   color: var(--red); }
.banner-icon { flex-shrink: 0; display: grid; }
.banner-text { display: flex; flex-direction: column; gap: 1px; flex: 1; min-width: 0; }
.banner-text strong { font-size: 15px; }
.banner-text span { font-size: 12.5px; opacity: 0.85; color: var(--text-2); }

.next-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--green);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: filter 0.15s, transform 0.1s;
  flex-shrink: 0;
}
.next-btn:hover { filter: brightness(1.08); }
.next-btn:active { transform: scale(0.97); }

@keyframes pop-in {
  from { opacity: 0; transform: scale(0.97) translateY(4px); }
  to   { opacity: 1; transform: none; }
}

/* 分段進度 */
.segments { display: flex; gap: 2px; height: 6px; margin: -4px 0 -2px; }
.seg { flex: 1; border-radius: 2px; min-width: 2px; }
.seg-pass { background: var(--green); }
.seg-fail { background: var(--red); }
.seg-skip { background: var(--surface-3); }

/* 測資列 */
.cases { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.case {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--border-hi);
  border-radius: var(--radius-sm);
  animation: row-in 0.25s var(--ease) both;
  min-width: 0;
}
.case.pass { border-left-color: var(--green); }
.case.fail { border-left-color: var(--red); background: var(--red-soft); border-color: transparent; border-left-color: var(--red); }
@keyframes row-in {
  from { opacity: 0; transform: translateX(-6px); }
  to   { opacity: 1; transform: none; }
}

.case-badge {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
  flex-shrink: 0;
}
.pass .case-badge { background: var(--green); }
.fail .case-badge { background: var(--red); }

.case-no { font-family: var(--font-mono); font-size: 11.5px; color: var(--text-3); flex-shrink: 0; }
.case-input {
  flex: 1;
  min-width: 0;
  background: none;
  padding: 0;
  color: var(--teal);
  font-size: 12.5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.case-values { display: flex; align-items: center; gap: 10px; flex-shrink: 0; font-family: var(--font-mono); font-size: 12px; }
.val-expected { color: var(--text-3); }
.val-got { color: var(--red); }
.val-got strong { font-weight: 700; }

/* 錯誤訊息 */
.error { border: 1px solid var(--red-soft); border-radius: var(--radius); overflow: hidden; }
.error-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  background: var(--red-soft);
  color: var(--red);
  font-size: 13px;
}
.error-case { margin-left: auto; font-family: var(--font-mono); font-size: 11.5px; opacity: 0.8; }
.error-body {
  padding: 12px 14px;
  font-family: var(--font-mono);
  font-size: 12.5px;
  line-height: 1.65;
  color: var(--text);
  background: var(--code-bg);
  white-space: pre-wrap;
  overflow-x: auto;
}

.notice {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  border-radius: var(--radius);
  background: var(--surface-3);
  color: var(--text-2);
  font-size: 13px;
  line-height: 1.6;
}
.notice svg { margin-top: 3px; flex-shrink: 0; }

.success {
  display: flex;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--radius);
  background: var(--green-soft);
  color: var(--green);
  font-size: 13.5px;
  line-height: 1.7;
}
.success svg { margin-top: 3px; flex-shrink: 0; }
.success div { color: var(--text-2); }
.success strong { color: var(--green); }

/* AI 提示卡 */
.hint {
  border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  border-radius: var(--radius);
  background: var(--accent-soft);
  overflow: hidden;
  animation: pop-in 0.4s var(--ease) both;
}
.hint-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 0;
  color: var(--accent);
  font-size: 13px;
}
.hint-body {
  padding: 8px 14px 14px;
  font-size: 14px;
  line-height: 1.85;
  color: var(--text);
  white-space: pre-wrap;
}
.hint-body :deep(strong) { color: var(--accent-hi); }
.hint-body :deep(code) { background: var(--surface); color: var(--accent); }
.hint-body :deep(.md-code) {
  margin: 8px 0;
  padding: 10px 12px;
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow-x: auto;
  white-space: pre;
}
.hint-body :deep(.md-code code) { background: none; color: var(--text); padding: 0; }

.dots { display: flex; gap: 4px; margin-left: 2px; }
.dots span {
  width: 5px; height: 5px; border-radius: 50%;
  background: var(--accent);
  animation: dot-pulse 1.2s ease-in-out infinite;
}
.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot-pulse {
  0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

.skeleton { display: flex; flex-direction: column; gap: 10px; padding: 14px; }
.skeleton i {
  display: block;
  height: 10px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--accent) 22%, transparent);
  animation: shimmer 1.6s ease-in-out infinite;
}
@keyframes shimmer { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }

@media (max-width: 900px) {
  .panel { height: auto; }
  .body { overflow: visible; }
  .case { flex-wrap: wrap; }
  .case-input { flex-basis: 60%; }
}
</style>
