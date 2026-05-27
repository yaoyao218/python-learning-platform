# Project Audit — Design Spec
**Date:** 2026-05-28  
**Branch:** Auxe  
**Scope:** 方案 B — 內容 Bug 修正 + 學習體驗補強

---

## 目標

1. 修正所有跨檔案內容不一致（數字、拼字、舊 URL、殘留程式碼）
2. 補上學習體驗缺口（全部通過回饋、題目 Constraints）
3. 確認 pytest 全綠、流程 end-to-end 可動

---

## 修改清單（7 項）

### Bug 修正

| # | 檔案 | 行號 | 問題 | 修法 |
|---|------|------|------|------|
| 1 | `backend/judge.py` | L35, L39 | docstring 寫「18 組」「18 筆」 | 改為「17 組」「17 筆」 |
| 2 | `backend/ai.py` | L109 | 「呼叫 Grok API」（Grok 是 X/Twitter 的 AI） | 改為「呼叫 Groq/Gemini API」 |
| 3 | `backend/ai.py` | L21 | docstring「三種 prompt 分支」與 CLAUDE.md「4 個分支」不一致 | 改為「4 種 error_type，對應 3 個 prompt 分支」 |
| 4 | `backend/main.py` | L5-6 | 設 WindowsProactorEventLoopPolicy，但 ThreadPoolExecutor 方案已不需要 | 移除這兩行 |
| 5 | `README.md` | L189-190 | 部署 URL 是舊的（`-one.vercel.app` / `-quf0.onrender.com`） | 更新為正確 URL（`-chi.vercel.app` / `-88vh.onrender.com`） |

### 學習體驗補強

| # | 檔案 | 功能 | 設計細節 |
|---|------|------|---------|
| 6 | `frontend/src/components/ResultPanel.vue` | 全部通過成功訊息 | 當 `passCount === results.length && results.length > 0` 且 `hint` 為 null，顯示綠色成功卡，文字：「✓ 全部通過！⋯太棒了！你的解法通過了所有 17 個測試案例。試試看能不能讓解法更有效率？」 |
| 7 | `frontend/src/App.vue` + `frontend/src/components/ProblemStatement.vue` | 題目 Constraints | 在 `problem` 物件加 `constraints` 欄位；`ProblemStatement.vue` 在範例卡片下方渲染。內容：`0 ≤ s.length ≤ 5 × 10⁴`、`s` 只包含英文字母、數字、符號與空白字元 |

---

## 架構與影響範圍

- 所有修改皆為獨立改動，不互相依賴
- 後端改動（#1-4）：純文字/docstring，不影響邏輯
- 前端改動（#6-7）：新增 UI 元素，不改動 API 合約
- 不新增測試（現有 pytest 全過即可）

---

## 驗證步驟

1. `cd backend && pytest -v` → 全綠
2. 啟動後端 + 前端，提交正確解 → 看到成功訊息
3. 提交空白 `pass` → 看到 AI 提示
4. 確認 README.md 連結點開正確

---

## 確認正確的項目（不需修改）

- **論文引用**：`CodeContests-O: Powering LLMs via Feedback-Driven Iterative Test Case Generation` — 已確認正確，三個引用位置（README.md、CLAUDE.md、testgen/PROGRESS.md）不需修改

---

## 不在範圍內

- 新增題目
- 修改 AI prompt 邏輯
- 修改測資集
- 新增後端 endpoint
