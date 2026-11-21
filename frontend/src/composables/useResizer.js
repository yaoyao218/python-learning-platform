import { ref, onBeforeUnmount } from 'vue'
import { loadItem, saveItem } from './storage.js'

/**
 * 可拖曳的分隔線。
 *  - axis: 'x' 量水平位移（調左欄寬度）；'y' 量垂直位移（調下方面板高度）
 *  - invert: 往右／下拖是縮小（例如調「下方面板」高度，往下拖它變矮）
 */
export function useResizer({ key, initial, min, max, axis = 'x', invert = false }) {
  const size = ref(Math.min(Math.max(loadItem(key, initial), min), max()))
  const dragging = ref(false)

  let startPos = 0
  let startSize = 0

  function clamp(v) {
    return Math.min(Math.max(v, min), max())
  }

  function onMove(e) {
    const pos = axis === 'x' ? e.clientX : e.clientY
    const delta = (pos - startPos) * (invert ? -1 : 1)
    size.value = clamp(startSize + delta)
  }

  function stop() {
    dragging.value = false
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', stop)
    window.removeEventListener('pointercancel', stop)
    document.body.style.userSelect = ''
    document.body.style.cursor = ''
    saveItem(key, size.value)
  }

  function start(e) {
    startPos = axis === 'x' ? e.clientX : e.clientY
    startSize = size.value
    dragging.value = true
    document.body.style.userSelect = 'none'
    document.body.style.cursor = axis === 'x' ? 'col-resize' : 'row-resize'
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', stop)
    window.addEventListener('pointercancel', stop)
  }

  // 鍵盤也能調：方向鍵每次 24px
  function nudge(step) {
    size.value = clamp(size.value + step)
    saveItem(key, size.value)
  }

  function reset() {
    size.value = clamp(initial)
    saveItem(key, size.value)
  }

  onBeforeUnmount(stop)

  return { size, dragging, start, nudge, reset }
}
