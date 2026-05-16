# Python 學習平台 — 專題說明

## 專案概述

給大一學生的 Python 程式學習平台（LeetCode 風格）。學生提交程式碼後，系統執行程式碼、比對 17 組測試案例，Groq AI 分析錯誤 pattern 並給予引導式提示（不直接給答案）。

目前只有一題：**Longest Substring Without Repeating Characters（LeetCode #3）**

**測資集已套用論文方法重做**（細節見「測資生成工具」章節）：TNR 從 0.49 → 0.88，全程 TPR=1.0。原本 18 筆 hardcoded 改成 17 筆由 `testgen/` 離線收斂出來的版本（首 3 筆保留 LC 官方範例做學生熱身），舊版備份在 `backend/problem_old.py`。

## 啟動方式

**後端（Terminal 1）：**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**前端（Terminal 2）：**
```bash
cd frontend
npm install   # 第一次需要
npm run dev
# 通常在 http://localhost:5173 或 5174（若 5173 被占用）
```

**Windows 注意：** executor.py 已改用 `ThreadPoolExecutor + subprocess.run`（跨平台相容），不再需要 ProactorEventLoop。

## 目錄結構

```
python-learning-platform/
├── backend/
│   ├── main.py          # FastAPI app，POST /submit（唯一 endpoint）
│   ├── executor.py      # ThreadPoolExecutor 執行學生程式碼 + AST 安全過濾（跨平台）
│   ├── judge.py         # 17 組 test case 比對，回傳完整 results 陣列
│   ├── ai.py            # Groq / Gemini 自動切換，4 種 prompt 分支
│   ├── problem.py       # 題目定義 + 17 組 TEST_CASES
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── .env             # GROQ_API_KEY=gsk_... 或 GEMINI_API_KEY=AIza...（不 commit）
│   └── tests/
│       ├── test_executor.py
│       ├── test_judge.py
│       ├── test_ai.py
│       ├── test_main.py
│       └── test_problem_quality.py  # 論文方法品質守門員
├── frontend/
│   ├── index.html
│   └── src/
│       ├── App.vue          # 左右兩欄佈局，handleSubmit，全域樣式
│       ├── api.js           # axios POST /submit（DEV 自動指向 localhost:8000）
│       └── components/
│           ├── ProblemStatement.vue  # 題目 + 3 個範例卡片
│           ├── CodeEditor.vue        # Monaco Editor（Python，vs-dark）
│           └── ResultPanel.vue       # 測試結果（到第一個失敗為止）+ AI 提示
└── backend/testgen/                 # 離線測資生成工具（論文方法的實作，不影響線上）
    ├── PROGRESS.md                   # 完整實驗紀錄（baseline→v4 四輪迭代）
    ├── QUICKSTART.md                 # 三道關卡的標準流程
    ├── TESTING_GUIDE.md              # 前端手動測試 6 段 bug 解的清單
    ├── gen.py                        # Python 生成器，10 個 mode 含 KILLER（combo_kill 等）
    ├── synthesize.py                 # 命令清單 → tests_v{N}.py 模組
    ├── run_eval.py                   # TPR/TNR 評估器，--tests 切換版本
    ├── export_to_problem_py.py       # 收斂結果 + LC 官方範例 → problem.py 格式
    ├── smoke_test.py                 # 5 個預檢，不需 pytest / server
    ├── http_smoke_test.py            # 用 TestClient 跑 HTTP 層（不啟 uvicorn）
    ├── play.py                       # 離線 CLI：貼程式碼跑完整 trace + 寫 log
    ├── view_session.py               # JSONL log 漂亮印出來 + 摘要
    ├── session_logger.py             # 後端 middleware（main.py 已接入，env var 控制）
    ├── commands_v1~v4.txt            # 每輪命令清單
    ├── tests_v1~v4.py                # 每輪測資集
    ├── feedback_baseline~v4.json     # 每輪反饋報告
    ├── solutions_correct/            # S+ 池（3 個正解）
    └── solutions_wrong/              # S- 池（6 個典型 bug pattern）
```

## 執行測試

```bash
cd backend
pytest -v
```

## 關鍵架構決策

- **後端跑全部 17 筆 test case**，前端只渲染到第一個失敗（含）為止
- `judge.py` 用 `asyncio.gather` 並行跑 17 個 test case，單次 submission 回應時間縮短約一半
- AI prompt 有 4 個分支：`syntax_error` → 強調「語法錯誤無法執行」；`runtime_error` → 強調「執行時錯誤」；`no_return` → 提醒 return；`wrong_answer`（error_type=None）→ 傳第一個失敗的 input/actual/expected + 其餘失敗 cases，並在分析前先提醒 AI 檢查 return 縮排層級與迴圈是否提早終止
- wrong_answer prompt 的 failed_summary 會截斷超過 50 字元的字串，避免壓力測試 case（`"a"*50000`）讓 prompt 過大導致 AI API 失敗
- executor 用 AST 過濾禁止模組（os, sys, subprocess, socket 等），用 `ThreadPoolExecutor + subprocess.run` 執行，跨平台相容（Windows / Linux）
- executor 在跑 subprocess 前先用 `compile()` 做語法檢查，語法錯誤直接 early return，stderr 格式帶上問題那行原碼與 `^` 指針

