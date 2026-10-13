# Design Spec: Python 程式學習平台

**Date:** 2026-04-08  
**Status:** Approved

---

## Context

為大一學生設計的python程式學習平台。目標是讓學生在解題過程中獲得 AI 的學習引導，而不只是看到對錯。與 LeetCode 的核心差異在於：AI 會分析學生程式碼的實際輸出與測試案例的差異，推斷學生可能犯了什麼邏輯錯誤，再給予引導式提示（而非直接給答案）。

---

## 技術選型

| 層級 | 技術 |
|------|------|
| 前端 | Vue.js + `@guolao/vue-monaco-editor` |
| 後端 | FastAPI (Python) |
| 程式碼執行 | Python `subprocess` + timeout |
| AI 分析 | Groq Cloud API（llama-3.1-8b-instant，OpenAI 相容格式） |

---

## 題目

**Longest Substring Without Repeating Characters（LeetCode #3, Medium）**

- 函式簽名：`def lengthOfLongestSubstring(self, s: str) -> int`
- 選題理由：大一生直覺上會用暴力解（雙層迴圈），其錯誤輸出能精準對應「沒有偵測重複字元」、「視窗邊界未更新」等具體錯誤，適合 AI 分析。

### Test Cases

共 18 組，分四類，定義於 `backend/problem.py`，來源：`testcase.txt`。

**基本測試（3 組）**

| # | Input | Expected |
|---|-------|----------|
| 1 | `"abcabcbb"` | `3` |
| 2 | `"bbbbb"` | `1` |
| 3 | `"pwwkew"` | `3` |

**邊界條件（4 組）**

| # | Input | Expected |
|---|-------|----------|
| 4 | `""` | `0` |
| 5 | `"a"` | `1` |
| 6 | `"au"` | `2` |
| 7 | `"aa"` | `1` |

**進階測試（6 組）**

| # | Input | Expected |
|---|-------|----------|
| 8 | `"abcdefg"` | `7` |
| 9 | `"dvdf"` | `3` |
| 10 | `"anviaj"` | `5` |
| 11 | `"tmmzuxt"` | `5` |
| 12 | `"abba"` | `2` |
| 13 | `"aab"` | `2` |

**特殊字元（3 組）**

| # | Input | Expected |
|---|-------|----------|
| 14 | `"a b"` | `3` |
| 15 | `"!@#$%"` | `5` |
| 16 | `" "` | `1` |

**壓力測試（2 組）**

| # | Input | Expected |
|---|-------|----------|
| 17 | `"a" * 50000` | `1` |
| 18 | `"abcdefghijklmnopqrstuvwxyz"` | `26` |

---

## 系統流程

```
學生在 Monaco Editor 撰寫程式碼
    │
    │ POST /submit { code: "..." }
    ▼
FastAPI
    ├── 1. executor.py：以 asyncio subprocess 執行單一 test case
    │       ├── 語法錯誤 / exception → 捕捉 stderr，標記 error_type="syntax_error" / "runtime_error"
    │       ├── 回傳 None → 標記 error_type="no_return"
    │       └── 正常執行 → 回傳 actual output
    ├── 2. judge.py：用 asyncio.gather 並行執行全部 18 組 test case，比對 actual vs expected
    │       收集完整結果：[{ input, expected, actual, passed, error_type, stderr }, ...]（共 18 筆，順序與 TEST_CASES 一致）
    ├── 3. ai.py：組裝 prompt → 呼叫 Groq Cloud API
    │       從完整結果中篩出所有失敗的 cases → 送給 AI 做 pattern 推斷
    │       AI 先推斷錯誤根本原因（從多組失敗 pattern），再針對第一個失敗給提示
    └── 4. 回傳 { results: [完整 18 筆], hint: "..." }
    │
Vue.js 前端（顯示邏輯在這裡控制）
    └── 收到完整 results 後，只渲染到第一個失敗為止，後面的不顯示
        顯示 AI 提示區塊，聚焦在第一個失敗的 test case
```

---

## 檔案結構

```
畢業專題/
├── backend/
│   ├── main.py          # FastAPI app，定義 POST /submit
│   ├── executor.py      # subprocess 執行 + timeout 控制（5s）
│   ├── judge.py         # test case 比對，回傳 results 陣列
│   ├── ai.py            # Groq Cloud API 呼叫，prompt 組裝
│   └── problem.py       # 題目定義：test cases、函式名稱、題目說明
└── frontend/
    ├── index.html
    └── src/
        ├── App.vue
        ├── components/
        │   ├── ProblemStatement.vue   # 題目說明 + 範例
        │   ├── CodeEditor.vue         # Monaco Editor（Python 3）
        │   └── ResultPanel.vue        # 測試結果列表 + AI 提示
        └── api.js                     # axios POST /submit
```

---

## UI 設計

**佈局：左右兩欄**
- **左欄：** Topbar → 題目說明 → Monaco Editor → 提交按鈕
- **右欄：** sticky 500px，測試結果 + AI 學習提示

**主題：** Warm Terminal 美學
- 深色背景（`#0c0b09`）+ amber accent（`#dfa050`）
- 全站統一 IBM Plex Mono 字型
- Pass/Fail 用 green/red border-left，hover 有微互動

