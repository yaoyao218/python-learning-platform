// localStorage 在無痕視窗或被封鎖時會丟例外，這裡一律包起來，讀不到就當作沒有。

export function loadItem(key, fallback = null) {
  try {
    const raw = localStorage.getItem(key)
    return raw === null ? fallback : JSON.parse(raw)
  } catch {
    return fallback
  }
}

export function saveItem(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* 存不了就算了，不影響使用 */
  }
}

export function removeItem(key) {
  try {
    localStorage.removeItem(key)
  } catch {
    /* ignore */
  }
}