## 環境設定

```bash
# backend/.env（二擇一）
GROQ_API_KEY=gsk_...       # 從 console.groq.com/keys 取得（推薦，500k tokens/day 免費）
GEMINI_API_KEY=AIza...     # 從 aistudio.google.com/apikey 取得（備用）

# ai.py 自動偵測：有 GEMINI_API_KEY 優先用 Gemini，否則用 Groq

# Python 套件
cd backend && pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

## AI 設定

| 選項 | Provider | Model | 端點 |
|---|---|---|---|
| 主要（推薦） | Groq Cloud | `llama-3.1-8b-instant` | `https://api.groq.com/openai/v1` |
| 備用 | Google Gemini | `gemini-2.0-flash` | `https://generativelanguage.googleapis.com/v1beta/openai/` |

`ai.py` 透過環境變數自動切換，兩者均使用 openai Python SDK（OpenAI 相容格式）。

## CORS

後端允許所有 `localhost:*` port 及 `*.vercel.app`（regex）：
```python
allow_origin_regex=r"http://localhost:\d+|https://.*\.vercel\.app"
```

## 前端樣式

- **設計：** Warm Terminal 美學，IBM Plex Mono 統一全站字型
- **配色：** CSS 變數定義在 App.vue `<style>`，amber accent（`--amber: #dfa050`）
- **佈局：** 左欄（題目+編輯器+提交），右欄 sticky 500px（結果+AI 提示）
- **開發/線上 URL 切換：** `api.js` 用 `import.meta.env.DEV` 自動判斷

## 部署

- **GitHub：** https://github.com/yaoyao218/python-learning-platform
- **前端：** https://python-learning-platform-chi.vercel.app/（Vercel，免費）
- **後端：** https://python-learning-platform-88vh.onrender.com（Render，免費）
- `git push` 自動觸發兩邊重新部署
- Render 免費方案閒置 15 分鐘後休眠，前端有冷啟動提示（loading 超過 5 秒顯示警告）
- `api.js` 的 axios timeout 設為 60 秒

---

## 測資生成工具（testgen/）

依據論文 *CodeContests-O: Powering LLMs via Feedback-Driven Iterative Test Case Generation* 實作的離線測資生成 pipeline，**完全跟線上服務解耦**——不啟用就跟原本沒差。

### 為什麼存在

原本 `problem.py` 的測資是憑經驗挑的，沒有量化指標證明它能：
- 不誤殺正確解（**TPR**）
- 真的抓得到常見 bug（**TNR**）

引入論文方法之後可以系統化評估每筆測資的鑑別力，並用閉環迭代壓低錯誤解漏網率。

### 已達成數字

| 指標 | baseline | v4（現行）| 改善 |
|---|---|---|---|
| TPR | 1.0000 | 1.0000 | 維持 |
| **TNR** | **0.4907** | **0.8824** | **+79.8% 相對提升** |
| 漏網 S-（false positive） | 0 | 0 | 維持 |
| 測資數 | 18 | 17 | 品質躍升、數量略減 |
| count_unique 抓到率 | 5.56% | 64.71% | +11.6× |
| no_reset_left 抓到率 | 11.11% | 70.59% | +6.4× |
| inner_return 抓到率 | 27.78% | 88.24% | +3.2× |

### 核心抽象

| 論文記號 | testgen 實作 | 在 backend 的角色 |
|---|---|---|
| `S*` reference solution | `solutions_correct/sliding_window.py` | 給 synthesize 算每筆 expected |
| `S+` 正確解池 | `solutions_correct/*.py`（3 個）| run_eval 算 TPR |
| `S-` 錯誤解池 | `solutions_wrong/*.py`（6 個 bug pattern）| run_eval 算 TNR |
| `G^(i)` 生成器 | `gen.py` 的 10 個 mode 函式 | 產測資字串 |
| `C^(i)` 命令清單 | `commands_v{N}.txt` 一行一條 | 控制 mode 跟參數 |
| `T^(e,i)` 測資集 | `tests_v{N}.py` 的 `TEST_CASES` | 對應 problem.py 格式 |
| `R^(i)` 反饋報告 | `feedback_v{N}.json`（含 command_value、S- pass_rates、survivors）| 看哪輪要改什麼 |

### Cheat sheet — 常用指令