**冷啟動提示：** 提交後若 loading 超過 5 秒（Render 免費方案冷啟動），顯示「☕ 伺服器冷啟動中，請稍候約 30 秒…」

**區塊功能：**
1. **Topbar** — 平台名稱 + LeetCode #3 tag
2. **題目說明** — 題目標題、描述、3 組範例卡片
3. **程式碼編輯器** — Monaco Editor，Python 3 語法高亮 + 自動補全，vs-dark 主題
4. **提交按鈕** — 按下後送出程式碼，觸發整個分析流程
5. **測試結果** — 依序顯示通過的 test case（✓），直到第一個失敗（✗）為止，後面的不顯示
6. **AI 學習提示** — teal 邊框區塊，針對第一個失敗的 test case 給出分析與引導

---

## AI Prompt 設計

`ai.py` 在組裝 prompt 前，先檢查 `first_fail['error_type']`，根據情況選擇對應的 prompt 版本：

---

### 情況一：`syntax_error` 或 `runtime_error`

程式根本沒執行，`all_failed_cases` 的 actual 全為 None，沒有 pattern 可分析。使用簡化版 prompt：

```
你是一個程式學習助教，目標是幫助大一學生學習 Python。

學生程式碼：
{student_code}

執行時發生錯誤，錯誤訊息如下：
{stderr}

請解釋這個錯誤訊息的意思，並引導學生找到並修正問題。

規則：
1. 不要直接給出修正後的程式碼
2. 用繁體中文回答，語氣友善鼓勵
3. 回答控制在 150 字以內
```

---

### 情況二：`no_return`

程式執行成功但沒有回傳值，無需分析 pattern。使用簡化版 prompt：

```
你是一個程式學習助教，目標是幫助大一學生學習 Python。

學生程式碼：
{student_code}

問題：函式執行後回傳了 None，代表函式內沒有 return 語句或 return 沒有帶值。

請提醒學生函式需要回傳值，並說明 return 的用法。

規則：
1. 不要直接給出答案
2. 用繁體中文回答，語氣友善鼓勵
3. 回答控制在 100 字以內
```

---

### 情況三：`wrong_answer`

程式正常執行但答案錯誤，使用完整版 prompt，聚焦在第一個失敗案例的 input/output 落差，其餘失敗案例作為輔助參考（字串輸入/輸出會截斷為 50 字元，避免壓力測試 case 把 prompt 撐爆）：

```
你是一個程式學習助教，幫助大一學生學習 Python。

題目：Longest Substring Without Repeating Characters
學生程式碼：
{student_code}

目前學生看到的第一個失敗案例：
- 輸入：{first_fail_input}
- 學生程式碼的輸出：{first_fail_actual}
- 正確答案：{first_fail_expected}

其他失敗案例（輔助參考）：
{failed_summary}
（每筆格式：Input / Expected / Actual，長字串截斷 50 字元）

請根據「這個輸入」和「學生程式碼實際給出的輸出」，分析程式碼哪裡出問題，然後給學生一個引導式提示，讓他能朝正確方向思考。

要求：
1. 不要直接給出正確程式碼
2. 提示要具體，針對這個 input/output 的落差，不要泛泛而談
3. 用繁體中文，語氣自然友善，像在跟學生說話
4. 控制在 150 字以內
```

**設計理念：** 原本使用「步驟一/步驟二」格式會讓 AI 回答過度結構化、機械式。改為自然語氣的分析 + 提示，聚焦在「這個 input 進去為什麼你的輸出是 X 而不是 Y」，讓 AI 的推理更直接對應學生看到的錯誤。

---

## 多人同時使用

- FastAPI 搭配 `uvicorn`，預設支援非同步並發
- `executor.py` 用 `asyncio.create_subprocess_exec`（非阻塞），讓多個學生的提交可同時執行
- `judge.py` 用 `asyncio.gather` 並行跑同一份 submission 的 18 個 test case，縮短單次提交回應時間
- 每次提交是完全獨立的 subprocess，沒有共享狀態
- 壓力測試 case（`"a"*50000`）timeout 設為 **10s**，其餘 **5s**，防止暴力解卡住其他人
- **部署注意：** Render 免費方案只有 0.1 CPU 共享，若要在電腦教室讓多位學生同時測試，可能會遇到 CPU 飽和問題。正式教室測試前建議先評估，必要時升級付費方案或改用自架 VPS

---

## 安全性

- subprocess 執行設定 timeout（5s 一般、10s 壓力測試），防止無限迴圈
- 不允許學生程式碼 import 危險模組：`os`、`sys`、`subprocess`、`socket`（blacklist 過濾）
- 每個 subprocess 執行在獨立 process，不影響後端主進程

---

## 驗證方式

1. 啟動 FastAPI：`uvicorn main:app --reload`
2. 啟動 Vue dev server：`npm run dev`
3. 在瀏覽器開啟前端，輸入以下測試程式碼：
   ```python
   class Solution:
       def lengthOfLongestSubstring(self, s: str) -> int:
           return len(s)  # 刻意的錯誤解法
   ```
4. 確認 Test 1、6、8、15、18 PASS，其餘 FAIL
5. 確認 AI 提示有針對失敗的測試給出具體分析（特別是 Test 2、9、12）
6. 多人測試：同時開兩個瀏覽器分頁提交，確認兩者都能正常收到結果
