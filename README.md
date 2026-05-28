# Python 學習平台

> 給大一學生的 LeetCode 風格 Python 練習平台，提交程式碼後自動執行測試並由 AI 給予引導式提示。

---

## 功能介紹

### 核心功能

1. **程式碼編輯器**：Monaco Editor（與 VS Code 同款），語法高亮、自動縮排
2. **自動判題**：提交後後端執行 17 組測試案例，即時回傳通過 / 失敗結果
3. **AI 引導提示**：判題失敗時，Groq AI 分析錯誤類型，給予方向提示（不直接給答案）
4. **錯誤分類**：語法錯誤 / 執行時錯誤 / 忘記 return / 答案錯誤，各有不同提示策略

---

## 技術架構

```
前端（Vue 3 + Vite）
    POST /submit { code }
        ↓
後端（FastAPI）
    ├── judge.py    → executor.py → subprocess（執行學生程式碼）
    │   asyncio.gather 並行跑 17 組測資
    └── ai.py       → Groq API（llama-3.1-8b-instant）
        ↓
回傳 { results: [...17筆], hint: "..." }
```

### 後端模組

| 檔案 | 職責 |
|---|---|
| `main.py` | FastAPI，單一 endpoint `POST /submit` |
| `executor.py` | AST 安全過濾 → 語法檢查 → ThreadPoolExecutor 執行 → timeout 處理 |
| `judge.py` | `asyncio.gather` 並行跑全部測資 |
| `ai.py` | 依 error_type 選 prompt 分支，呼叫 Groq API |
| `problem.py` | 17 組 TEST_CASES（LC 官方 3 筆 + 論文方法生成 14 筆） |

### 前端元件

| 元件 | 功能 |
|---|---|
| `App.vue` | 左右兩欄佈局、提交邏輯、冷啟動偵測 |
| `ProblemStatement.vue` | 題目描述 + 3 個範例卡片 |
| `CodeEditor.vue` | Monaco Editor（Python, vs-dark theme） |
| `ResultPanel.vue` | 測試結果（顯示到第一個失敗）+ AI 提示卡 |

---

## 17 個測試案例設計

### 前 3 筆：LeetCode 官方範例（熱身）

| # | 輸入 | 答案 | 設計目的 |
|---|---|---|---|
| 1 | `abcabcbb` | 3 | 基本 sliding window，出現重複後要縮窗 |
| 2 | `bbbbb` | 1 | 全部相同字元，答案永遠是 1 |
| 3 | `pwwkew` | 3 | 重複出現後正確答案不在字串末尾 |

### carry_kill 組（殺 no_reset_left bug）

> 模式 `X + Y₁..Yₖ + X + Z`：正確解遇第二個 X 只丟掉第一個 X 並保留中間 Y；bug 解整個清空重算。

| # | 輸入 | 答案 | 說明 |
|---|---|---|---|
| 4 | `gogn` | 3 | 最小 carry，落差小但精準 |
| 5 | `qmjqztg` | 6 | prefix_len=2，bug 解落差 2 |
| 6 | `zuxtzrhmqc` | 9 | prefix_len=3，落差更大 |

### doubled_distinct 組（殺 count_unique bug）

> 模式 `aabbccdd...`：set 大小 >> 正確答案，`count_unique` 誤回傳 set 大小。

| # | 輸入 | 答案 | 說明 |
|---|---|---|---|
| 7 | `aabbccddeeff` | 2 | 6 對，count_unique 回傳 6 |
| 13 | `aabbccddeeffgghhiijj` | 2 | 10 對，差距更明顯 |

### combo_kill 組（同時殺 4 種 bug）

> 結構：doubled前綴 + XYZX carry中段 + 長 distinct 尾段
> - doubled 前綴 → 殺 `count_unique`
> - 前段重複 → 殺 `inner_return`（提早 return 漏掉後面）
> - XYZX carry → 殺 `no_reset_left`（清空窗口漏掉中間段）
> - len >> answer → 殺 `always_len`