```bash
cd backend

# 預檢：5 個檢查 10 秒跑完，不需 server / pytest
python -m testgen.smoke_test

# HTTP 層測試：用 TestClient 跑 /submit 4 個劇本
python -m testgen.http_smoke_test

# 離線 CLI 模擬學生：貼程式碼看完整 trace + 自動寫 log
python -m testgen.play --file my_sol.py
python -m testgen.play                           # 互動：貼完 Ctrl-D

# 後端開 session logger 跑線上服務（前端用 Monaco）
# Windows:
set TESTGEN_SESSION_LOG=1 && python -m uvicorn main:app --reload --port 8000
# Linux/Mac:
TESTGEN_SESSION_LOG=1 uvicorn main:app --reload --port 8000

# 看 session log
python -m testgen.view_session                   # 全部
python -m testgen.view_session --last 5          # 最後 5 次
python -m testgen.view_session --summary         # AC率、平均耗時、最常踩雷

# 評估目前 problem.py 的 TPR/TNR
python -m testgen.run_eval --tests problem --label current

# 跑既有 + 新 pytest（含品質守門員）
pytest -v

# 回滾測資集
cp problem_old.py problem.py
```

### 怎麼加新 bug pattern 或新測資

迭代流程：

```bash
# 1. 新發現一個學生常犯的 bug
# 建立 backend/testgen/solutions_wrong/new_bug.py

# 2. 看現在的 problem.py 抓不抓得到
python -m testgen.run_eval --tests problem --label current
# 若 new_bug.py 通過率 ≈ 100% → 漏網了，需要補測資

# 3. 想新測資模式或調命令
# 編輯 backend/testgen/gen.py        加新 mode（選用）
# 編輯 backend/testgen/commands_v5.txt  加命令或抄前一輪改

# 4. 產測資 → 評估
python -m testgen.synthesize \
    --commands testgen/commands_v5.txt \
    --out testgen/tests_v5.py
python -m testgen.run_eval --tests testgen.tests_v5 --label v5

# 5. 滿意了就導出 + swap
python -m testgen.export_to_problem_py \
    --tests testgen.tests_v5 --out problem_v5.py \
    --feedback testgen/feedback_v5.json
cp problem.py problem_old.py                # 備份目前版
cp problem_v5.py problem.py                 # 上新版
python -m testgen.smoke_test                # 確認預檢全綠
pytest tests/test_problem_quality.py        # 確認守門員放行
```

### 品質守門員（pytest 自動把關）

`backend/tests/test_problem_quality.py` 4 個斷言：

| 斷言 | 條件 | 違反時的修法 |
|---|---|---|
| `test_tpr_equals_one` | TPR = 1.0 | 找哪筆測資讓正解輸出對不上 expected |
| `test_tnr_above_threshold` | TNR ≥ 0.85 | 跑 testgen 迭代改進 |
| `test_every_bug_caught_at_least_once` | 沒有 S- 通過所有測資 | 為漏網 bug 加 killer mode |
| `test_minimum_test_case_count` | TEST_CASES ≥ 10 筆 | 確保不被砍到太少 |

要切到另一個版本跑：`PROBLEM_MODULE=problem_old pytest tests/test_problem_quality.py`

### 跟 main.py 的整合方式

```python
# main.py 最上面
try:
    from testgen.session_logger import log_submission, LOG_ENABLED
except ImportError:
    LOG_ENABLED = False
    async def log_submission(*a, **kw): pass

# /submit handler 結尾
if LOG_ENABLED:
    await log_submission(code=req.code, results=results, hint=hint,
                         ai_prompt=build_prompt(req.code, results),
                         elapsed_ms=elapsed_ms)
```

`LOG_ENABLED` 預設 `False`，要開 logger 才會寫檔案。生產環境（Render）不設環境變數，行為跟舊版完全一樣。

### 重要設計決策

- **不用 testlib C++**：題目輸入只是字串，Python 隨機產生就夠用，避開編譯依賴
- **每個 mode 一個 Python 函式**：synthesize.py 用 `inspect.signature` 自動過濾參數
- **`combo_kill` mode 是突破點**：單一字串同殺 4 種 bug（doubled prefix + carry-kill 中段 + 長 distinct 尾）讓 TNR 一輪 +13 ppt
- **保留 LC 官方範例做首 3 筆**：學生看到熟悉的 abcabcbb / bbbbb / pwwkew 失敗時容易理解
- **問題排序按 input 長度**：「第一個失敗」會是短易讀的測資，不是 50000 字元 stress
- **session_logger 用 asyncio.Lock + asyncio.to_thread**：多 worker 寫檔不會打架，且不阻塞 event loop

### CLAUDE.md 之外的關鍵文件

- `backend/testgen/PROGRESS.md` — 完整實驗紀錄、四輪迭代的洞察，可當畢業專題報告章節初稿
- `backend/testgen/QUICKSTART.md` — 三道關卡的標準操作流程
- `backend/testgen/TESTING_GUIDE.md` — 前端手動測試 6 段 bug 解的清單
