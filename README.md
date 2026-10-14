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
7. **遮照填空**：同一題連續 3 次沒通過，AI 提示下方會出現「填空提示」——標準答案把關鍵部分（條件、迴圈範圍、關鍵變數更新）挖成編號空格，讓學生自己補；通過後收起。次數記在學生自己的瀏覽器

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
| 2026-10-14 | 修正無窮迴圈要等 40 秒以上（一筆超時後略過其餘測資，約 5 秒）；AI 提示的 `**粗體**`、程式碼區塊改為正確顯示；文件一致性整理，README 新增「尚未實作的功能」與「接下來的任務」 |
| 2026-10-14 | 新增遮照填空（`extension-plan.md` 第 2 節的設計）：同一題連續 3 次沒通過就顯示標準答案挖洞的填空題，通過後收起；五題都驗證過「填回答案測資全過、挖洞版本過不了」 |
| 2026-10-14 | 新增 `backend/testgen/mask_demo.py`：故意讓提示夾帶完整正解，印出遮罩前後對照，方便展示遮罩功能 |
| 2026-10-14 | 題目頁的「虛擬碼」收合列改成青綠色色塊，加上展開箭頭與「點開看解題步驟」提示，比較顯眼 |
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

### 已知問題

- AI 提案在字串輸入的題目偶爾把字串多包一層引號，整輪被判不合法（valid-parentheses 第 2 輪，組員指南 K21）；要改提示詞才能避免，屬於改流程
- 提示遮罩（`masking.py`）會保留程式碼裡的註解；若 AI 給的程式碼附有說明解法的註解，遮罩後仍會透露思路
- AI 提示偶爾會說錯數字細節（例如「輸出比期望值大 1 或 2」），只是方向提示，不保證每句都精確
- 虛擬碼有幾處小瑕疵（重複描述迴圈、用了 `//` 等程式寫法），記在各題 `pseudocode.json` 的 `format_warnings`；照規則不手動改寫
- 填空提示的「連續失敗次數」存在學生自己的瀏覽器，換瀏覽器或清除網站資料就會歸零
- 除了 longest-substring，其餘四題的測資都還沒達到收斂門檻（達成率 ≥ 0.85）
- Render 免費方案閒置 15 分鐘會休眠，第一次載入要等 30～60 秒

### 設計方案中尚未實作的功能

| 來源 | 功能 | 狀態 |
|---|---|---|
| `extension-plan.md` 第 1 節 | 分階段提示：方向 → 細節 → 測資分析 → 虛擬碼，連錯 3 次升一階 | 未實作。目前是一種 AI 提示，加上題目頁一直可看的虛擬碼；第 2 節的最後一階（遮照填空）已實作 |
| `extension-plan.md` 第 3 節 | 學習成效量化：分組實驗的說明書（嘗試次數、完成時間、後測、同意書） | 未撰寫 |
| `extension-plan.md` 第 4 節 | 自動標籤系統：AI 判斷錯誤程式屬於哪一類，人再覆核 | 未實作 |
| `extension-plan.md` 第 6 節／組員指南 A2、K10 | 加強安全執行：擋 `open`、`eval` 等內建函式，加記憶體上限，必要時用容器隔離 | 未實作；目前只擋模組名稱（威脅模型：無意誤用） |
| 組員指南 A1、A3、A4 | 安全批次執行器、檢查關接批次執行器、registry 自動化 | 未實作（不影響實測） |
| 組員指南 B1、B3–B6 | AI 先建池：建池腳本、雜湊與淘汰迴圈、標籤審核紀錄、驗收批用另一個模型、輸入規格自動產生 | 未實作；目前 S+／S- 池與 `spec.py` 都是人工寫的 |
| 組員指南 C3 | 使用者說明與同意說明 | 草稿完成，【待確認】欄位（保存期限、可存取的人、退出後資料處理）待負責人填入 |
| 組員指南 C4 | 失敗模式記錄與離線比對 | 未實作；需先完成 C3 的同意說明 |
| 組員指南 D1 | 論文、簡報、用語同步 | `IEEE_Paper.md` 的題目表已更新；新加的兩題結果、遮照填空尚未寫進論文與簡報；`IEEE_Paper.docx` 未同步 |

### 接下來的任務

依優先順序：

1. **填完使用者說明的【待確認】欄位（C3）**：給其他人試用前一定要完成（`docs/superpowers/specs/user-facing-draft.md`）
2. **找人試用網站**：照「試用流程」請幾位同學實際操作五題，收集虛擬碼、AI 提示、填空提示的意見
3. **論文與簡報同步（D1）**：補上五題的結果、虛擬碼中文化、遮照填空、無窮迴圈修正；同步 `IEEE_Paper.docx`
4. **決定是否處理 K21**：調整 AI 提案的提示詞（避免字串多包引號）後重跑 valid-parentheses；屬於改流程，驗收池也已用過兩次，需要先決定
5. **分階段提示（extension-plan 第 1 節）**：和已上線的虛擬碼、填空提示如何搭配要先想清楚（設計文件提到一開始就給虛擬碼，第 4 階會變多餘）
6. **加強安全執行（A2／extension-plan 第 6 節）**：開放給更多人使用前建議完成
7. 有空再做：A1、A3、A4、B1、B3–B6、C4、自動標籤系統、學習成效量化說明書

