<template>
  <header class="topbar">
    <div class="brand">
      <Mascot :mood="'idle'" :size="46" class="brand-mascot" />
      <div class="brand-text">
        <span class="brand-name">Python 學習平台</span>
        <span class="brand-sub">跟派派一起練</span>
      </div>
    </div>

    <div class="switcher" v-if="problems.length" ref="switcherEl">
      <button
        class="nav-btn"
        :disabled="index <= 0"
        aria-label="上一關"
        title="上一關"
        @click="$emit('select', problems[index - 1].id)"
      >
        <ChevronLeft :size="18" :stroke-width="2.6" />
      </button>

      <button class="picker" :aria-expanded="open" aria-haspopup="listbox" @click="open = !open">
        <span class="stage-no">第 {{ index + 1 }} 關</span>
        <span class="picker-title">{{ current?.title ?? '選擇題目' }}</span>
        <ChevronDown :size="16" :stroke-width="2.6" class="caret" :class="{ flipped: open }" />
      </button>

      <button
        class="nav-btn"
        :disabled="index < 0 || index >= problems.length - 1"
        aria-label="下一關"
        title="下一關"
        @click="$emit('select', problems[index + 1].id)"
      >
        <ChevronRight :size="18" :stroke-width="2.6" />
      </button>

      <Transition name="pop">
        <div v-if="open" class="menu" role="listbox">
          <div class="menu-title">選一關</div>
          <ul>
            <li
              v-for="(p, i) in problems"
              :key="p.id"
              role="option"
              :aria-selected="p.id === currentId"
              :class="['menu-item', { active: p.id === currentId, done: solved.includes(p.id) }]"
              @click="choose(p.id)"
            >
              <span class="node">{{ solved.includes(p.id) ? '★' : i + 1 }}</span>
              <span class="menu-name">{{ p.title }}</span>
              <span class="level" :class="`lv-${p.difficulty}`" :title="`難度 ${diffLabel(p.difficulty)}`">
                <i v-for="n in 3" :key="n" :class="{ on: n <= diffNum(p.difficulty) }"></i>
              </span>
            </li>
          </ul>
        </div>
      </Transition>
    </div>

    <div class="right">
      <span class="chip" :class="{ cold: !streak }" :title="streak ? `已連續練習 ${streak} 天` : '今天練一題，就開始累積連續天數'">
        <svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true">
          <path d="M12 2c1 4-2 5-2 8 0 1.5 1 2.5 2 2.5 0-2 2-3 3-5 3 2 5 5 5 8a8 8 0 0 1-16 0c0-3 2-5 3-7 1 1 1 2 1.5 2.5C9 8 11 6 12 2z"
                fill="currentColor" stroke="var(--ink)" stroke-width="1.6" stroke-linejoin="round" />
        </svg>
        <b>{{ streak }}</b><span class="chip-unit">天</span>
      </span>

      <span class="chip stars" :title="`已過 ${solvedCount} / ${problems.length} 關`">
        <span class="star">★</span><b>{{ solvedCount }}</b><span class="chip-unit">/ {{ problems.length }}</span>
      </span>

      <button class="icon-btn" aria-label="新手導覽" title="新手導覽" @click="$emit('help')">?</button>
      <button
        class="icon-btn"
        :aria-label="theme === 'dark' ? '切換成淺色' : '切換成深色'"
        :title="theme === 'dark' ? '切換成淺色' : '切換成深色'"
        @click="$emit('toggle-theme')"
      >
        <Sun v-if="theme === 'dark'" :size="17" :stroke-width="2.4" />
        <Moon v-else :size="17" :stroke-width="2.4" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { ChevronLeft, ChevronRight, ChevronDown, Sun, Moon } from 'lucide-vue-next'
import Mascot from './Mascot.vue'

const props = defineProps({
  problems:  { type: Array,  default: () => [] },   // [{ id, title, difficulty }]
  currentId: { type: [String, null], default: null },
  solved:    { type: Array,  default: () => [] },   // 通過過的題目 id
  theme:     { type: String, default: 'light' },
  streak:    { type: Number, default: 0 },
})
const emit = defineEmits(['select', 'toggle-theme', 'help'])

const DIFF_LABELS = { easy: '低', medium: '中', hard: '高' }
const DIFF_NUM = { easy: 1, medium: 2, hard: 3 }
const diffLabel = (d) => DIFF_LABELS[d] ?? d
const diffNum = (d) => DIFF_NUM[d] ?? 1

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
  border-bottom: var(--bw) solid var(--ink);
  position: relative;
  z-index: 50;
}

.brand { display: flex; align-items: center; gap: 8px; min-width: 0; }
.brand-mascot { margin-top: 6px; }
.brand-text { display: flex; flex-direction: column; line-height: 1.2; min-width: 0; }
.brand-name { font-family: var(--font-display); font-size: 17px; white-space: nowrap; }
.brand-sub { font-size: 11.5px; color: var(--text-3); white-space: nowrap; }

