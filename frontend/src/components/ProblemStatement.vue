<template>
  <div class="problem">
    <div class="problem-header">
      <div class="problem-meta">
        <span class="meta-label" :class="diffClass">{{ diffLabel }}</span>
      </div>
      <h1 class="problem-title">{{ problem.title }}</h1>
      <p class="problem-desc" v-html="problem.description"></p>
    </div>

    <div class="examples">
      <div v-for="(ex, i) in problem.examples" :key="i" class="example-card">
        <div class="example-num">{{ String(i + 1).padStart(2, '0') }}</div>
        <div class="example-body">
          <div class="io-row">
            <span class="io-key">in</span>
            <span class="io-val input-val">"{{ ex.input }}"</span>
          </div>
          <div class="io-row">
            <span class="io-key">out</span>
            <span class="io-val output-val">{{ ex.output }}</span>
          </div>
          <div class="example-note">{{ ex.explanation }}</div>
        </div>
      </div>
    </div>

    <div v-if="problem.constraints && problem.constraints.length" class="constraints">
      <div class="constraints-header">限制條件</div>
      <ul class="constraints-list">
        <li v-for="(c, i) in problem.constraints" :key="i" class="constraint-item">
          {{ c }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  problem: { type: Object, required: true },
})

const DIFF_MAP = {
  easy:   { label: '低', cls: 'diff-easy' },
  medium: { label: '中', cls: 'diff-medium' },
  hard:   { label: '高', cls: 'diff-hard' },
}

const diffLabel = computed(() => DIFF_MAP[props.problem.difficulty]?.label ?? '題目')
const diffClass = computed(() => DIFF_MAP[props.problem.difficulty]?.cls ?? '')
</script>

<style scoped>
.problem { border-bottom: 1px solid var(--border); }

.problem-header { padding: 28px 32px 24px; }

.problem-meta { margin-bottom: 12px; }

.meta-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--amber);
  background: var(--amber-dim);
  padding: 3px 8px;
  border-radius: 2px;
}

.diff-easy   { color: var(--green); background: var(--green-dim); }
.diff-medium { color: var(--amber); background: var(--amber-dim); }
.diff-hard   { color: var(--red);   background: var(--red-dim); }

.problem-title {
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.3;
  margin-bottom: 14px;
  letter-spacing: -0.02em;
}

.problem-desc {
  font-family: var(--font-sans);
  font-size: 15px;
  line-height: 1.75;
  color: var(--text-2);
}

.examples {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-top: 1px solid var(--border);
}

.example-card {
  padding: 18px 20px;
  border-right: 1px solid var(--border);
  display: flex;
  gap: 14px;
  align-items: flex-start;
  transition: background 0.15s;
}
.example-card:last-child { border-right: none; }
.example-card:hover { background: var(--surface); }

.example-num {
  font-family: var(--font-mono);
  font-size: 20px;
  font-weight: 600;
  color: var(--border-hi);
  line-height: 1;
  padding-top: 2px;
  flex-shrink: 0;
}

.example-body { flex: 1; min-width: 0; }

.io-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 5px;
}

.io-key {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--text-3);
  text-transform: uppercase;
  width: 22px;
  flex-shrink: 0;
}

.io-val {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.input-val  { color: var(--teal); }
.output-val { color: var(--amber); }

.example-note {
  font-family: var(--font-sans);
  font-size: 12px;
  color: var(--text-3);
  line-height: 1.5;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.constraints {
  padding: 16px 32px 20px;
  border-top: 1px solid var(--border);
}

.constraints-header {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-3);
  margin-bottom: 10px;
}

.constraints-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.constraint-item {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-2);
  padding-left: 14px;
  position: relative;
}

.constraint-item::before {
  content: '·';
  position: absolute;
  left: 0;
  color: var(--amber);
}
</style>
