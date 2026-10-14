<template>
  <!-- 遮照填空：同一題連續失敗 threshold 次後，顯示標準答案挖掉關鍵部分的版本 -->
  <div v-if="streak >= threshold && cloze" class="cloze">
    <div class="cloze-header">
      <span class="cloze-label">填空提示</span>
      <span class="cloze-streak">已連續 {{ streak }} 次沒通過</span>
    </div>
    <div class="cloze-intro">
      這是標準答案把關鍵部分挖掉的版本，共 {{ cloze.blanks }} 個空格。
      想想每個 <code class="cloze-blank-sample">____1____</code> 應該填什麼，再寫進自己的程式。
    </div>
    <pre class="cloze-code" v-html="codeHtml"></pre>
    <div class="cloze-actions">
      <button class="cloze-copy" @click="copy">{{ copied ? '已複製' : '複製填空題' }}</button>
      <span class="cloze-note">通過之後填空提示會收起來</span>
    </div>
  </div>
  <div v-else-if="streak > 0 && streak < threshold" class="cloze-countdown">
    再連續 {{ threshold - streak }} 次沒通過，會出現填空提示
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
  escapeHtml(props.cloze?.code ?? '').replace(/____(\d+)____/g, '<span class="cloze-blank">____$1____</span>')
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
  margin: 16px 20px 20px;
  border: 1px solid var(--amber);
  border-left-width: 4px;
  border-radius: 6px;
  background: var(--amber-dim);
  animation: cloze-in 0.4s ease both;
}
@keyframes cloze-in {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: none; }
}
.cloze-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid color-mix(in srgb, var(--amber) 40%, transparent);
}
.cloze-label {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: var(--amber);
}
.cloze-streak {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--amber);
  opacity: 0.8;
}
.cloze-intro {
  padding: 12px 14px 0;
  font-family: var(--font-sans);
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
}
.cloze-blank-sample {
  font-family: var(--font-mono);
  color: var(--amber);
}
.cloze-code {
  margin: 12px 14px;
  padding: 12px 14px;
  background: var(--bg);
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.7;
  color: var(--text);
  overflow-x: auto;
}
.cloze-code :deep(.cloze-blank) {
  color: var(--bg);
  background: var(--amber);
  border-radius: 3px;
  padding: 0 2px;
  font-weight: 600;
}
.cloze-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 14px 12px;
}
.cloze-copy {
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 5px 10px;
  color: var(--amber);
  background: transparent;
  border: 1px solid var(--amber);
  border-radius: 4px;
  cursor: pointer;
}
.cloze-copy:hover { background: color-mix(in srgb, var(--amber) 15%, transparent); }
.cloze-note {
  font-family: var(--font-sans);
  font-size: 11px;
  color: var(--text-3);
}
.cloze-countdown {
  margin: 12px 20px 16px;
  font-family: var(--font-sans);
  font-size: 12px;
  color: var(--text-3);
}
</style>
