// 把判題結果翻成新手看得懂的話，並決定派派這一刻的表情與台詞。
// 純函式、不碰後端，只讀 /submit 回傳的 results。

const clip = (v, n = 60) => {
  const s = String(v)
  return s.length > n ? s.slice(0, n) + '…' : s
}

export function summarize({ results, loading }) {
  if (loading) {
    return { mood: 'think', say: '我正在跑你的程式，等我一下下…' }
  }
  if (!results.length) {
    return { mood: 'idle', say: '寫好之後按「提交」，我幫你檢查所有測資！' }
  }

  const passCount = results.filter((r) => r.passed).length
  if (passCount === results.length) {
    return { mood: 'happy', say: `全部通過！${results.length} 個測資一個都沒漏，你超強的！` }
  }

  const fail = results.find((r) => !r.passed)
  const near = passCount / results.length >= 0.6
  const lead = near ? '快成功了！' : '沒關係，一起來看看。'

  switch (fail.error_type) {
    case 'syntax_error':
      return { mood: 'sad', say: `${lead}程式有語法錯誤，所以還跑不起來。看下面紅色訊息，它會告訴你是哪一行。` }
    case 'runtime_error':
      return { mood: 'sad', say: `${lead}程式跑到一半出錯了（第 ${fail.index} 筆測資）。想想看這個輸入有什麼特別的地方？` }
    case 'timeout':
      return { mood: 'sad', say: `${lead}程式跑太久了。是不是有迴圈出不來，或是重複做了很多事？` }
    case 'no_return':
      return { mood: 'sad', say: `${lead}函式跑完沒有回傳東西。記得用 return 把答案交出來喔。` }
    default:
      return { mood: 'sad', say: `${lead}第 ${fail.index} 筆測資答案不一樣，看下面的對照。` }
  }
}

// 第一個沒過的測資：白話對照（給「哪裡不對」卡片用）
export function describeFirstFail(results) {
  const fail = results.find((r) => !r.passed)
  if (!fail) return null
  return {
    index: fail.index,
    input: clip(fail.input),
    expected: clip(fail.expected),
    // 有錯誤類型時沒有 actual，交給錯誤訊息區顯示
    actual: fail.error_type ? null : clip(fail.actual ?? ''),
    hasError: !!fail.error_type,
  }
}
