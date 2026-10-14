# Python 學習平台

> 給大一學生的 LeetCode 風格 Python 練習平台，提交程式碼後自動執行測試並由 AI 給予引導式提示。

---

## 功能介紹

### 核心功能

1. **程式碼編輯器**：Monaco Editor（與 VS Code 同款），語法高亮、自動縮排
2. **多題目**：頂端下拉選單切換 5 題（見下方題目表），標示難度
3. **自動判題**：提交後後端執行該題全部測試案例，即時回傳通過 / 失敗結果
4. **AI 引導提示**：判題失敗時，AI 分析錯誤類型，給予方向提示（不直接給答案、不讀學生程式碼）
5. **錯誤分類**：語法錯誤 / 執行時錯誤 / 執行超時 / 忘記 return / 答案錯誤，各有不同提示策略
6. **虛擬碼**：五題都有通過往返檢查的中文虛擬碼，在題目頁顯示（可收合），AI 提示可引用步驟編號

### 題目

| 題目 id | 題目 | 難度 | 測資數 | 虛擬碼 |
|---|---|---|---|---|
| `longest-substring` | Longest Substring Without Repeating Characters（LC #3） | 中 | 18 | 有 |
| `valid-parentheses` | Valid Parentheses（LC #20） | 易 | 19 | 有 |
| `median-two-sorted-arrays` | Median of Two Sorted Arrays（LC #4） | 難 | 45 | 有 |
| `best-time-stock` | Best Time to Buy and Sell Stock（LC #121） | 易 | 10 | 有 |
| `longest-valid-parentheses` | Longest Valid Parentheses（LC #32） | 難 | 54 | 有 |

---

## 目前進度

> GitHub 上的 `main` 就是組上最新的進度；推到 `main` 會自動部署到正式網站。

### 更新紀錄

| 日期 | 內容 |
|---|---|
| 2026-10-14 | valid-parentheses、median-two-sorted-arrays 也改用 AI 輔助產生測資：各建 3 份正解、6 份訓練用錯解、3 份驗收用錯解，跑全自動流程後寫回 `problem.py`（12→19 道、11→45 道）。修正 `propose.py`：AI 回覆整份讀不出 JSON 時不再算成一輪 |
| 2026-10-14 | valid-parentheses、median-two-sorted-arrays 補上虛擬碼（同一套往返檢查，第 1 次通過），五題都有虛擬碼；兩題各新增一份正解與輸入規格（`backend/testgen/problems/<id>/`），只用來產生虛擬碼，沒有跑測資流程 |
| 2026-10-14 | longest-valid-parentheses、longest-substring 的虛擬碼改用中文重新產生，並重新通過往返檢查（原本一題是英文、一題有一步寫錯） |
| 2026-10-14 | AI 輔助測資分支合併到 `main`：正式網站從 3 題變 5 題（新增 best-time-stock、longest-valid-parentheses）、題目頁顯示虛擬碼、AI 提示可引用虛擬碼步驟；GitHub 只保留 `main` |

### AI 輔助測資的結果

TPR 五題都是 1.0（不誤殺正解）；驗收池每題只跑一次（valid-parentheses 例外，見表下說明）。

| 題目 | 測資數 | 訓練池 TNR | 驗收池 TNR |
|---|---|---|---|
| longest-substring | 18 | 0.8889 | 0.47 |
| best-time-stock | 10 | 0.3833（補強前實驗紀錄 0.5833） | 0.4667，無漏網 |
| longest-valid-parentheses | 54 | 0.6759 | 0.5370，無漏網 |
| valid-parentheses | 19（原 12） | 0.2193（上限 0.5，達成率 0.44；原 0.1528） | 0.1228，無漏網 |
| median-two-sorted-arrays | 45（原 11） | 0.5778（原 0.2576） | 0.6148，無漏網 |

