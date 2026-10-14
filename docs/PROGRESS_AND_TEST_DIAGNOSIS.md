# Python 學習平台 — 程式進度與測試階段診斷

> 產生時間：2026-09-11　基準 commit：`022e21e`（main，與 origin/main 完全同步，無分岔）

---

## 1. 專案現況總覽

給大一學生的 LeetCode 風格 Python 練習平台。學生提交程式碼後，後端執行測資並由 code-blind AI（完全不讀學生程式碼）給引導式提示。核心研究貢獻是 Feedback-Driven 測資生成方法論（TPR/TNR 量化指標 + 閉環迭代），目前已從單題目擴充為多題目架構。

| 項目 | 內容 |
|---|---|
| 後端 | FastAPI（`main.py`／`judge.py`／`executor.py`／`ai.py`／`problem.py`） |
| 前端 | Vue 3 + Vite + Monaco Editor |
| 部署 | 後端 Render、前端 Vercel，`git push` 自動觸發 |
| GitHub | github.com/yaoyao218/python-learning-platform |
| 題目 | 3 題：Longest Substring（中）、Valid Parentheses（低）、Median of Two Sorted Arrays（高） |

---

## 2. 目前功能

### 2.1 多題目架構（本次開發主軸）

- `executor.run_code(code, method, args)`：通用化，不再寫死呼叫 `lengthOfLongestSubstring`
- `judge.judge(code, problem_id)`：依 `problem_id` 從 `problem.PROBLEMS` 路由到對應題目的 test_cases
- `judge.compare(actual, expected)`：新增浮點容錯比對（學生回傳 `int` 而非 `float` 仍判 PASS）
- `main.py`：新增 `GET /problems`（列表）、`GET /problems/{id}`（詳情），`POST /submit` 改吃 `problem_id`
- 前端：topbar 題目下拉選單、難度色標（低綠／中黃／高紅）、限制條件顯示

### 2.2 Code-Blind AI 提示系統

- `ai.build_prompt(results, problem_title, problem_context)` / `ai.get_hint(...)`：**完全不接收學生程式碼**，只看測試結果（input/expected/actual）
- 4 種錯誤類型分支（syntax_error / runtime_error / no_return / wrong_answer），wrong_answer 分支明確要求「不要給出正確程式碼或完整演算法步驟」且「結尾必須是問句」（蘇格拉底式引導）
- 模型：Groq `openai/gpt-oss-20b`（原本的 `llama-3.1-8b-instant` 已下架，本次修復）／ Gemini `gemini-2.0-flash` 備援

### 2.3 測資生成方法論（testgen/，離線工具，跟線上服務解耦）

- `gen.py`：12 個生成 mode（含 `doubled_distinct`、`carry_kill`、`combo_kill` 三個 killer mode）
- `run_eval.py` / `smoke_test.py` / `verify_hints.py` / `play.py`：已同步更新至新的 `run_code(code, method, args)` 簽名與 problem_id 路由

---

## 3. 自動化測試現況（2026-09-11 重新驗證）

### 3.1 Pytest — 41/41 全綠

```
tests/test_ai.py .................... 10 passed
tests/test_executor.py .............. 8 passed
tests/test_judge.py .................. 6 passed
tests/test_main.py ................... 6 passed
tests/test_new_problems.py ........... 7 passed
tests/test_problem_quality.py ........ 4 passed
======================= 41 passed in 25.45s =======================
```

### 3.2 Smoke Test（`testgen.smoke_test`）— 5/5 全通過

| 預檢 | 結果 |
|---|---|
| 核心模組 import | ✓ |
| problem.py schema 檢查 | ✓ |
| Reference 正解全過（17/17） | ✓ |
| 6 個錯誤解法皆被攔下 | ✓ |
| `ai.build_prompt` 4 種分支皆能組出 prompt | ✓ |

> 注意：這支腳本在 Windows 終端機用非 UTF-8 codepage 執行會因為 ✓/✗ 符號噴 `UnicodeEncodeError`——這是終端機編碼問題，不是程式碼 bug，用 `PYTHONUTF8=1` 執行即正常。

### 3.3 測資品質守門員（TPR / TNR，僅 Longest Substring）

```
TPR = 1.0000   TNR = 0.8824   測資數 = 17   S+ = 3   S- = 6
```

守門員（`test_problem_quality.py`）4 項斷言全過，且已驗證邏輯正確：拿舊版 baseline（TNR=0.49）跑會正確 FAIL，拿現版會正確 PASS。

