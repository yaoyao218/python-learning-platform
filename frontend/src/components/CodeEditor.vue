<template>
  <section class="editor">
    <div class="toolbar">
      <div class="file">
        <span class="lights" aria-hidden="true"><i></i><i></i><i></i></span>
        <span class="file-name">solution.py</span>
      </div>
      <div class="actions">
        <button class="ghost" title="還原成起始程式碼" @click="$emit('reset')">重設</button>
        <slot name="actions" />
      </div>
    </div>

    <div class="monaco-wrap">
      <VueMonacoEditor
        v-model:value="code"
        language="python"
        :theme="theme === 'dark' ? 'pylp-dark' : 'pylp-light'"
        :options="editorOptions"
        @before-mount="defineThemes"
        @mount="onMount"
      />
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'

const props = defineProps({
  modelValue: { type: String, required: true },
  theme:      { type: String, default: 'light' },
})
const emit = defineEmits(['update:modelValue', 'submit', 'reset'])

const code = ref(props.modelValue)
watch(code, (val) => emit('update:modelValue', val))
watch(() => props.modelValue, (val) => {
  if (val !== code.value) code.value = val
})

const editorOptions = {
  fontSize: 15,
  lineHeight: 25,
  fontFamily: "'JetBrains Mono', Consolas, monospace",
  fontLigatures: true,
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 4,
  insertSpaces: true,
  quickSuggestions: true,
  wordBasedSuggestions: 'currentDocument',
  padding: { top: 16, bottom: 16 },
  lineNumbers: 'on',
  renderLineHighlight: 'line',
  smoothScrolling: true,
  cursorSmoothCaretAnimation: 'on',
  roundedSelection: true,
  guides: { indentation: true },
  scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
}

// 兩個跟全站配色一致的 Monaco 主題（奶油紙／深藍夜）
function defineThemes(monaco) {
  monaco.editor.defineTheme('pylp-light', {
    base: 'vs',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '9a9484', fontStyle: 'italic' },
      { token: 'keyword', foreground: 'c2410c' },
      { token: 'string', foreground: '1f8a5b' },
      { token: 'number', foreground: '306998' },
    ],
    colors: {
      'editor.background': '#fffdf7',
      'editor.lineHighlightBackground': '#fff3c4',
      'editorLineNumber.foreground': '#c5bca2',
      'editorLineNumber.activeForeground': '#5b5866',
      'editorIndentGuide.background1': '#efe3c4',
      'editorCursor.foreground': '#2b2a33',
    },
  })
  monaco.editor.defineTheme('pylp-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '848077', fontStyle: 'italic' },
      { token: 'keyword', foreground: 'ffb36b' },
      { token: 'string', foreground: '62d6a3' },
      { token: 'number', foreground: '8fc2ee' },
    ],
    colors: {
      'editor.background': '#262b3b',
      'editor.lineHighlightBackground': '#2e3446',
      'editorLineNumber.foreground': '#555d75',
      'editorLineNumber.activeForeground': '#bab6a9',
      'editorIndentGuide.background1': '#343b50',
      'editorCursor.foreground': '#ffd43b',
    },
  })
}

// Ctrl/⌘ + Enter 直接提交（Monaco 會吃掉這組鍵，所以要註冊在編輯器裡）
function onMount(editor, monaco) {
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => emit('submit'))
}
</script>

<style scoped>
.editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: var(--surface);
  border: var(--bw) solid var(--ink);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-hard);
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  height: 52px;
  padding: 0 10px 0 16px;
  background: var(--surface-2);
  border-bottom: var(--bw) solid var(--ink);
  flex-shrink: 0;
}

.file { display: flex; align-items: center; gap: 14px; min-width: 0; }
.lights { display: flex; gap: 6px; }
.lights i { width: 11px; height: 11px; border-radius: 50%; border: 1.5px solid var(--ink); }
.lights i:nth-child(1) { background: #ff7a7a; }
.lights i:nth-child(2) { background: var(--sun); }
.lights i:nth-child(3) { background: #5fd3a0; }
.file-name { font-family: var(--font-mono); font-size: 13px; color: var(--text-2); }

.actions { display: flex; align-items: center; gap: 10px; }

.ghost {
  height: 32px;
  padding: 0 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-2);
  font-size: 13px;
  cursor: pointer;
  text-decoration: underline dotted;
  text-underline-offset: 4px;
}
.ghost:hover { color: var(--text); background: var(--surface-3); }

.monaco-wrap { flex: 1; min-height: 0; }
.monaco-wrap :deep(> div) { height: 100%; }

@media (max-width: 900px) {
  .editor { height: 380px; }
}
</style>
