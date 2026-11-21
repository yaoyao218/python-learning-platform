import { ref, computed } from 'vue'
import { loadItem, saveItem } from './storage.js'

// 「有練習的日子」：每天第一次提交就記一天。只存日期字串，連續天數由日期算出來。
const days = ref(loadItem('pylp:days', []))

function dayKey(d = new Date()) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

// 從今天（或昨天，今天還沒練也不算斷）往回數連續幾天
const streak = computed(() => {
  const set = new Set(days.value)
  const cursor = new Date()
  if (!set.has(dayKey(cursor))) cursor.setDate(cursor.getDate() - 1)
  let n = 0
  while (set.has(dayKey(cursor))) {
    n++
    cursor.setDate(cursor.getDate() - 1)
  }
  return n
})

export function useStats() {
  function markToday() {
    const k = dayKey()
    if (days.value.includes(k)) return
    // 只留最近 400 天，避免無限增長
    days.value = [...days.value, k].slice(-400)
    saveItem('pylp:days', days.value)
  }
  return { streak, markToday }
}
