// AI 寫的文字（虛擬碼、提示）只轉換少數幾種標記；一律先跳脫 HTML，再轉換，避免注入。
//   ```程式碼區塊```  → <pre><code>
//   **粗體**         → <strong>
//   `行內程式`        → <code>

export function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;')
}

function inline(text) {
  return text
    .replace(/`([^`\n]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
}

export function renderLite(text) {
  if (!text) return ''
  // 依 ``` 切開：奇數段是程式碼區塊（第一行可能是語言標記），偶數段是一般文字
  return text.split('```').map((part, i) => {
    if (i % 2 === 0) return inline(escapeHtml(part))
    const body = part.replace(/^[A-Za-z0-9_+-]*\n/, '').replace(/\n$/, '')
    return `<pre class="md-code"><code>${escapeHtml(body)}</code></pre>`
  }).join('')
}
