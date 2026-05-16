<template>
  <div class="editor-section">
    <div class="editor-label">
      <span class="label-text">solution.py</span>
      <span class="lang-badge">Python 3</span>
    </div>
    <VueMonacoEditor
      v-model:value="code"
      language="python"
      theme="vs-dark"
      :options="editorOptions"
      style="height: 300px;"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'

const props = defineProps({
  modelValue: { type: String, required: true },
})
const emit = defineEmits(['update:modelValue'])

const code = ref(props.modelValue)
watch(code, (val) => emit('update:modelValue', val))

const editorOptions = {
  fontSize: 14,
  lineHeight: 22,
  fontFamily: "'IBM Plex Mono', monospace",
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 4,
  insertSpaces: true,
  quickSuggestions: true,
  wordBasedSuggestions: true,
  padding: { top: 16, bottom: 16 },
  lineNumbers: 'on',
  renderLineHighlight: 'line',
  scrollbar: { verticalScrollbarSize: 4, horizontalScrollbarSize: 4 },
}
</script>

<style scoped>
.editor-section {
  border-bottom: 1px solid var(--border);
}

.editor-label {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 32px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.label-text {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-2);
  font-weight: 500;
}

.lang-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--teal);
  background: var(--teal-dim);
  padding: 2px 8px;
  border-radius: 2px;
}
</style>
