<template>
  <div class="panel">
    <!-- Empty state -->
    <div v-if="results.length === 0" class="empty-state">
      <div class="empty-icon">◎</div>
      <div class="empty-text">提交程式碼後<br>測試結果會顯示在這裡</div>
    </div>

    <!-- Results -->
    <template v-else>
      <div class="panel-section">
        <div class="section-header">
          <span class="section-label">測試結果</span>
          <span class="result-summary">
            <span :class="passCount === results.length ? 'summary-all' : 'summary-partial'">{{ passCount }}</span>
            <span class="summary-sep"> / {{ results.length }} 通過</span>
          </span>
        </div>
        <div class="progress-bar-wrap">
          <div
            class="progress-bar-fill"
            :class="passCount === results.length ? 'fill-all' : 'fill-partial'"
            :style="{ width: (passCount / results.length * 100) + '%' }"
          ></div>
        </div>

        <div class="result-list">
          <div
            v-for="(result, i) in visibleResults"
            :key="result.index"
            :class="['result-row', result.passed ? 'pass' : 'fail']"
            :style="{ animationDelay: `${i * 50}ms` }"
          >
            <span :class="['status-badge', result.passed ? 'badge-pass' : 'badge-fail']">
              {{ result.passed ? 'PASS' : 'FAIL' }}
            </span>
            <span class="result-num">{{ result.index }}</span>
            <span class="result-input">"{{ result.input }}"</span>
            <div class="result-values">
              <span class="val-expected">→ {{ result.expected }}</span>
              <span v-if="!result.passed" class="val-got">
                got <strong>{{ result.actual ?? 'Error' }}</strong>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Success card (all passed, no hint) -->
      <div v-if="allPassed && !hint" class="panel-section success-section">
        <div class="section-header">
          <span class="section-label success-label">全部通過</span>
        </div>
        <div class="success-body">
          太棒了！你的解法通過了所有 {{ results.length }} 個測試案例。<br>
          試試看能不能讓解法更有效率？
        </div>
      </div>

      <!-- AI Hint skeleton -->
      <div v-if="loading && !hint" class="panel-section hint-section">
        <div class="section-header">
          <span class="section-label hint-label">AI 分析中</span>
          <span class="skeleton-dot-row">
            <span></span><span></span><span></span>
          </span>
        </div>
        <div class="hint-skeleton">
          <div class="sk-line sk-line-80"></div>
          <div class="sk-line sk-line-60"></div>
          <div class="sk-line sk-line-90"></div>
          <div class="sk-line sk-line-50"></div>
        </div>
      </div>

      <!-- AI Hint -->
      <div v-if="hint" class="panel-section hint-section">
        <div class="section-header">
          <span class="section-label hint-label">AI 分析</span>
        </div>
        <div class="hint-body">{{ hint }}</div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  results: { type: Array,    default: () => [] },
  hint:    { type: String,   default: null },
  loading: { type: Boolean,  default: false },
})

const visibleResults = computed(() => {
  const firstFailIdx = props.results.findIndex((r) => !r.passed)
  if (firstFailIdx === -1) return props.results
  return props.results.slice(0, firstFailIdx + 1)
})

const passCount = computed(() =>
  props.results.filter((r) => r.passed).length
)

const allPassed = computed(() =>
  props.results.length > 0 && props.results.every((r) => r.passed)
)
</script>

<style scoped>
.panel {
  min-height: 100%;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 32px;
  gap: 16px;
}

.empty-icon {
  font-size: 32px;
  color: var(--border-hi);
  line-height: 1;
}

.empty-text {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-3);
  text-align: center;
  line-height: 1.8;
  letter-spacing: 0.02em;
}

/* Section */
.panel-section {
  border-bottom: 1px solid var(--border);
}

.section-header {
  padding: 14px 20px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.section-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-3);
}

.hint-label { color: var(--teal); }

.result-summary {
  font-family: var(--font-mono);
  font-size: 11px;
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.summary-all     { color: var(--green); font-weight: 600; font-size: 13px; }
.summary-partial { color: var(--amber); font-weight: 600; font-size: 13px; }
.summary-sep     { color: var(--text-3); }

/* Progress bar */
.progress-bar-wrap {
  height: 2px;
  background: var(--border);
}

.progress-bar-fill {
  height: 100%;
  transition: width 0.4s ease;
}

.fill-all     { background: var(--green); }
.fill-partial { background: var(--amber); }

/* Result rows */
.result-list { padding: 8px 0; }

.result-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 20px;
  border-left: 3px solid transparent;
  animation: row-in 0.25s ease both;
  transition: background 0.12s;
}
.result-row:hover { background: var(--surface); }
.result-row.pass { border-left-color: var(--green); }
.result-row.fail { border-left-color: var(--red); background: color-mix(in srgb, var(--red-dim) 40%, transparent); }

@keyframes row-in {
  from { opacity: 0; transform: translateX(-6px); }
  to   { opacity: 1; transform: translateX(0); }
}

.status-badge {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.08em;
  padding: 2px 6px;
  border-radius: 2px;
  flex-shrink: 0;
}
.badge-pass { background: var(--green-dim); color: var(--green); }
.badge-fail { background: var(--red-dim);   color: var(--red);   }

.result-num {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-3);
  width: 20px;
  flex-shrink: 0;
}

.result-input {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--teal);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-values {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.val-expected {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-3);
}

.val-got {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--red);
}
.val-got strong { color: var(--red); font-weight: 600; }

/* AI Hint skeleton */
.skeleton-dot-row {
  display: flex;
  gap: 4px;
  align-items: center;
}
.skeleton-dot-row span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--teal);
  animation: dot-pulse 1.2s ease-in-out infinite;
}
.skeleton-dot-row span:nth-child(2) { animation-delay: 0.2s; }
.skeleton-dot-row span:nth-child(3) { animation-delay: 0.4s; }

.hint-skeleton {
  margin: 16px 20px;
  padding: 16px;
  background: var(--teal-dim);
  border-left: 2px solid var(--teal);
  border-radius: 0 4px 4px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sk-line {
  height: 10px;
  border-radius: 3px;
  background: color-mix(in srgb, var(--teal) 20%, var(--teal-dim));
  animation: shimmer 1.6s ease-in-out infinite;
}
.sk-line-80 { width: 80%; }
.sk-line-60 { width: 60%; }
.sk-line-90 { width: 90%; }
.sk-line-50 { width: 50%; }

@keyframes shimmer {
  0%, 100% { opacity: 0.4; }
  50%       { opacity: 0.9; }
}

/* AI Hint */
.hint-section { border-bottom: none; }

.hint-body {
  padding: 20px;
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-2);
  white-space: pre-wrap;
  border-left: 2px solid var(--teal);
  margin: 16px 20px;
  padding-left: 16px;
  background: var(--teal-dim);
  border-radius: 0 4px 4px 0;
  animation: hint-in 0.4s ease both;
}

@keyframes hint-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Success card */
.success-section { border-bottom: none; }

.success-label { color: var(--green); }

.success-body {
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-2);
  border-left: 2px solid var(--green);
  margin: 16px 20px;
  padding: 16px;
  background: var(--green-dim);
  border-radius: 0 4px 4px 0;
  animation: hint-in 0.4s ease both;
}
</style>
