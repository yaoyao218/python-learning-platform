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
            {{ passCount }} / {{ results.length }} 通過
          </span>
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
  results: { type: Array, default: () => [] },
  hint:    { type: String, default: null },
})

const visibleResults = computed(() => {
  const firstFailIdx = props.results.findIndex((r) => !r.passed)
  if (firstFailIdx === -1) return props.results
  return props.results.slice(0, firstFailIdx + 1)
})

const passCount = computed(() =>
  props.results.filter((r) => r.passed).length
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
  color: var(--text-3);
}

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
</style>
