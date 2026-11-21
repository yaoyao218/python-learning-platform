<template>
  <section class="problem">
    <!-- 分頁：題目 / 虛擬碼。虛擬碼預設不顯示，想自己想的人不會被劇透 -->
    <div class="tabs" role="tablist">
      <button
        class="tab"
        role="tab"
        :aria-selected="tab === 'desc'"
        :class="{ active: tab === 'desc' }"
        @click="tab = 'desc'"
      >
        <FileText :size="15" />題目
      </button>
      <button
        v-if="problem.pseudocode"
        class="tab"
        role="tab"
        :aria-selected="tab === 'pseudo'"
        :class="{ active: tab === 'pseudo' }"
        @click="tab = 'pseudo'"
      >
        <ListOrdered :size="15" />虛擬碼
        <span class="tab-tip">解題步驟</span>
      </button>
    </div>

    <div class="scroll">
      <article v-if="tab === 'desc'" :key="problem.id + ':desc'" class="pane">
        <div class="meta">
          <span class="diff-pill" :class="diffClass">難度 {{ diffLabel }}</span>
        </div>
        <h1 class="title">{{ problem.title }}</h1>
        <p class="desc" v-html="problem.description"></p>

        <h2 class="section-title">範例</h2>
        <div class="examples">
          <div v-for="(ex, i) in problem.examples" :key="i" class="example">
            <div class="example-head">範例 {{ i + 1 }}</div>
            <div class="io">
              <div class="io-row">
                <span class="io-key">輸入</span>
                <code class="io-val in">{{ ex.input }}</code>
              </div>
              <div class="io-row">
                <span class="io-key">輸出</span>
                <code class="io-val out">{{ ex.output }}</code>
              </div>
            </div>
            <p v-if="ex.explanation" class="example-note">{{ ex.explanation }}</p>
          </div>
        </div>

        <template v-if="problem.constraints && problem.constraints.length">
          <h2 class="section-title">限制條件</h2>
          <ul class="constraints">
            <li v-for="(c, i) in problem.constraints" :key="i"><code>{{ c }}</code></li>
          </ul>
        </template>
      </article>

      <article v-else :key="problem.id + ':pseudo'" class="pane">
        <div class="pseudo-note">
          <Lightbulb :size="15" />
          卡住再看就好。先自己想過一輪，學到的會比較多。
        </div>
        <div class="pseudo-body" v-html="pseudocodeHtml"></div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { FileText, ListOrdered, Lightbulb } from 'lucide-vue-next'
import { renderLite } from '../markdown.js'

const props = defineProps({
  problem: { type: Object, required: true },
})

const tab = ref('desc')
// 換題時回到題目分頁（虛擬碼預設收起來，跟原本行為一致）
watch(() => props.problem.id, () => { tab.value = 'desc' })

const DIFF_MAP = {
  easy:   { label: '低', cls: 'diff-easy' },
  medium: { label: '中', cls: 'diff-medium' },
  hard:   { label: '高', cls: 'diff-hard' },
}
const diffLabel = computed(() => DIFF_MAP[props.problem.difficulty]?.label ?? '—')
const diffClass = computed(() => DIFF_MAP[props.problem.difficulty]?.cls ?? '')

// 虛擬碼是 AI 寫的文字：先跳脫 HTML，再只轉換少數標記（見 markdown.js）
const pseudocodeHtml = computed(() => renderLite(props.problem.pseudocode?.text ?? ''))
</script>

<style scoped>
.problem {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.tabs {
  display: flex;
  gap: 4px;
  padding: 8px 10px 0;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.tab {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 14px;
  border: 1px solid transparent;
  border-bottom: none;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  background: transparent;
  color: var(--text-2);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  margin-bottom: -1px;
  transition: color 0.15s, background 0.15s;
}
.tab:hover { color: var(--text); }
.tab.active {
  background: var(--surface);
  color: var(--text);
  border-color: var(--border);
  font-weight: 700;
}
.tab-tip {
  font-size: 10.5px;
  font-weight: 500;
  color: var(--teal);
  background: var(--teal-soft);
  padding: 1px 7px;
  border-radius: 999px;
}

.scroll { flex: 1; min-height: 0; overflow-y: auto; }
.pane { padding: 24px 26px 32px; animation: fade-in 0.25s var(--ease) both; }

@keyframes fade-in {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: none; }
}

.meta { margin-bottom: 12px; }
.diff-pill {
  display: inline-block;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 999px;
}
.diff-easy   { color: var(--green); background: var(--green-soft); }
.diff-medium { color: var(--amber); background: var(--amber-soft); }
.diff-hard   { color: var(--red);   background: var(--red-soft); }

.title {
  font-size: 22px;
  line-height: 1.35;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin-bottom: 14px;
}

.desc {
  font-size: 15px;
  line-height: 1.85;
  color: var(--text-2);
}
.desc :deep(strong) { color: var(--text); }

.section-title {
  margin: 28px 0 12px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--text-3);
}

.examples { display: flex; flex-direction: column; gap: 12px; }

.example {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
}
.example-head {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-3);
  margin-bottom: 10px;
}
.io { display: flex; flex-direction: column; gap: 8px; }
.io-row { display: flex; align-items: baseline; gap: 12px; min-width: 0; }
.io-key { font-size: 12px; color: var(--text-3); width: 28px; flex-shrink: 0; }
.io-val {
  font-size: 13px;
  padding: 3px 9px;
  background: var(--surface);
  border: 1px solid var(--border);
  white-space: pre-wrap;
  word-break: break-all;
}
.io-val.in  { color: var(--teal); }
.io-val.out { color: var(--amber); }
.example-note {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-hi);
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
}

.constraints { list-style: none; display: flex; flex-direction: column; gap: 8px; }
.constraints li { font-size: 13px; }
.constraints code { color: var(--text-2); }

/* 虛擬碼 */
.pseudo-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 18px;
  border-radius: var(--radius);
  background: var(--teal-soft);
  color: var(--teal);
  font-size: 13px;
  font-weight: 500;
}
.pseudo-body {
  font-size: 14px;
  line-height: 2;
  color: var(--text-2);
  white-space: pre-wrap;
}
.pseudo-body :deep(strong) { color: var(--text); }
.pseudo-body :deep(code) { color: var(--teal); }
.pseudo-body :deep(.md-code) {
  margin: 8px 0;
  padding: 12px 14px;
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow-x: auto;
  white-space: pre;
}
.pseudo-body :deep(.md-code code) { background: none; padding: 0; color: var(--text); }

@media (max-width: 900px) {
  .problem { height: auto; }
  .scroll { overflow: visible; }
  .pane { padding: 18px 16px 24px; }
}
</style>