/* 關卡切換 */
.switcher { display: flex; align-items: center; gap: 8px; position: relative; min-width: 0; }

.nav-btn, .icon-btn {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border: var(--bw) solid var(--ink);
  border-radius: 10px;
  background: var(--surface);
  color: var(--text);
  font-family: var(--font-display);
  font-size: 16px;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: transform 0.12s var(--ease), box-shadow 0.12s var(--ease), background 0.15s;
  flex-shrink: 0;
}
.nav-btn:hover:not(:disabled), .icon-btn:hover { background: var(--sun); color: var(--on-sun); transform: translate(-1px, -1px); box-shadow: 3px 3px 0 var(--ink); }
.nav-btn:active:not(:disabled), .icon-btn:active { transform: translate(2px, 2px); box-shadow: none; }
.nav-btn:disabled { opacity: 0.35; cursor: not-allowed; box-shadow: none; }

.picker {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 40px;
  min-width: 0;
  max-width: 440px;
  padding: 0 14px;
  background: var(--surface-2);
  border: var(--bw) solid var(--ink);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  color: var(--text);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.12s var(--ease), box-shadow 0.12s var(--ease);
}
.picker:hover { transform: translate(-1px, -1px); box-shadow: 3px 3px 0 var(--ink); }
.stage-no {
  font-family: var(--font-display);
  font-size: 13px;
  padding: 1px 9px;
  background: var(--sun);
  color: var(--on-sun);
  border: 1.5px solid var(--ink);
  border-radius: 8px;
  white-space: nowrap;
}
.picker-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
.caret { flex-shrink: 0; transition: transform 0.2s var(--ease); }
.caret.flipped { transform: rotate(180deg); }

.menu {
  position: absolute;
  top: calc(100% + 12px);
  left: 50%;
  transform: translateX(-50%);
  width: min(500px, 92vw);
  background: var(--surface);
  border: var(--bw) solid var(--ink);
  border-radius: var(--radius-lg);
  box-shadow: 5px 5px 0 var(--ink);
  overflow: hidden;
}
.menu-title {
  padding: 10px 16px;
  background: var(--surface-2);
  border-bottom: var(--bw) solid var(--ink);
  font-family: var(--font-display);
  font-size: 14px;
}
.menu ul { list-style: none; padding: 8px; max-height: 66vh; overflow-y: auto; }
.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 10px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.12s;
}
.menu-item:hover { background: var(--surface-2); }
.menu-item.active { background: var(--blue-soft); }
.node {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border: var(--bw) solid var(--ink);
  border-radius: 50%;
  background: var(--surface);
  font-family: var(--font-display);
  font-size: 14px;
  flex-shrink: 0;
}
.menu-item.done .node { background: var(--sun); color: var(--on-sun); }
.menu-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.level { display: flex; gap: 3px; flex-shrink: 0; }
.level i { width: 8px; height: 14px; border: 1.5px solid var(--ink); border-radius: 3px; background: var(--surface-3); }
.level.lv-easy i.on   { background: var(--green); }
.level.lv-medium i.on { background: var(--sun); }
.level.lv-hard i.on   { background: var(--red); }

.pop-enter-active, .pop-leave-active { transition: opacity 0.15s, transform 0.22s var(--spring); }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translate(-50%, -8px) scale(0.97); }

/* 右側 */
.right { display: flex; align-items: center; justify-content: flex-end; gap: 10px; }

.chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 34px;
  padding: 0 11px;
  border: var(--bw) solid var(--ink);
  border-radius: 10px;
  background: var(--amber-soft);
  color: #e8590c;
  font-size: 14px;
  box-shadow: var(--shadow-sm);
}
.chip b { font-family: var(--font-display); font-weight: 400; font-size: 16px; color: var(--text); }
.chip-unit { font-size: 12px; color: var(--text-2); }
.chip.cold { color: var(--text-3); background: var(--surface-2); }
.chip.stars .star { color: #f5a300; font-size: 16px; -webkit-text-stroke: 1.2px var(--ink); }
.chip.stars { background: var(--surface-2); }

@media (max-width: 1100px) {
  .brand-sub { display: none; }
  .chip-unit { display: none; }
}

@media (max-width: 900px) {
  .topbar { grid-template-columns: auto 1fr auto; padding: 0 10px; gap: 8px; height: 58px; }
  .brand-text { display: none; }
  .brand-mascot { margin-top: 4px; }
  .chip { display: none; }
  .picker { max-width: none; flex: 1; padding: 0 10px; }
  .stage-no { display: none; }
  .switcher { position: static; min-width: 0; }
  .menu { left: 10px; transform: none; width: calc(100vw - 20px); }
  .pop-enter-from, .pop-leave-to { transform: translateY(-8px); }
  .icon-btn[title='新手導覽'] { display: none; }
}
</style>
