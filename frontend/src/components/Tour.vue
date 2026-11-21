<template>
  <Transition name="fade">
    <div v-if="open" class="backdrop" @click.self="close">
      <div class="dialog" role="dialog" aria-modal="true" aria-label="新手導覽">
        <button class="skip" @click="close">跳過</button>

        <div class="stage">
          <Mascot :mood="step.mood" :size="130" />
        </div>

        <Transition name="slide" mode="out-in">
          <div :key="i" class="text">
            <h2>{{ step.title }}</h2>
            <p v-for="(line, k) in step.lines" :key="k" v-html="line"></p>
          </div>
        </Transition>

        <div class="foot">
          <div class="dots">
            <i v-for="(_, n) in steps" :key="n" :class="{ on: n === i }"></i>
          </div>
          <div class="btns">
            <button v-if="i > 0" class="back" @click="i--">上一步</button>
            <button class="btn-sticker" @click="next">{{ i === steps.length - 1 ? '開始練習' : '下一步' }}</button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import Mascot from './Mascot.vue'

const props = defineProps({ open: { type: Boolean, default: false } })
const emit = defineEmits(['close'])

const steps = [
  {
    mood: 'wave',
    title: '嗨，我是派派！',
    lines: [
      '接下來我會陪你一題一題練 Python。',
      '寫錯了不用怕，我會一步一步帶你找到問題。',
    ],
  },
  {
    mood: 'idle',
    title: '左邊看題目，右邊寫程式',
    lines: [
      '程式只要寫在 <code>def</code> 裡面，最後別忘了用 <code>return</code> 把答案交出來。',
      '<code>class Solution</code> 和 <code>self</code> 先照抄就好，不用現在搞懂。',
    ],
  },
  {
    mood: 'think',
    title: '寫好就按「提交」',
    lines: [
      '我會用很多組測資幫你檢查，沒過的話告訴你是哪一組、差在哪。',
      '連續錯 3 次，我會給你一份「填空小抄」。真的卡住，左邊還有「虛擬碼」可以看。',
    ],
  },
  {
    mood: 'happy',
    title: '準備好了嗎？',
    lines: [
      '每過一關就會亮起一顆星，連續幾天練習我也會幫你記著。',
      '右上角的 <b>？</b> 隨時可以再看一次這個導覽。',
    ],
  },
]

const i = ref(0)
const step = computed(() => steps[i.value])
watch(() => props.open, (v) => { if (v) i.value = 0 })

function next() {
  if (i.value < steps.length - 1) i.value++
  else close()
}
function close() { emit('close') }
</script>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 150;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(20, 20, 30, 0.55);
}

.dialog {
  position: relative;
  width: min(460px, 100%);
  padding: 22px 26px 22px;
  background: var(--surface);
  border: var(--bw) solid var(--ink);
  border-radius: var(--radius-lg);
  box-shadow: 6px 6px 0 var(--ink);
  animation: pop 0.4s var(--spring) both;
}
@keyframes pop { from { opacity: 0; transform: translateY(14px) scale(0.96); } to { opacity: 1; transform: none; } }

.skip {
  position: absolute;
  top: 14px;
  right: 16px;
  border: none;
  background: none;
  color: var(--text-3);
  font-size: 13px;
  cursor: pointer;
}
.skip:hover { color: var(--text); }

.stage { display: grid; place-items: center; height: 140px; }

.text { min-height: 150px; text-align: center; }
.text h2 { font-family: var(--font-display); font-weight: 400; font-size: 22px; margin: 6px 0 12px; }
.text p { font-size: 14.5px; line-height: 1.85; color: var(--text-2); }
.text p + p { margin-top: 6px; }

.foot { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; }
.dots { display: flex; gap: 7px; }
.dots i { width: 9px; height: 9px; border-radius: 50%; border: 1.5px solid var(--ink); background: var(--surface-3); transition: all 0.2s var(--ease); }
.dots i.on { background: var(--sun); width: 24px; border-radius: 6px; }
.btns { display: flex; align-items: center; gap: 12px; }
.back { border: none; background: none; color: var(--text-2); font-size: 13.5px; cursor: pointer; }
.back:hover { color: var(--text); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-enter-active, .slide-leave-active { transition: opacity 0.15s, transform 0.2s var(--ease); }
.slide-enter-from { opacity: 0; transform: translateX(14px); }
.slide-leave-to { opacity: 0; transform: translateX(-14px); }
</style>
