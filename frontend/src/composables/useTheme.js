import { ref, watchEffect } from 'vue'
import { loadItem, saveItem } from './storage.js'

// index.html 的內嵌腳本已經先設好 data-theme，這裡讀回來當初始值
const initial = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'
const theme = ref(loadItem('pylp:theme', initial))

watchEffect(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
})

export function useTheme() {
  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    saveItem('pylp:theme', theme.value)
  }
  return { theme, toggle }
}