---

## 技術架構

```
前端（Vue 3 + Vite）
    GET /problems、GET /problems/{id}、GET /problems/{id}/cloze、POST /submit
    （POST /submit 送 { code, problem_id }）
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
| `main.py` | FastAPI：`GET /problems`、`GET /problems/{id}`、`GET /problems/{id}/cloze`、`POST /submit` |
| `executor.py` | AST 安全過濾 → 語法檢查 → ThreadPoolExecutor 執行 → timeout 處理 |
| `judge.py` | `asyncio.gather` 並行跑全部測資 |
| `ai.py` | 依 error_type 選 prompt 分支，呼叫 Groq API |
| `masking.py` | 提示夾帶能通過測資的完整解答時，遮蔽關鍵邏輯 |
| `hint_guard.py` | 檢查提示品質（不給程式碼、不整段複述虛擬碼） |
| `cloze.py` | 遮照填空：用 AST 從標準答案挑關鍵部分挖成編號空格（不經 AI，每次結果相同；答案不送前端） |
| `problem.py` | `PROBLEMS` 登錄表：5 題的題目敘述、範例、測資，並載入通過檢查的虛擬碼 |

### 前端元件

| 元件 | 功能 |
|---|---|
| `App.vue` | 左右兩欄佈局、提交邏輯 |
| `ProblemStatement.vue` | 題目描述、範例卡片、限制條件、虛擬碼（可收合） |
| `CodeEditor.vue` | Monaco Editor（Python, vs-dark theme） |
| `ResultPanel.vue` | 測試結果（顯示到第一個失敗）+ AI 提示卡 |
| `ClozePanel.vue` | 連續失敗倒數，與第 3 次後的填空提示 |

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

## AI 提示策略（5 種分支）

AI 只看得到題目、測資的輸入／期望／實際輸出、錯誤訊息與虛擬碼，**看不到學生程式碼**。

```
error_type
├── syntax_error   → 解釋語法錯誤，引導找到問題行（120 字）
├── runtime_error  → 解釋執行時錯誤訊息，問「這個輸入有什麼特別」（150 字）
├── timeout        → 壓力測資超時：引導想效率；短測資就超時：引導檢查無窮迴圈（150 字）
├── no_return      → 提醒函式必須 return 值（100 字）
└── wrong_answer   → 傳所有失敗的 (input, expected, actual)，不讀學生程式碼
                     AI 從數值 pattern 推斷 bug 類型，給蘇格拉底式引導提示（200 字）
```

提示產生後依序經過 `masking.py`（夾帶的程式碼能過測資就遮蔽）與 `hint_guard.py`（品質檢查），通過才顯示。

---

## 安全機制

- **AST 靜態分析**：禁止 import `os`, `sys`, `subprocess`, `socket` 等危險模組
- **語法預編譯**：`compile()` early return，避免 subprocess 卡住
- **ThreadPoolExecutor**：跨平台相容（Windows / Linux），timeout 防止無限迴圈（一般 5 秒、壓力測資 10 秒；一筆超時後其餘還沒開始的測資直接略過）
- **prompt 截斷**：超過 50 字元的輸入值截斷，避免壓力測試案例讓 AI prompt 過大
- **提示遮罩**（`masking.py`）：AI 提示裡的程式碼若能通過任何一筆測資，就請 AI 把關鍵邏輯換成 `# TODO`；遮完仍能通過就整段換成一句提醒。想看實際效果：`cd backend && python -m testgen.mask_demo --problem best-time-stock`（需要 `backend/.env` 的 GROQ_API_KEY），會印出遮罩前後的對照

---

## Longest Substring 的人工迭代歷程（論文方法的第一題）

五題目前的結果見上方「目前進度」。以下是最早以人工迭代完成的 longest-substring。依據論文 *CodeContests-O: Powering LLMs via Feedback-Driven Iterative Test Case Generation* 建立測資評估流程：

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
│   ├── main.py          # FastAPI app，GET /problems、GET /problems/{id}、GET /problems/{id}/cloze、POST /submit
│   ├── executor.py      # ThreadPoolExecutor 執行學生程式碼 + AST 安全過濾
│   ├── judge.py         # 該題全部 test case 並行比對
│   ├── ai.py            # Groq API，依錯誤類型分支
│   ├── masking.py       # 提示遮罩
│   ├── hint_guard.py    # 提示品質檢查
│   ├── cloze.py         # 遮照填空（標準答案挖洞）
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
│           ├── ResultPanel.vue
│           └── ClozePanel.vue
└── backend/testgen/     # 離線測資生成工具（論文方法實作）
```
