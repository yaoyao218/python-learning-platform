<template>
  <div v-if="show" class="confetti" aria-hidden="true">
    <i
      v-for="p in pieces"
      :key="p.id"
      :style="{
        left: p.x + '%',
        background: p.color,
        width: p.w + 'px',
        height: p.h + 'px',
        borderRadius: p.round ? '50%' : '2px',
        animationDelay: p.delay + 's',
        animationDuration: p.dur + 's',
        '--drift': p.drift + 'px',
        '--spin': p.spin + 'deg',
      }"
    ></i>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

// 每次 fire 數字增加就噴一次紙花，約 2.6 秒後自己消失
const props = defineProps({ fire: { type: Number, default: 0 } })

const COLORS = ['#ffd43b', '#4b8bbe', '#ff7a7a', '#5fd3a0', '#ffffff', '#ff9f43']
const show = ref(false)
const pieces = ref([])
let timer = null

watch(() => props.fire, (n) => {
  if (!n) return
  pieces.value = Array.from({ length: 44 }, (_, i) => ({
    id: n * 100 + i,
    x: 5 + Math.random() * 90,
    w: 6 + Math.random() * 6,
    h: 8 + Math.random() * 8,
    round: Math.random() > 0.65,
    color: COLORS[Math.floor(Math.random() * COLORS.length)],
    delay: Math.random() * 0.45,
    dur: 1.6 + Math.random() * 1.1,
    drift: -80 + Math.random() * 160,
    spin: 180 + Math.random() * 540,
  }))
  show.value = true
  clearTimeout(timer)
  timer = setTimeout(() => { show.value = false }, 2800)
})
</script>

<style scoped>
.confetti {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 200;
}
.confetti i {
  position: absolute;
  top: -20px;
  border: 1.5px solid var(--ink);
  animation: fall linear forwards;
}
@keyframes fall {
  0%   { transform: translate(0, 0) rotate(0); opacity: 1; }
  85%  { opacity: 1; }
  100% { transform: translate(var(--drift), 105vh) rotate(var(--spin)); opacity: 0; }
}
</style>