### 3.4 手動瀏覽器驗證（上次 session 完成）

三題切換、狀態重置、AI 提示、進度條/成功訊息 UI 皆實測通過；壓力測試（Median 1000+1000 元素、Parentheses 2000 字元）正常無 timeout。

### 3.5 線上部署健康檢查（本次新做）

| 端點 | 狀態 |
|---|---|
| Render 後端 `GET /problems` | ✓ 200，回傳正確 3 題（首次請求因免費方案冷啟動逾時，重試後正常） |
| Render 後端 `POST /submit`（Valid Parentheses） | ✓ 200，判題邏輯正確 |
| Vercel 前端首頁 | ✓ 200 |

未做：對正式環境前端跑完整瀏覽器互動測試（下拉選單、AI 提示渲染），僅驗證本機 dev 環境與正式環境後端 API。

---

## 4. 測試階段診斷

### 4.1 已驗證、可信賴的部分

- 三題判題邏輯（含精心設計會在指定 index 觸發的 bug 測資）✓
- Code-blind AI 提示不會洩漏學生程式碼（結構性保證，非僅靠 prompt 約束）✓
- 浮點容錯比對、多參數呼叫（`executor.run_code` 通用化）✓
- Pytest 品質守門員能正確區分「好測資」與「退化測資」✓
- CI/CD（push → Vercel/Render 自動部署）確認可用 ✓

### 4.2 已知風險與缺口

| # | 問題 | 嚴重度 | 說明 |
|---|---|---|---|
| 1 | 新兩題（Valid Parentheses、Median）沒有 TPR/TNR 收斂 | 中 | 測資是手動設計，已驗證能精準抓到指定 bug，但沒有像 Longest Substring 一樣建立 S+/S- 解池跑論文方法量化鑑別度。`testgen/solutions_wrong/` 目前只有 Longest Substring 的 6 個 bug pattern。 |
| 2 | AI 提示品質沒有回歸測試 | 中 | `testgen/verify_hints.py` 存在但只覆蓋 `longest-substring`（因為只有它有 S- 池可跑）；提示品質目前靠人工在瀏覽器裡逐一檢查，沒有自動化斷言（例如「輸出不得包含程式碼區塊」）。 |
| 3 | 與隨機 Fuzzing 的量化對照未實測 | 低 | 目前只有方法論上的論證（pattern 定向生成 vs 隨機字串命中率低），沒有真的跑一次 fuzzing baseline 量出數字。 |
| 4 | 正式環境前端沒有做過完整互動測試 | 低 | 本次只驗證了 Render 後端 API 存活，沒有對 Vercel 正式站做瀏覽器層級的下拉選單/AI 提示渲染驗證。 |
| 5 | Render 免費方案冷啟動 | 低（已知限制，非 bug） | 閒置 15 分鐘後首次請求會逾時，前端目前**沒有**冷啟動提示訊息（code-blind 重構時被移除了），axios timeout 設 60 秒，理論上重試/等待內會成功，但沒有 UX 提示可能讓使用者誤以為壞掉。 |

### 4.3 一個需要澄清的地方（跟先前簡報的落差）

上一版簡報（`docs/`）的「已知問題」列了一條：「Median『忽略 nums2』bug 的提示直接洩漏修正後程式碼片段」。**這個問題已經被 code-blind AI 重構結構性解決**——重新測過同一個案例，提示只給診斷描述加問句，不再出現程式碼。舊簡報那條記錄的是採用 code-blind 設計「之前」的行為，如果要更新簡報，這條該從「已知問題」移到「已解決」。

### 4.4 建議的下一步測試優先順序

1. **先做 #2（AI 提示品質回歸測試）**：比起幫新兩題做 TPR/TNR 收斂，這個成本低很多——加幾條 `assert "def " not in hint` / `assert "return" not in hint.lower()` 這類簡單斷言到 `verify_hints.py`，就能自動抓「AI 突然又開始給程式碼」的退化。
2. **#1（新兩題測資收斂）**：規劃內但非緊急，因為手動測資已驗證有效，只是沒有論文等級的量化證明。
3. **#4（正式環境瀏覽器測試）**：跑一次跟本機一樣的手動流程即可，成本很低，建議在下次要展示 demo 前做。
4. **#3（Fuzzing 對照）**：優先度最低，主要是為了論文/簡報的完整性，不影響系統可用性。
