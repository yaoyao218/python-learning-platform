<template>
  <section class="problem">
    <!-- 分頁：題目 / 虛擬碼。虛擬碼預設不顯示，想自己想的人不會被劇透 -->
    <div class="tabs" role="tablist">
      <button class="tab" role="tab" :aria-selected="tab === 'desc'" :class="{ active: tab === 'desc' }" @click="tab = 'desc'">
        題目
      </button>
      <button
        v-if="problem.pseudocode"
        class="tab"
        role="tab"
        :aria-selected="tab === 'pseudo'"
        :class="{ active: tab === 'pseudo' }"
        @click="tab = 'pseudo'"
      >
        虛擬碼<span class="tab-tip">卡住再看</span>
      </button>
    </div>

    <div class="scroll">
      <article v-if="tab === 'desc'" :key="problem.id + ':desc'" class="pane">
        <div class="level-row">
          <span class="level" :class="diffClass"><i v-for="n in 3" :key="n" :class="{ on: n <= diffNum }"></i></span>
          <span class="level-text">難度 {{ diffLabel }}</span>
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
            <li v-for="(c, i) in problem.constraints" :key="i">{{ c }}</li>
          </ul>
        </template>
      </article>

      <article v-else :key="problem.id + ':pseudo'" class="pane">
        <div class="pseudo-note">
          <Mascot mood="think" :size="52" />
          <p>先自己想過一輪再看喔，學到的會比較多。這是解題的步驟，不是答案。</p>
        </div>
        <div class="pseudo-body" v-html="pseudocodeHtml"></div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import Mascot from './Mascot.vue'
import { renderLite } from '../markdown.js'

const props = defineProps({
  problem: { type: Object, required: true },
})

const tab = ref('desc')
// 換題時回到題目分頁（虛擬碼預設收起來，跟原本行為一致）
watch(() => props.problem.id, () => { tab.value = 'desc' })

const DIFF_MAP = {
  easy:   { label: '低', num: 1, cls: 'lv-easy' },
  medium: { label: '中', num: 2, cls: 'lv-medium' },
  hard:   { label: '高', num: 3, cls: 'lv-hard' },
}
const diffLabel = computed(() => DIFF_MAP[props.problem.difficulty]?.label ?? '—')
const diffNum = computed(() => DIFF_MAP[props.problem.difficulty]?.num ?? 1)
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
  border: var(--bw) solid var(--ink);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-hard);
  overflow: hidden;
}

/* 活頁夾分頁 */
.tabs {
  display: flex;
  gap: 6px;
  padding: 10px 12px 0;
  background: var(--surface-2);
  border-bottom: var(--bw) solid var(--ink);
  flex-shrink: 0;
}
.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 18px 8px;
  border: var(--bw) solid transparent;
  border-bottom: none;
  border-radius: 12px 12px 0 0;
  background: transparent;
  color: var(--text-2);
  font-family: var(--font-display);
  font-size: 15px;
  cursor: pointer;
  margin-bottom: calc(var(--bw) * -1);
  transition: color 0.15s, background 0.15s;
}
.tab:hover { color: var(--text); }
.tab.active {
  background: var(--surface);
  color: var(--text);
  border-color: var(--ink);
  padding-bottom: 10px;
}
.tab-tip {
  font-family: var(--font-sans);
  font-size: 11px;
  color: var(--blue);
}

.scroll { flex: 1; min-height: 0; overflow-y: auto; }
.pane { padding: 22px 26px 34px; animation: fade-in 0.3s var(--ease) both; }
@keyframes fade-in { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: none; } }

.level-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.level { display: flex; gap: 3px; }
.level i { width: 9px; height: 16px; border: 1.5px solid var(--ink); border-radius: 3px; background: var(--surface-3); }
.level.lv-easy i.on   { background: var(--green); }
.level.lv-medium i.on { background: var(--sun); }
.level.lv-hard i.on   { background: var(--red); }
.level-text { font-size: 12.5px; color: var(--text-2); }

.title {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 25px;
  line-height: 1.4;
  margin-bottom: 14px;
}

.desc { font-size: 15.5px; line-height: 1.95; color: var(--text-2); }
.desc :deep(strong) { color: var(--text); background: linear-gradient(transparent 62%, color-mix(in srgb, var(--sun) 75%, transparent) 62%); }

.section-title {
  margin: 30px 0 12px;
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.section-title::after { content: ''; flex: 1; border-top: 2px dashed var(--line); }

.examples { display: flex; flex-direction: column; gap: 14px; }

.example {
  background: var(--surface-2);
  border: var(--bw) solid var(--ink);
  border-radius: var(--radius);
  padding: 12px 16px 14px;
  box-shadow: var(--shadow-sm);
}
.example-head { font-family: var(--font-display); font-size: 13px; color: var(--text-3); margin-bottom: 9px; }
.io { display: flex; flex-direction: column; gap: 8px; }
.io-row { display: flex; align-items: baseline; gap: 12px; min-width: 0; }
.io-key { font-size: 12.5px; color: var(--text-3); width: 30px; flex-shrink: 0; }
.io-val {
  font-size: 13.5px;
  padding: 3px 10px;
  background: var(--surface);
  border: 1.5px solid var(--line);
  border-radius: 8px;
  white-space: pre-wrap;
  word-break: break-all;
}
.io-val.in  { color: var(--blue); }
.io-val.out { color: var(--green); font-weight: 600; }
.example-note {
  margin-top: 12px;
  padding-top: 11px;
  border-top: 2px dashed var(--line);
  font-size: 13.5px;
  line-height: 1.75;
  color: var(--text-2);
}

.constraints { list-style: none; display: flex; flex-direction: column; gap: 8px; }
.constraints li { position: relative; padding-left: 20px; font-family: var(--font-mono); font-size: 13px; color: var(--text-2); }
.constraints li::before { content: '✦'; position: absolute; left: 0; color: var(--sun); -webkit-text-stroke: 1px var(--ink); }

/* 虛擬碼 */
.pseudo-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px 8px 10px;
  margin-bottom: 20px;
  background: var(--blue-soft);
  border: var(--bw) dashed var(--blue);
  border-radius: var(--radius);
}
.pseudo-note p { font-size: 13.5px; line-height: 1.7; color: var(--text-2); }
.pseudo-body { font-size: 15px; line-height: 2.05; color: var(--text-2); white-space: pre-wrap; }
.pseudo-body :deep(strong) { color: var(--text); }
.pseudo-body :deep(code) { color: var(--blue); }
.pseudo-body :deep(.md-code) {
  margin: 8px 0;
  padding: 12px 14px;
  background: var(--code-bg);
  border: 1.5px solid var(--ink);
  border-radius: var(--radius-sm);
  overflow-x: auto;
  white-space: pre;
}
.pseudo-body :deep(.md-code code) { background: none; padding: 0; color: var(--text); }

@media (max-width: 900px) {
  .problem { height: auto; }
  .scroll { overflow: visible; }
  .pane { padding: 18px 16px 26px; }
}
</style>
