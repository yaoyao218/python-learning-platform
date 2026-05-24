<template>
  <div class="panel">
    <!-- ── Empty state ── -->
    <div v-if="results.length === 0" class="empty-state">
      <div class="empty-icon">◎</div>
      <div class="empty-text">提交程式碼後<br>測試結果會顯示在這裡</div>
    </div>

    <template v-else>
      <!-- ── Test results ── -->
      <div class="panel-section">
        <div class="section-header">
          <span class="section-label">測試結果</span>
          <span class="result-summary">{{ passCount }} / {{ results.length }} 通過</span>
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

      <!-- ── Simple text hint (syntax / runtime / no_return) ── -->
      <div v-if="isStringHint" class="panel-section hint-section">
        <div class="section-header">
          <span class="section-label hint-label">AI 分析</span>
        </div>
        <div class="hint-body">{{ hint }}</div>
      </div>

      <!-- ── Interactive diagnosis (wrong_answer) ── -->
      <div v-else-if="isDiagnosis" class="panel-section diag-section">
        <div class="section-header">
          <span class="section-label hint-label">AI 診斷</span>
          <span class="diag-round">第 {{ diagAttempt }} 輪</span>
        </div>

        <!-- Phase: selecting options -->
        <div v-if="diagPhase === 'options'" class="diag-body">
          <div class="diag-intro">{{ diagIntro }}</div>

          <div class="diag-options">
            <label
              v-for="opt in diagOptions"
              :key="opt.id"
              :class="['diag-option', diagSelected === opt.id ? 'selected' : '']"
              @click="diagSelected = opt.id"
            >
              <span class="opt-radio">
                <span v-if="diagSelected === opt.id" class="opt-dot"></span>
              </span>
              <span class="opt-id">{{ opt.id }}</span>
              <span class="opt-text">{{ opt.text }}</span>
            </label>
          </div>

          <!-- Wrong-answer message from previous round -->
          <div v-if="diagMessage" class="diag-wrong-msg">
            <span class="wrong-icon">✕</span>
            {{ diagMessage }}
          </div>

          <button
            class="diag-btn"
            :disabled="!diagSelected || diagLoading"
            @click="submitDiagnosis"
          >
            <span class="diag-btn-icon">{{ diagLoading ? '⟳' : '▶' }}</span>
            {{ diagLoading ? '分析中...' : '確認選項' }}
          </button>
        </div>

        <!-- Phase: correct option → show hint -->
        <div v-else-if="diagPhase === 'hint'" class="diag-body">
          <div class="diag-correct-banner">
            <span class="correct-icon">✓</span> 找到問題了！
          </div>
          <div class="hint-body">{{ diagHint }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { submitHint } from '../api.js'

const props = defineProps({
  results: { type: Array,          default: () => [] },
  hint:    { type: [String, Object], default: null },
  code:    { type: String,         default: '' },
})

// ── Visible results (up to first FAIL) ───────────────────────────────────────
const visibleResults = computed(() => {
  const idx = props.results.findIndex((r) => !r.passed)
  return idx === -1 ? props.results : props.results.slice(0, idx + 1)
})

const passCount = computed(() => props.results.filter((r) => r.passed).length)

// ── Hint type ─────────────────────────────────────────────────────────────────
const isStringHint = computed(() => typeof props.hint === 'string')
const isDiagnosis  = computed(
  () => props.hint && typeof props.hint === 'object' && props.hint.type === 'diagnosis',
)

// ── Diagnosis local state ─────────────────────────────────────────────────────
const diagPhase    = ref('options')
const diagIntro    = ref('')
const diagOptions  = ref([])
const diagSelected = ref(null)
const diagHint     = ref('')
const diagMessage  = ref('')
const diagAttempt  = ref(1)
const diagLoading  = ref(false)

// Reset state whenever a new diagnosis arrives (new submission)
watch(
  () => props.hint,
  (val) => {
    if (val && typeof val === 'object' && val.type === 'diagnosis') {
      diagPhase.value    = 'options'
      diagIntro.value    = val.intro
      diagOptions.value  = val.options
      diagSelected.value = null
      diagHint.value     = ''
      diagMessage.value  = ''
      diagAttempt.value  = 1
    }
  },
  { immediate: true },
)

// ── Submit selected option to /hint ──────────────────────────────────────────
async function submitDiagnosis() {
  if (!diagSelected.value || diagLoading.value) return
  const opt = diagOptions.value.find((o) => o.id === diagSelected.value)
  if (!opt) return

  diagLoading.value = true
  diagMessage.value = ''

  try {
    const res = await submitHint(props.code, props.results, opt.text, diagAttempt.value)
    if (res.correct) {
      diagPhase.value = 'hint'
      diagHint.value  = res.hint
    } else {
      // Wrong → show new options for another round
      diagMessage.value  = res.message
      diagOptions.value  = res.options
      diagSelected.value = null
      diagAttempt.value += 1
    }
  } catch {
    diagMessage.value = '系統暫時無法回應，請稍後重試。'
  } finally {
    diagLoading.value = false
  }
}
</script>

<style scoped>
.panel { min-height: 100%; }

/* ── Empty state ── */
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

/* ── Sections ── */
.panel-section { border-bottom: 1px solid var(--border); }

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

/* ── Result rows ── */
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
.result-row.pass  { border-left-color: var(--green); }
.result-row.fail  {
  border-left-color: var(--red);
  background: color-mix(in srgb, var(--red-dim) 40%, transparent);
}

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
.val-got { font-family: var(--font-mono); font-size: 11px; color: var(--red); }
.val-got strong { color: var(--red); font-weight: 600; }

/* ── Simple hint ── */
.hint-section { border-bottom: none; }
.hint-body {
  margin: 16px 20px;
  padding: 16px;
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-2);
  white-space: pre-wrap;
  border-left: 2px solid var(--teal);
  background: var(--teal-dim);
  border-radius: 0 4px 4px 0;
  animation: hint-in 0.4s ease both;
}
@keyframes hint-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Interactive diagnosis ── */
.diag-section { border-bottom: none; }

