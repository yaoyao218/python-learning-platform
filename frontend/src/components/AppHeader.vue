<template>
  <header class="topbar">
    <div class="brand">
      <span class="brand-mark" aria-hidden="true">
        <Code2 :size="16" :stroke-width="2.6" />
      </span>
      <span class="brand-text">Python 學習平台</span>
    </div>

    <div class="switcher" v-if="problems.length" ref="switcherEl">
      <button
        class="nav-btn"
        :disabled="index <= 0"
        aria-label="上一題"
        title="上一題"
        @click="$emit('select', problems[index - 1].id)"
      >
        <ChevronLeft :size="16" />
      </button>

      <button
        class="picker"
        :aria-expanded="open"
        aria-haspopup="listbox"
        @click="open = !open"
      >
        <span class="picker-index">{{ index + 1 }}</span>
        <span class="picker-title">{{ current?.title ?? '選擇題目' }}</span>
        <span v-if="current" class="diff-pill" :class="`diff-${current.difficulty}`">{{ diffLabel(current.difficulty) }}</span>
        <ChevronDown :size="15" class="picker-caret" :class="{ flipped: open }" />
      </button>

      <button
        class="nav-btn"
        :disabled="index < 0 || index >= problems.length - 1"
        aria-label="下一題"
        title="下一題"
        @click="$emit('select', problems[index + 1].id)"
      >
        <ChevronRight :size="16" />
      </button>

      <Transition name="pop">
        <ul v-if="open" class="menu" role="listbox">
          <li
            v-for="(p, i) in problems"
            :key="p.id"
            role="option"
            :aria-selected="p.id === currentId"
            :class="['menu-item', { active: p.id === currentId }]"
            @click="choose(p.id)"
          >
            <span class="menu-no">{{ i + 1 }}</span>
            <span class="menu-title">{{ p.title }}</span>
            <span class="diff-pill" :class="`diff-${p.difficulty}`">{{ diffLabel(p.difficulty) }}</span>
            <span class="menu-done" :class="{ on: solved.includes(p.id) }" :title="solved.includes(p.id) ? '已通過' : '尚未通過'">
              <Check :size="13" :stroke-width="3" />
            </span>
          </li>
        </ul>
      </Transition>
    </div>

    <div class="right">
      <span v-if="problems.length" class="progress" :title="`已通過 ${solvedCount} / ${problems.length} 題`">
        <span class="progress-track">
          <span class="progress-fill" :style="{ width: (solvedCount / problems.length) * 100 + '%' }"></span>
        </span>
        <span class="progress-text">{{ solvedCount }}/{{ problems.length }}</span>
      </span>
      <button
        class="icon-btn"
        :aria-label="theme === 'dark' ? '切換成淺色' : '切換成深色'"
        :title="theme === 'dark' ? '切換成淺色' : '切換成深色'"
        @click="$emit('toggle-theme')"
      >
        <Sun v-if="theme === 'dark'" :size="17" />
        <Moon v-else :size="17" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { Code2, ChevronLeft, ChevronRight, ChevronDown, Check, Sun, Moon } from 'lucide-vue-next'

const props = defineProps({
  problems:  { type: Array,  default: () => [] },   // [{ id, title, difficulty }]
  currentId: { type: [String, null], default: null },
  solved:    { type: Array,  default: () => [] },   // 通過過的題目 id
  theme:     { type: String, default: 'light' },
})
const emit = defineEmits(['select', 'toggle-theme'])

const DIFF_LABELS = { easy: '低', medium: '中', hard: '高' }
const diffLabel = (d) => DIFF_LABELS[d] ?? d

const index = computed(() => props.problems.findIndex((p) => p.id === props.currentId))
const current = computed(() => props.problems[index.value] ?? null)
const solvedCount = computed(() => props.problems.filter((p) => props.solved.includes(p.id)).length)

const open = ref(false)
const switcherEl = ref(null)

function choose(id) {
  open.value = false
  if (id !== props.currentId) emit('select', id)
}

function onDocClick(e) {
  if (open.value && switcherEl.value && !switcherEl.value.contains(e.target)) open.value = false
}
function onKey(e) {
  if (e.key === 'Escape') open.value = false
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocClick)
  document.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocClick)
  document.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.topbar {
  height: var(--topbar-h);
  flex-shrink: 0;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 16px;
  padding: 0 20px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: relative;
  z-index: 50;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: 0.01em;
  min-width: 0;
}
.brand-mark {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: var(--accent);
  color: var(--on-accent);
  flex-shrink: 0;
}
.brand-text { white-space: nowrap; }

/* ── 題目切換 ── */
.switcher {
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
  min-width: 0;
}

.nav-btn, .icon-btn {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}
.nav-btn:hover:not(:disabled), .icon-btn:hover { background: var(--surface-3); color: var(--text); }
.nav-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.picker {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 36px;
  min-width: 0;
  max-width: 460px;
  padding: 0 12px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-size: 13.5px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.picker:hover { border-color: var(--border-hi); background: var(--surface-3); }

.picker-index {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
}
.picker-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}
.picker-caret { color: var(--text-3); transition: transform 0.2s var(--ease); flex-shrink: 0; }
.picker-caret.flipped { transform: rotate(180deg); }

.diff-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 999px;
  flex-shrink: 0;
}
.diff-easy   { color: var(--green); background: var(--green-soft); }
.diff-medium { color: var(--amber); background: var(--amber-soft); }
.diff-hard   { color: var(--red);   background: var(--red-soft); }

.menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  width: min(520px, 92vw);
  list-style: none;
  padding: 6px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow), 0 12px 40px rgba(0, 0, 0, 0.12);
  max-height: 70vh;
  overflow-y: auto;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13.5px;
  transition: background 0.12s;
}
.menu-item:hover { background: var(--surface-3); }
.menu-item.active { background: var(--accent-soft); }
.menu-no { font-family: var(--font-mono); font-size: 12px; color: var(--text-3); width: 16px; text-align: right; flex-shrink: 0; }
.menu-title { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.menu-done {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  border: 1.5px solid var(--border-hi);
  color: transparent;
  flex-shrink: 0;
}
.menu-done.on { background: var(--green); border-color: var(--green); color: #fff; }

.pop-enter-active, .pop-leave-active { transition: opacity 0.15s, transform 0.18s var(--ease); }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translate(-50%, -6px); }

/* ── 右側 ── */
.right { display: flex; align-items: center; justify-content: flex-end; gap: 14px; }

.progress { display: flex; align-items: center; gap: 8px; }
.progress-track { width: 72px; height: 6px; border-radius: 999px; background: var(--surface-3); overflow: hidden; }
.progress-fill { display: block; height: 100%; background: var(--green); border-radius: 999px; transition: width 0.5s var(--ease); }
.progress-text { font-family: var(--font-mono); font-size: 12px; color: var(--text-2); }

@media (max-width: 900px) {
  .topbar { grid-template-columns: auto 1fr auto; padding: 0 12px; gap: 8px; }
  .brand-text { display: none; }
  .progress { display: none; }
  .picker { max-width: none; flex: 1; }
  .switcher { min-width: 0; position: static; }
  .menu { left: 12px; transform: none; width: calc(100vw - 24px); }
  .pop-enter-from, .pop-leave-to { transform: translateY(-6px); }
}
</style>
