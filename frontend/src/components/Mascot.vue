<template>
  <svg
    class="mascot"
    :class="`m-${mood}`"
    :width="size"
    :height="size"
    viewBox="0 0 120 120"
    role="img"
    :aria-label="`派派（${MOOD_LABELS[mood]}）`"
  >
    <g class="whole">
      <!-- 尾巴 -->
      <path class="tail" d="M96 100 C112 98 116 84 108 78 C104 75 100 80 103 84"
            fill="none" stroke="var(--ink)" stroke-width="3.2" stroke-linecap="round" />
      <path class="tail-fill" d="M96 100 C112 98 116 84 108 78 C104 75 100 80 103 84"
            fill="none" stroke="var(--snake)" stroke-width="8" stroke-linecap="round" />
      <circle cx="103" cy="84" r="3.4" fill="var(--belly)" stroke="var(--ink)" stroke-width="2" />

      <!-- 盤起來的身體 -->
      <ellipse cx="60" cy="98" rx="44" ry="15" fill="var(--snake)" stroke="var(--ink)" stroke-width="3.2" />
      <path d="M22 99 Q60 112 98 99" fill="none" stroke="var(--belly)" stroke-width="5" stroke-linecap="round" opacity="0.9" />

      <!-- 直立的身體 -->
      <rect x="36" y="52" width="48" height="52" rx="24" fill="var(--snake)" stroke="var(--ink)" stroke-width="3.2" />
      <ellipse cx="60" cy="80" rx="14" ry="22" fill="var(--belly)" />
      <path d="M48 72 H72 M47 80 H73 M48 88 H72" stroke="var(--snake-dark)" stroke-width="1.6" stroke-linecap="round" opacity="0.35" />

      <!-- 頭 -->
      <g class="head">
        <ellipse cx="60" cy="46" rx="33" ry="27" fill="var(--snake)" stroke="var(--ink)" stroke-width="3.2" />
        <circle cx="42" cy="30" r="3.4" fill="var(--snake-dark)" opacity="0.45" />
        <circle cx="52" cy="24" r="2.6" fill="var(--snake-dark)" opacity="0.45" />
        <circle cx="76" cy="28" r="3" fill="var(--snake-dark)" opacity="0.45" />

        <!-- 腮紅 -->
        <ellipse cx="37" cy="54" rx="5.5" ry="3.6" fill="#ff8a8a" opacity="0.7" />
        <ellipse cx="83" cy="54" rx="5.5" ry="3.6" fill="#ff8a8a" opacity="0.7" />

        <!-- 眼睛 -->
        <g v-if="mood === 'sleep'" stroke="var(--ink)" stroke-width="3" stroke-linecap="round" fill="none">
          <path d="M40 46 Q47 51 54 46" />
          <path d="M66 46 Q73 51 80 46" />
        </g>
        <g v-else-if="mood === 'happy'" stroke="var(--ink)" stroke-width="3.2" stroke-linecap="round" fill="none">
          <path d="M40 48 Q47 38 54 48" />
          <path d="M66 48 Q73 38 80 48" />
        </g>
        <g v-else class="eyes">
          <ellipse cx="47" cy="45" rx="7.5" ry="8.5" fill="#fff" stroke="var(--ink)" stroke-width="2.6" />
          <ellipse cx="73" cy="45" rx="7.5" ry="8.5" fill="#fff" stroke="var(--ink)" stroke-width="2.6" />
          <circle class="pupil" :cx="mood === 'think' ? 49 : 47" :cy="mood === 'think' ? 42 : 46" r="3.8" fill="var(--ink)" />
          <circle class="pupil" :cx="mood === 'think' ? 75 : 73" :cy="mood === 'think' ? 42 : 46" r="3.8" fill="var(--ink)" />
          <circle :cx="mood === 'think' ? 50.4 : 48.4" :cy="mood === 'think' ? 40.6 : 44.6" r="1.2" fill="#fff" />
          <circle :cx="mood === 'think' ? 76.4 : 74.4" :cy="mood === 'think' ? 40.6 : 44.6" r="1.2" fill="#fff" />
        </g>

        <!-- 眉毛（難過／思考） -->
        <g v-if="mood === 'sad'" stroke="var(--ink)" stroke-width="2.8" stroke-linecap="round" fill="none">
          <path d="M39 33 L54 37" />
          <path d="M81 33 L66 37" />
        </g>
        <g v-if="mood === 'think'" stroke="var(--ink)" stroke-width="2.8" stroke-linecap="round" fill="none">
          <path d="M40 34 Q47 30 54 34" />
          <path d="M66 32 Q73 28 80 32" />
        </g>

        <!-- 嘴巴 -->
        <path v-if="mood === 'idle' || mood === 'wave'" d="M52 58 Q60 65 68 58" fill="none" stroke="var(--ink)" stroke-width="3" stroke-linecap="round" />
        <g v-else-if="mood === 'happy'">
          <path d="M50 56 Q60 74 70 56 Z" fill="#7a2d3a" stroke="var(--ink)" stroke-width="3" stroke-linejoin="round" />
          <path d="M55 64 Q60 70 65 64 Q60 60 55 64Z" fill="#ff7a8a" />
        </g>
        <path v-else-if="mood === 'sad'" d="M52 63 Q60 55 68 63" fill="none" stroke="var(--ink)" stroke-width="3" stroke-linecap="round" />
        <ellipse v-else-if="mood === 'think'" cx="62" cy="61" rx="3.6" ry="3" fill="#7a2d3a" stroke="var(--ink)" stroke-width="2.4" />
        <path v-else-if="mood === 'sleep'" d="M54 60 Q60 63 66 60" fill="none" stroke="var(--ink)" stroke-width="3" stroke-linecap="round" />

        <!-- 吐舌頭（待機） -->
        <path v-if="mood === 'idle'" class="tongue" d="M60 63 V70 M60 70 L56 74 M60 70 L64 74" fill="none" stroke="#e2475f" stroke-width="2.4" stroke-linecap="round" />

        <!-- 淚滴 -->
        <path v-if="mood === 'sad'" class="tear" d="M84 52 Q88 58 84 62 Q80 58 84 52Z" fill="#8fd3ff" stroke="var(--ink)" stroke-width="1.6" />
      </g>

      <!-- 揮手 -->
      <g v-if="mood === 'wave'" class="hand">
        <circle cx="94" cy="62" r="7" fill="var(--snake)" stroke="var(--ink)" stroke-width="3" />
      </g>
    </g>

    <!-- 思考的泡泡 / 睡覺的 Z -->
    <g v-if="mood === 'think'" class="dots-think" fill="var(--ink)">
      <circle cx="96" cy="22" r="3" /><circle cx="106" cy="14" r="3.6" /><circle cx="117" cy="8" r="4.2" />
    </g>
    <g v-if="mood === 'sleep'" class="zzz" fill="var(--ink)" font-family="var(--font-display)" font-weight="700">
      <text x="92" y="26" font-size="14">z</text>
      <text x="102" y="14" font-size="11">z</text>
    </g>
  </svg>