.diag-round {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--amber);
  letter-spacing: 0.06em;
}

.diag-body { padding: 20px; }

.diag-intro {
  font-family: var(--font-sans);
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
  margin-bottom: 16px;
}

/* Options */
.diag-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.diag-option {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  animation: opt-in 0.25s ease both;
}
.diag-option:hover { border-color: var(--border-hi); background: var(--surface-hi); }
.diag-option.selected {
  border-color: var(--amber);
  background: var(--amber-dim);
}

@keyframes opt-in {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}

.opt-radio {
  width: 14px;
  height: 14px;
  border: 1.5px solid var(--border-hi);
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.15s;
}
.diag-option.selected .opt-radio { border-color: var(--amber); }

.opt-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--amber);
}

.opt-id {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--amber);
  width: 16px;
  flex-shrink: 0;
}

.opt-text {
  font-family: var(--font-sans);
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-2);
}
.diag-option.selected .opt-text { color: var(--text); }

/* Wrong message */
.diag-wrong-msg {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 14px;
  background: var(--red-dim);
  border-left: 2px solid var(--red);
  border-radius: 0 4px 4px 0;
  font-family: var(--font-sans);
  font-size: 13px;
  line-height: 1.6;
  color: var(--red);
  animation: hint-in 0.3s ease both;
}
.wrong-icon { font-size: 10px; margin-top: 3px; flex-shrink: 0; }

/* Confirm button */
.diag-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--amber);
  color: var(--bg);
  border: none;
  padding: 9px 22px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.03em;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
}
.diag-btn:hover:not(:disabled)  { background: #f0b060; }
.diag-btn:active:not(:disabled) { transform: scale(0.98); }
.diag-btn:disabled { background: var(--surface-hi); color: var(--text-3); cursor: not-allowed; }

.diag-btn-icon { font-size: 11px; }

/* Correct banner */
.diag-correct-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  margin-bottom: 4px;
  background: var(--green-dim);
  border-left: 2px solid var(--green);
  border-radius: 0 4px 4px 0;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--green);
  letter-spacing: 0.04em;
  animation: hint-in 0.3s ease both;
}
.correct-icon { font-size: 12px; }
</style>
