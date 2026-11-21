<template>
  <!-- 遮照填空：同一題連續失敗 threshold 次後，顯示標準答案挖掉關鍵部分的版本 -->
  <div v-if="streak >= threshold && cloze" class="cloze">
    <div class="cloze-head">
      <span class="title">填空小抄</span>
      <span class="streak">連續 {{ streak }} 次沒過</span>
    </div>
    <p class="intro">
      這是標準答案把關鍵部分挖掉的版本，共 {{ cloze.blanks }} 個空格。
      想想每個 <code class="sample">____1____</code> 該填什麼，再寫進自己的程式。
    </p>
    <pre class="code" v-html="codeHtml"></pre>
    <div class="actions">
      <button class="copy" @click="copy">{{ copied ? '已複製 ✓' : '複製小抄' }}</button>
      <span class="note">通過之後小抄會收起來</span>
    </div>
  </div>

  <div v-else-if="streak > 0 && streak < threshold" class="countdown">
    <span class="steps" aria-hidden="true">
      <i v-for="n in threshold" :key="n" :class="{ on: n <= streak }"></i>
    </span>
    再連續 {{ threshold - streak }} 次沒通過，派派會給你填空小抄
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  streak:    { type: Number, default: 0 },
  threshold: { type: Number, default: 3 },
  cloze:     { type: [Object, null], default: null },   // { code, blanks }
})

const copied = ref(false)
watch(() => props.cloze, () => { copied.value = false })

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

// 先跳脫 HTML，再把 ____N____ 標成醒目的空格
const codeHtml = computed(() =>
  escapeHtml(props.cloze?.code ?? '').replace(/____(\d+)____/g, '<span class="blank">____$1____</span>')
)

async function copy() {
  try {
    await navigator.clipboard.writeText(props.cloze.code)
    copied.value = true
  } catch {
    copied.value = false
  }
}
</script>

<style scoped>
.cloze {
  border: var(--bw) solid var(--ink);
  border-radius: var(--radius);
  background: var(--amber-soft);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  animation: cloze-in 0.45s var(--spring) both;
}
@keyframes cloze-in { from { opacity: 0; transform: translateY(10px) scale(0.98); } to { opacity: 1; transform: none; } }

.cloze-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: var(--sun);
  color: var(--on-sun);
  border-bottom: var(--bw) solid var(--ink);
}
.title { font-family: var(--font-display); font-size: 15px; }
.streak { font-size: 12px; opacity: 0.8; }

.intro { padding: 10px 14px 0; font-size: 13.5px; line-height: 1.8; color: var(--text-2); }
.sample { background: var(--surface); color: var(--amber); }

.code {
  margin: 12px 14px;
  padding: 12px 14px;
  background: var(--code-bg);
  border: 1.5px solid var(--ink);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 12.5px;
  line-height: 1.75;
  color: var(--text);
  overflow-x: auto;
}
.code :deep(.blank) {
  color: var(--on-sun);
  background: var(--sun);
  border: 1.5px solid var(--ink);
  border-radius: 5px;
  padding: 0 3px;
  font-weight: 600;
}

.actions { display: flex; align-items: center; gap: 12px; padding: 0 14px 12px; }
.copy {
  height: 30px;
  padding: 0 13px;
  border: var(--bw) solid var(--ink);
  border-radius: 9px;
  background: var(--surface);
  color: var(--text);
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: transform 0.12s var(--ease), box-shadow 0.12s var(--ease);
}
.copy:hover { transform: translate(-1px, -1px); box-shadow: 3px 3px 0 var(--ink); }
.copy:active { transform: translate(2px, 2px); box-shadow: none; }
.note { font-size: 12px; color: var(--text-3); }

/* 還差幾次 */
.countdown {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border: var(--bw) dashed var(--ink);
  border-radius: var(--radius);
  font-size: 13px;
  color: var(--text-2);
}
.steps { display: flex; gap: 4px; }
.steps i { width: 16px; height: 8px; border: 1.5px solid var(--ink); border-radius: 4px; background: var(--surface-3); }
.steps i.on { background: var(--sun); }
</style>