- **valid-parentheses**：第一次執行時，AI 第 1 輪的回覆格式錯誤，被工具誤判為「停滯」並用掉了驗收池（TNR 0.1389）。修正工具後重跑，所以驗收池是第二次使用；第一次的紀錄原樣保留在 `backend/testgen/problems/valid-parentheses/rounds/void_20261014/`。重跑的第 2 輪 AI 把字串多包了一層引號，12 筆全部不合法，流程依規則判定停滯，只跑了 2 輪。
- 這兩題的錯解池由我們依常見錯誤手寫，各 9 份，先分好訓練／驗收再開始評測。

### 已知問題與待辦

- AI 提示裡的 `**粗體**` 會直接顯示星號
- 遇到無窮迴圈要等 20～35 秒才顯示「執行超時」
- 使用者說明（`docs/superpowers/specs/user-facing-draft.md`）的【待確認】欄位尚未填入
- `docs/IEEE_Paper.md` 的題目表測資數過時
- 字串輸入的題目，AI 提案偶爾會把字串多包一層引號，整輪被判不合法（valid-parentheses 第 2 輪）；提示詞尚未針對這點調整

---

## 技術架構

```
前端（Vue 3 + Vite）
    GET /problems、GET /problems/{id}、POST /submit { code, problem_id }
        ↓
後端（FastAPI）
    ├── judge.py    → executor.py → subprocess（執行學生程式碼）
    │   asyncio.gather 並行跑該題全部測資
    └── ai.py       → Groq API（openai/gpt-oss-20b）→ masking.py 遮罩 → hint_guard.py 檢查
        ↓
回傳 { results: [...], hint: "..." }
```

### 後端模組

| 檔案 | 職責 |
|---|---|
| `main.py` | FastAPI：`GET /problems`、`GET /problems/{id}`、`POST /submit` |
| `executor.py` | AST 安全過濾 → 語法檢查 → ThreadPoolExecutor 執行 → timeout 處理 |
| `judge.py` | `asyncio.gather` 並行跑全部測資 |
| `ai.py` | 依 error_type 選 prompt 分支，呼叫 Groq API |
| `masking.py` | 提示夾帶能通過測資的完整解答時，遮蔽關鍵邏輯 |
| `hint_guard.py` | 檢查提示品質（不給程式碼、不整段複述虛擬碼） |
| `problem.py` | `PROBLEMS` 登錄表：5 題的題目敘述、範例、測資，並載入通過檢查的虛擬碼 |

### 前端元件

| 元件 | 功能 |
|---|---|
| `App.vue` | 左右兩欄佈局、提交邏輯 |
| `ProblemStatement.vue` | 題目描述、範例卡片、限制條件、虛擬碼（可收合） |
| `CodeEditor.vue` | Monaco Editor（Python, vs-dark theme） |
| `ResultPanel.vue` | 測試結果（顯示到第一個失敗）+ AI 提示卡 |

---

## Longest Substring 的測資設計

以下是 longest-substring 人工迭代出的 17 筆測資；第 18 筆是 5×10⁴ 字元的壓力測資（擋 O(n²) 寫法）。best-time-stock 與 longest-valid-parentheses 的測資由 `backend/testgen/` 的 AI 輔助流程產生，紀錄在 `backend/testgen/rounds/`。

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
└── wrong_answer   → 傳所有失敗的 (input, expected, actual)，不讀學生程式碼
                     AI 從數值 pattern 推斷 bug 類型，給蘇格拉底式引導提示（200字）
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

`git push` 自動觸發兩邊重新部署。Render 免費方案閒置 15 分鐘後休眠，首次請求需等待約 30 秒冷啟動。

---

## 目錄結構

```
python-learning-platform/
├── backend/
│   ├── main.py          # FastAPI app，GET /problems、GET /problems/{id}、POST /submit
│   ├── executor.py      # ThreadPoolExecutor 執行學生程式碼 + AST 安全過濾
│   ├── judge.py         # 該題全部 test case 並行比對
│   ├── ai.py            # Groq API，依錯誤類型分支
│   ├── masking.py       # 提示遮罩
│   ├── hint_guard.py    # 提示品質檢查
│   ├── problem.py       # 5 題的題目定義與測資
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
