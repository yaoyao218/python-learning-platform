<template>
  <!-- 遮照填空：同一題連續失敗 threshold 次後，顯示標準答案挖掉關鍵部分的版本 -->
  <div v-if="streak >= threshold && cloze" class="cloze">
    <div class="cloze-head">
      <PencilLine :size="15" />
      <strong>填空提示</strong>
      <span class="streak">已連續 {{ streak }} 次沒通過</span>
    </div>
    <p class="intro">
      這是標準答案把關鍵部分挖掉的版本，共 {{ cloze.blanks }} 個空格。
      想想每個 <code class="sample">____1____</code> 應該填什麼，再寫進自己的程式。
    </p>
    <pre class="code" v-html="codeHtml"></pre>
    <div class="actions">
      <button class="copy" @click="copy">
        <Check v-if="copied" :size="13" /><Copy v-else :size="13" />
        {{ copied ? '已複製' : '複製填空題' }}
      </button>
      <span class="note">通過之後填空提示會收起來</span>
    </div>
  </div>

  <div v-else-if="streak > 0 && streak < threshold" class="countdown">
    <span class="steps" aria-hidden="true">
      <i v-for="n in threshold" :key="n" :class="{ on: n <= streak }"></i>
    </span>
    再連續 {{ threshold - streak }} 次沒通過，會出現填空提示
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { PencilLine, Copy, Check } from 'lucide-vue-next'

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
  border: 1px solid color-mix(in srgb, var(--amber) 40%, transparent);
  border-radius: var(--radius);
  background: var(--amber-soft);
  overflow: hidden;
  animation: cloze-in 0.4s var(--ease) both;
}
@keyframes cloze-in {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: none; }
}

.cloze-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 0;
  color: var(--amber);
  font-size: 13px;
}
.streak { margin-left: auto; font-family: var(--font-mono); font-size: 11.5px; opacity: 0.85; }

.intro { padding: 8px 14px 0; font-size: 13px; line-height: 1.75; color: var(--text-2); }
.sample { background: var(--surface); color: var(--amber); }

.code {
  margin: 12px 14px;
  padding: 12px 14px;
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 12.5px;
  line-height: 1.75;
  color: var(--text);
  overflow-x: auto;
}
.code :deep(.blank) {
  color: var(--surface);
  background: var(--amber);
  border-radius: 4px;
  padding: 0 3px;
  font-weight: 600;
}

.actions { display: flex; align-items: center; gap: 12px; padding: 0 14px 12px; }
.copy {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 11px;
  border: 1px solid var(--amber);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--amber);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.copy:hover { background: color-mix(in srgb, var(--amber) 14%, transparent); }
.note { font-size: 11.5px; color: var(--text-3); }

/* 還差幾次 */
.countdown {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius);
  background: var(--surface-2);
  border: 1px dashed var(--border-hi);
  font-size: 12.5px;
  color: var(--text-2);
}
.steps { display: flex; gap: 4px; }
.steps i { width: 14px; height: 5px; border-radius: 3px; background: var(--surface-3); }
.steps i.on { background: var(--amber); }
</style>
