<template>
  <section class="editor">
    <div class="toolbar">
      <div class="file">
        <FileCode2 :size="15" />
        <span class="file-name">solution.py</span>
        <span class="lang">Python 3</span>
      </div>
      <div class="actions">
        <button class="ghost" title="還原成起始程式碼" @click="$emit('reset')">
          <RotateCcw :size="14" />重設
        </button>
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
import { FileCode2, RotateCcw } from 'lucide-vue-next'

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
  fontSize: 14,
  lineHeight: 23,
  fontFamily: "'JetBrains Mono', Consolas, monospace",
  fontLigatures: true,
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 4,
  insertSpaces: true,
  quickSuggestions: true,
  wordBasedSuggestions: 'currentDocument',
  padding: { top: 14, bottom: 14 },
  lineNumbers: 'on',
  renderLineHighlight: 'line',
  smoothScrolling: true,
  cursorSmoothCaretAnimation: 'on',
  roundedSelection: true,
  guides: { indentation: true },
  scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
}

// 兩個跟全站配色一致的 Monaco 主題
function defineThemes(monaco) {
  monaco.editor.defineTheme('pylp-light', {
    base: 'vs',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '8a919c', fontStyle: 'italic' },
      { token: 'keyword', foreground: '4f46e5' },
      { token: 'string', foreground: '17935a' },
      { token: 'number', foreground: 'b86e00' },
    ],
    colors: {
      'editor.background': '#ffffff',
      'editor.lineHighlightBackground': '#f6f5f1',
      'editorLineNumber.foreground': '#b5b9c1',
      'editorLineNumber.activeForeground': '#545b66',
      'editorIndentGuide.background1': '#ecebe5',
    },
  })
  monaco.editor.defineTheme('pylp-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6e7687', fontStyle: 'italic' },
      { token: 'keyword', foreground: '8f91ff' },
      { token: 'string', foreground: '4cc38a' },
      { token: 'number', foreground: 'e9b350' },
    ],
    colors: {
      'editor.background': '#161920',
      'editor.lineHighlightBackground': '#1b1f27',
      'editorLineNumber.foreground': '#464d5c',
      'editorLineNumber.activeForeground': '#a4abba',
      'editorIndentGuide.background1': '#232833',
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
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  height: 46px;
  padding: 0 10px 0 16px;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.file { display: flex; align-items: center; gap: 8px; color: var(--text-2); min-width: 0; }
.file-name { font-family: var(--font-mono); font-size: 12.5px; font-weight: 500; color: var(--text); }
.lang {
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-soft);
  padding: 1px 8px;
  border-radius: 999px;
}

.actions { display: flex; align-items: center; gap: 8px; }

.ghost {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-2);
  font-size: 12.5px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.ghost:hover { background: var(--surface-3); color: var(--text); }

.monaco-wrap { flex: 1; min-height: 0; }
.monaco-wrap :deep(> div) { height: 100%; }

@media (max-width: 900px) {
  .editor { height: 380px; }
  .toolbar { padding-left: 12px; }
}
</style>