| # | 輸入 | 答案 |
|---|---|---|
| 8 | `mmiictscxgyvo` | 8 |
| 9 | `ttdduuycnysbaleg` | 9 |
| 10 | `rroouumszmdgjakhwc` | 11 |
| 11 | `hhjjiinnyduyskmrec` | 9 |
| 12 | `beebcedfeaeadcebbfde` | 5 |
| 14 | `ffbbuuccgqzgwisanldxtk` | 13 |
| 15 | `ddrrsskkhhbtxbanquoiym` | 11 |
| 16 | `wwzzooueyudmficvgrxnjp` | 15 |
| 17 | `qqccffzzkkidaiwntpherjlm` | 13 |

---

## AI 提示策略（4 種分支）

```
error_type
├── syntax_error   → 解釋語法錯誤，引導找到問題行（150字）
├── runtime_error  → 解釋執行時錯誤訊息（150字）
├── no_return      → 提醒函式必須 return 值（100字）
└── wrong_answer   → 傳入第一個失敗的 input/actual/expected
                     特別提示 AI 先檢查：return 縮排層級、迴圈是否提早終止（150字）
```

---

## 安全機制

- **AST 靜態分析**：禁止 import `os`, `sys`, `subprocess`, `socket` 等危險模組
- **語法預編譯**：`compile()` early return，避免 subprocess 卡住
- **ThreadPoolExecutor**：跨平台相容（Windows / Linux），timeout 防止無限迴圈
- **prompt 截斷**：超過 50 字元的輸入值截斷，避免壓力測試案例讓 AI prompt 過大

---

## 測資品質指標（論文方法）

依據論文 *CodeContests-O: Powering LLMs via Feedback-Driven Iterative Test Case Generation* 建立測資評估流程：

| 指標 | 說明 | 結果 |
|---|---|---|
| **TPR** | 正確解通過率（不誤殺） | 1.000（全程維持） |
| **TNR** | 錯誤解擋下率（鑑別力） | 0.882（從 baseline 0.491 提升 +79.8%） |

迭代歷程：

| 版本 | TNR | 關鍵改動 |
|---|---|---|
| baseline | 0.491 | 原始 18 筆 hardcoded |
| v1 | 0.689 | 砍低價值測資，加 KILLER 模式 |
| v2 | 0.729 | 設計 carry_kill（XYXZ pattern） |
| v3 | 0.745 | 大量 doubled_distinct（被稀釋） |
| **v4** | **0.882** | **combo_kill：一個字串同殺 4 種 bug** |

---

## 本機啟動

### 環境需求

- Python 3.10+
- Node.js 18+

### 後端

```bash
cd backend
pip install -r requirements.txt

# 建立 .env
echo "GROQ_API_KEY=gsk_..." > .env

# 啟動
python -m uvicorn main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 開啟 http://localhost:5173
```

### 執行測試

```bash
cd backend
pytest -v
```

---

## 部署

| 服務 | 平台 | URL |
|---|---|---|
| 前端 | Vercel（自動部署） | https://python-learning-platform-chi.vercel.app/ |
| 後端 | Render（自動部署） | https://python-learning-platform-88vh.onrender.com |

`git push` 自動觸發兩邊重新部署。Render 免費方案閒置 15 分鐘後休眠，前端有冷啟動提示。

---

## 目錄結構

```
python-learning-platform/
├── backend/
│   ├── main.py          # FastAPI app，POST /submit
│   ├── executor.py      # ThreadPoolExecutor 執行學生程式碼 + AST 安全過濾
│   ├── judge.py         # 17 組 test case 並行比對
│   ├── ai.py            # Groq API，4 種 prompt 分支
│   ├── problem.py       # 題目定義 + 17 組 TEST_CASES
│   ├── requirements.txt
│   └── tests/           # pytest 測試（含品質守門員）
├── frontend/
│   ├── index.html
│   └── src/
│       ├── App.vue
│       ├── api.js
│       └── components/
│           ├── ProblemStatement.vue
│           ├── CodeEditor.vue
│           └── ResultPanel.vue
└── backend/testgen/     # 離線測資生成工具（論文方法實作）
```