</template>

<script setup>
// 吉祥物「派派」：Python 配色的小蛇。mood 決定表情與動作。
defineProps({
  mood: { type: String, default: 'idle' },   // idle | wave | think | happy | sad | sleep
  size: { type: Number, default: 96 },
})

const MOOD_LABELS = {
  idle: '待機', wave: '打招呼', think: '思考中', happy: '開心', sad: '加油', sleep: '睡覺',
}
</script>

<style scoped>
.mascot {
  --snake: #4b8bbe;
  --snake-dark: #306998;
  --belly: #ffd43b;
  display: block;
  overflow: visible;
  flex-shrink: 0;
}

.whole { transform-origin: 60px 104px; animation: bob 3.4s ease-in-out infinite; }
@keyframes bob {
  0%, 100% { transform: translateY(0) scale(1, 1); }
  50% { transform: translateY(-2px) scale(1.01, 0.985); }
}

.eyes { transform-origin: 60px 45px; animation: blink 4.5s infinite; }
@keyframes blink {
  0%, 94%, 100% { transform: scaleY(1); }
  97% { transform: scaleY(0.1); }
}

.tongue { transform-origin: 60px 63px; animation: flick 3.4s ease-in-out infinite; }
@keyframes flick {
  0%, 70%, 100% { transform: scaleY(0); }
  78%, 90% { transform: scaleY(1); }
}

.m-happy .whole { animation: hop 0.7s var(--ease) 3; }
@keyframes hop {
  0%, 100% { transform: translateY(0) scale(1, 1); }
  35% { transform: translateY(-14px) scale(0.97, 1.05); }
  70% { transform: translateY(0) scale(1.05, 0.94); }
}

.m-sad .head { transform-origin: 60px 60px; animation: droop 2.8s ease-in-out infinite; }
@keyframes droop {
  0%, 100% { transform: rotate(-2deg); }
  50% { transform: rotate(2deg) translateY(1px); }
}
.tear { animation: tear 2.4s ease-in infinite; }
@keyframes tear {
  0%, 20% { opacity: 0; transform: translateY(-4px); }
  45% { opacity: 1; }
  100% { opacity: 0; transform: translateY(12px); }
}

.m-think .head { transform-origin: 60px 60px; animation: tilt 1.8s ease-in-out infinite; }
@keyframes tilt {
  0%, 100% { transform: rotate(-3deg); }
  50% { transform: rotate(3deg); }
}
.dots-think circle { animation: pop 1.4s ease-in-out infinite; }
.dots-think circle:nth-child(2) { animation-delay: 0.2s; }
.dots-think circle:nth-child(3) { animation-delay: 0.4s; }
@keyframes pop { 0%, 100% { opacity: 0.25; } 50% { opacity: 1; } }

.m-sleep .whole { animation: breathe 3.2s ease-in-out infinite; }
@keyframes breathe {
  0%, 100% { transform: scale(1, 1); }
  50% { transform: scale(1.02, 1.03); }
}
.zzz { animation: float-z 2.6s ease-in-out infinite; }
@keyframes float-z {
  0%, 100% { opacity: 0.4; transform: translateY(2px); }
  50% { opacity: 1; transform: translateY(-3px); }
}

.hand { transform-origin: 90px 74px; animation: wave 0.9s ease-in-out infinite; }
@keyframes wave {
  0%, 100% { transform: rotate(-12deg); }
  50% { transform: rotate(22deg); }
}
</style>
