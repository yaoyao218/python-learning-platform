# 基於回饋驅動迭代測資生成之 Python 程式學習平台設計與實作

**A Feedback-Driven Iterative Test Case Generation Method for a Python Programming Education Platform**

> **作者：** 姚雅瑤  
> **系所：** 資訊管理學系  
> **格式：** IEEE Conference Paper  
> **字數：** 約 6,000 字  

---

## Abstract

This paper describes the design of a Python programming education platform for first-year university students and reports an environment test of its two components. It is a proposal with an environment test: it does not claim accuracy, validity, or learning-outcome results. The first component is a code-blind hint system: the LLM receives only the problem statement and test results, never the student's code, and an output-side guard replaces hints that leak code or lack a guiding question. The second is a feedback-driven iterative test-case construction method inspired by CodeContests-O, in which a test set is scored by its True Negative Rate (TNR, the mean interception rate over a pool of wrong solutions). We describe what was observed when the pipeline was run. On one problem (LeetCode #3), four rounds of human-driven refinement raised TNR on the six wrong solutions used during iteration from 0.491 to 0.882, but on three wrong solutions withheld from iteration the same test set reached only 0.471, so the first figure should be read as in-sample. On a second problem (Longest Valid Parentheses) we ran an AI-assisted loop (AI proposes, an objective harness scores, a reviewer selects) with an AI standing in for the human reviewer; in a handful of runs, feeding scores back to the model was the only condition that produced inputs catching the hardest wrong solution, while overall TNR rose about equally with and without feedback. These observations come from few runs on few problems, with failed API calls in some runs, and are reported to document problems found and adjustments made, not to establish effectiveness. The platform is deployed on Vercel and Render, with an LLM (by default Groq-hosted openai/gpt-oss-20b) generating the hints.

**Index Terms** — programming education, test case generation, feedback-driven iteration, True Positive Rate, True Negative Rate, Python, LLM-assisted learning, LeetCode

---

## I. Introduction

程式設計教育中，自動評分系統（Automated Grading System, AGS）的測試案例品質直接決定系統是否能正確區分「學生的程式是否真正理解了演算法」。現有平台（如 LeetCode、HackerRank）的測試案例多由工程師憑經驗設計，缺乏系統性指標衡量每筆測試案例的「鑑別度」（Discriminative Power）。

此問題在程式學習平台尤為關鍵：

1. **誤放（False Negative）**：錯誤程式碼通過了所有測試案例，導致學生誤以為自己理解了演算法。
2. **誤殺（False Positive）**：正確程式碼被錯誤判定為失敗，打擊學習信心。

本研究以 LeetCode #3（Longest Substring Without Repeating Characters）為主要觀察題目，設計並實作一個 Python 程式學習平台，把重心放在兩件事：（1）讓 AI 提示在構造上看不到學生程式碼；（2）把「測資好不好」變成可觀察的數字，並以 AI 協助補強測資。

**本研究的定位。** 這是一份提案加環境測試：我們提出做法、把環境搭起來並跑過，記錄過程中發現的問題與調整。我們**不**宣稱準度、效度或學習成效，也不以任何門檻判定成敗。文中的數字是環境測試的觀察，樣本少（少數題目、少數次執行）、部分由 AI 代替人工審核，只能當線索。具體內容如下：

- **提出並走通 feedback-driven 迭代測資流程。** 觀察到：在迭代期間使用的 6 個錯誤解（訓練池）上，TNR 由 0.491 升至 0.882；在迭代期間未參與評測的 3 個錯誤解（驗收池）上為 0.471。前者屬樣本內數字，兩者的落差本身就是一個發現（VI.E）。TPR = 1.0 由構造保證，只作一致性檢查。
- **設計 `combo_kill` 生成模式**，單一字串同時針對 4 種常見錯誤解。它在訓練池上帶來該輪最大的 TNR 增幅，但尚未在驗收池上單獨評估。
- **建立 pytest 品質守門員**，以 4 個自動化斷言確保測資集在維護時不退化。
- **整合 code-blind 的 LLM 提示系統**，並加上輸出端檢查；以 6 種已知錯誤各跑一次，確認自動檢查通過（只說明環境可運作，不代表提示有效）。
- **以第二題試跑 AI 協作補測資**（VI.F）：記錄了 AI 提案的指示調整、最難攔截的錯誤解，以及「看到分數再改」的少量觀察。

---

## II. Related Work

### A. 自動化測試案例生成

Shi et al. [1] 在 *CodeContests-O* 中提出 feedback-driven 迭代測資生成框架，以 LLM 為核心，依據前一輪的 TPR/TNR 回饋自動修改生成器命令。本研究在此框架下進行人工驅動的迭代，以確保可重現性並降低 API 成本。

Claessen and Hughes [2] 的 QuickCheck 奠定了基於屬性的測試生成基礎，強調以隨機輸入揭露程式缺陷。本研究的生成器（`gen.py`）繼承此精神，但針對特定演算法錯誤設計結構化生成策略。

### B. 程式設計學習平台

Ihantola et al. [3] 回顧了 Web-based 程式判題系統，指出測資覆蓋率與學習效果的正相關。Crow et al. [4] 進一步指出，對新手學習者提供「診斷性」（Diagnostic）而非「評斷性」（Summative）的回饋，能顯著提升學習動機。

### C. LLM 輔助程式教育

Phung et al. [5] 研究 GPT-4 在程式除錯輔助中的應用，發現引導式提示（不直接給出答案）比直接提供修正程式更能促進學習遷移。本平台的 AI 提示設計遵循此原則，明確在 prompt 中要求「不直接給出修正後程式碼」。

---

## III. System Architecture

### A. 整體架構

本平台採用前後端分離架構（圖 1）。後端只暴露三個端點：`GET /problems`（題目清單）、`GET /problems/{id}`（題目敘述、範例、限制條件與起始程式碼）、`POST /submit`（接收 `{code, problem_id}`，回傳 `{results, hint}`）。測資內容不會經由任何端點送到前端。

```
┌──────────────────────────────────────────────────────┐
│                   Frontend (Vue 3 + Vite)            │
│  題目下拉選單 ← GET /problems、/problems/{id}         │
│  Monaco Editor → CodeEditor.vue                      │
│  結果顯示   → ResultPanel.vue (到第一個 FAIL)         │
│  AI 提示    → ResultPanel.vue hint-section           │
└────────────────────┬─────────────────────────────────┘
                     │ POST /submit  { code, problem_id }
                     ▼
┌──────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                  │
│  main.py ──→ judge.py ──→ executor.py                │
│              (asyncio.gather)  (ThreadPoolExecutor   │
│                                 + subprocess)        │
│          └──→ ai.py ──→ LLM API（不接收學生程式碼）   │
│                 └──→ hint_guard.py（輸出端檢查）      │
└──────────────────────────────────────────────────────┘
```

**圖 1. 平台整體架構**

系統有兩條互相呼應的資訊限制：學生看不到測資（避免由測資反推題目的檢查重點），LLM 看不到學生程式碼（見 V.B）。

### B. 後端核心元件

| 元件 | 功能 |
|---|---|
| `main.py` | FastAPI；三個端點；`/submit` 先由 `judge.py` 跑完測資，再把結果交給 `ai.py` 產生提示（提示依賴測資結果，兩者為序列關係）；可選的提交紀錄器（環境變數開啟，預設關閉） |
| `problem.py` | `PROBLEMS` 登錄表；每題以 `method`、`ai_context`、`starter_code`、`test_cases` 等欄位描述，`judge` 與 `ai` 依 `problem_id` 取用，新增題目不需修改判題與提示邏輯 |
| `judge.py` | `asyncio.gather` 並行跑完該題**全部**測資，不因某筆失敗而中止（提早截斷只發生在前端顯示）；支援單參數 `input` 與多參數 `args` 兩種呼叫方式；數值比對允許 1e-6 浮點誤差 |
| `executor.py` | 學生程式碼的檢查與隔離執行，見 III.C |
| `ai.py` | 依錯誤類型組 prompt、呼叫 LLM，見第 V 章 |
| `hint_guard.py` | LLM 輸出的檢查，見 V.C |

目前登錄的題目如下。**只有 longest-substring 完成第 IV 章的量化迭代**；兩道人工設計題未經量化收斂；最後兩題僅有第 0 輪測資（官方範例），測資集尚未收斂。

| 題目 id | 難度 | 測資數 | 測資來源 |
|---|---|---|---|
| `longest-substring` | medium | 17 | 第 IV 章迭代（已收斂） |
| `valid-parentheses` | easy | 12 | 人工設計 |
| `median-two-sorted-arrays` | hard | 11 | 人工設計 |
| `best-time-stock` | easy | 2 | 第 0 輪（官方範例） |
| `longest-valid-parentheses` | hard | 3 | 第 0 輪（官方範例） |

### C. 程式碼執行安全機制

學生提交的程式碼依序經過三道處理：

1. **AST 匯入黑名單**：解析 AST，若出現對 `os`、`sys`、`subprocess`、`socket`、`multiprocessing`、`threading`、`ctypes`、`importlib` 這 8 個模組的 `import` 或 `from ... import` 即拒絕執行。
2. **語法預檢**：`compile()` 失敗時直接回傳含行號與位置指示的 SyntaxError 訊息，不啟動子程序。
3. **子程序執行**：程式經由 stdin 傳入 `python -`（避免命令列長度上限），一般測資 5 秒、壓力測資 10 秒逾時，逾時視為執行期錯誤；學生程式呼叫 `input()` 會立即得到 EOFError，不會卡到逾時。

**威脅模型與限制。** 這套機制的目標是防止不熟悉語言特性的學生「不小心」造成破壞，不是抵禦惡意輸入的沙盒。具體限制有二：（1）黑名單只檢查匯入陳述式，不涵蓋 `open()`、`eval()`、`exec()`、`__import__()` 等內建函式，動態匯入亦未攔截；（2）子程序與伺服器共用機器與檔案系統，沒有記憶體或 CPU 配額，逾時只限制時間，不限制資源。在使用者身分已知、規模為一個班級的前提下，此風險可接受；若開放給未知使用者，需改用容器隔離與資源限制，列為未來工作。

### D. 前端設計

前端使用 Vue 3 + Vite，以 Monaco Editor（VS Code 同款編輯器）提供 Python 語法高亮與自動縮排，頂端題目下拉選單標示難度（低／中／高）並在切換題目時重置程式碼與結果。ResultPanel 只顯示到第一個 FAIL，降低學生認知負擔；因此測資的排列順序決定了學生第一眼看到的失敗內容。整體採用 Warm Terminal 美學（深色底、amber accent），字型統一使用 IBM Plex Mono。

---

## IV. Test Case Generation Methodology

本章為本研究核心貢獻，描述 feedback-driven 迭代測資生成的完整流程。

### A. 品質指標定義

參考 CodeContests-O [1]，以正確解池 $S^+$、錯誤解池 $S^-$ 與測資集 $T$ 定義評估指標。令 $p(s)$ 為解法 $s$ 在 $T$ 上的通過率（通過的測資數 ÷ $|T|$）。

**True Positive Rate (TPR)**：正確解池的平均通過率。
$$\text{TPR} = \frac{1}{|S^+|}\sum_{s \in S^+} p(s)$$

TPR = 1.0 等價於每個正確解都通過全部測資，本研究以此為門檻。由於測資的 expected 由參考解計算（見 VII.B），TPR = 1.0 在構造上近乎必然成立，因此它是一致性檢查，而非衡量測資鑑別力的效果指標。

**True Negative Rate (TNR)**：錯誤解池的平均攔截率。
$$\text{TNR} = \frac{1}{|S^-|}\sum_{s \in S^-}\bigl(1 - p(s)\bigr) = 1 - \frac{\sum_{s \in S^-} \text{(s 通過的測資數)}}{|S^-| \times |T|}$$

TNR 衡量的是測資集的**攔截密度**：平均每個錯誤解被多少比例的測資攔下，而非「是否被攔下」。「是否被攔下」另以**漏網數**度量：
$$\text{Survivors} = \bigl|\{s \in S^- \mid p(s) = 1\}\bigr|$$
本研究在 baseline、v1–v3 與最終版的漏網數皆為 0（見 VI.A），因此各輪 TNR 的提升反映的是攔截密度增加，而不是錯誤解從「漏網」變成「被攔下」。

**訓練 TNR 與驗收 TNR**：將錯誤解分為迭代期間使用的訓練池 $S^-_{tr}$，以及迭代期間不參與評測的驗收池 $S^-_{ho}$。生成策略（如 combo_kill）是針對 $S^-_{tr}$ 的弱點設計的，因此在 $S^-_{tr}$ 上計算的 TNR 屬於樣本內（in-sample）數字；對未見錯誤的泛化程度，以同一公式在 $S^-_{ho}$ 上計算的**驗收 TNR** 衡量，且只在迭代結束後計算一次（結果見 VI.E）。

**設計目標：TPR = 1.0（不誤殺任何正解）、漏網數 = 0、訓練 TNR ≥ 0.85。** 驗收 TNR 僅回報，不設門檻。TNR ≥ 0.85 為研究者設定的經驗門檻，並非由資料推導，只用於品質守門員的自動檢查，不作為本研究的成功標準。另外，TNR 不可能超過「單一輸入最多能同時攔下的錯誤解比例」（TNR 上限，以窮舉小輸入加隨機輸入估計）；對上限小於 1 的題目，品質守門員改用達成率（TNR ÷ 上限），報告時並列絕對 TNR。

### B. 解池設計（S+ / S-）

**S+（正確解池，3 個）：**

| 解法 | 策略 | 時間複雜度 |
|---|---|---|
| `sliding_window.py` | Set 維護當前視窗 | O(n) |
| `hash_map.py` | Dict 紀錄最後出現位置 | O(n) |
| `brute_force.py` | 雙層迴圈暴力枚舉 | O(n²) |

**S-（錯誤解池，6 種 bug pattern）：**

| 錯誤解 | Bug 描述 | 代表程式碼 |
|---|---|---|
| `always_len.py` | 直接回傳字串長度 | `return len(s)` |
| `count_unique.py` | 回傳不重複字元數（誤讀題意） | `return len(set(s))` |
| `off_by_one_window.py` | 視窗長度差一（缺少 +1） | `best = right - left` |
| `no_reset_left.py` | 遇重複時 left 指針不正確重置 | `left = right` |
| `inner_return.py` | 內層迴圈提早 return | `if ch in seen: return best` |
| `no_return.py` | 演算法正確但無 return 語句 | （缺少 return） |

**S+/S- 池的擴充機制：AI 提案 + 客觀評測 + 裁決（環境測試中）**

上述 S+/S- 池目前僅涵蓋 Longest Substring 一題，且完全由研究者手動設計——這是本方法論目前最主要的可擴展性瓶頸：每推廣到一道新題目，都需要研究者重新從零構思「初學者可能犯下哪些理解錯誤」，無法隨題目數量線性擴充。

本研究提出一套半自動化的擴充機制（環境中的提案、評測、審核流程已在第二題跑通，見 VI.F；審核目前由 AI 代替人工）：由 LLM 根據題目敘述與參考正解，提議候選錯誤解法與對應的攻擊測資，並附上理由說明每個候選鎖定哪一種典型錯誤；候選隨後交由既有的評測工具 `run_eval.py` 對 S+/S- 池執行，取得客觀的 TPR/TNR 影響數據，依結果分三級裁決：候選若導致任何 S+ 正解的 TPR 低於 1.0，自動拒絕；候選若維持 TPR = 1.0 且確實提升 TNR，自動採用；僅當 TPR = 1.0 但 TNR 提升不明確（與既有測資鑑別度重疊）時，才交付研究者依 AI 提供的理由判斷該測資在教學情境下是否合理。

此設計呼應 Wang et al. [9] 提出的「LLM 產生＋驗證器評分＋低分案例轉人工」協作架構——`run_eval.py` 恰好扮演該架構中「驗證器」的角色，不需額外開發。同時，為避免 Lane et al. [10] 指出的「敘事式解釋會誘使評估者過度服從 AI 建議、尤其是拒絕類建議，進而讓敘事取代獨立驗證」這項風險，裁決介面刻意將 `run_eval.py` 算出的客觀數據置於 AI 理由之前呈現；AI 理由僅用於協助判斷「教學情境是否合理」這類本就沒有客觀答案的問題，不介入 TPR/TNR 這類已有客觀判準的裁決。目前的狀態是：提案程式（`testgen/propose.py`）、輪次評測與審核紀錄已可運作，審核者由 AI 代替人工、紀錄標註為測試階段；真正的人工裁決尚未進行，同一輪內「看到分數再改」只是實驗腳本，尚未納入程式庫（見 VI.F、Section VIII）。

### C. 生成器設計（gen.py）

`gen.py` 實作 12 個生成模式（Mode），每個模式為一個 Python 函式，接收參數後產生一個字串輸入：

| Mode | 設計目的 | 範例輸出 |
|---|---|---|
| `random` | 隨機字母字串 | `beebcedfeaeadcebbfde` |
| `doubled_distinct` | 每個字母出現兩次（`aabbccdd...`） | `aabbccddeeff` |
| `carry_kill` | XYXZ pattern（攻擊 no_reset_left） | `gogn`, `qmjqztg` |
| `combo_kill` | doubled 前綴 + XYZX 中段 + 長 distinct 尾段 | `mmiictscxgyvo` |
| `late_window` | 最長視窗出現在字串末段 | — |
| `stress_same` | 超長相同字元（壓力測試） | `"a" × 50000` |
| ... | 其他 6 個輔助模式（all_same、no_repeat、abba_chain、alternating、punctuation、stress_random） | — |

`synthesize.py` 讀取命令清單（`commands_v{N}.txt`），呼叫對應生成函式並以 reference solution 計算 expected，輸出 `tests_v{N}.py`。

### D. 迭代流程

```
┌─────────────────────────────────────────────────────┐
│  初始：commands_v{N}.txt                            │
└──────────────────┬──────────────────────────────────┘
                   ↓
         synthesize.py
         （命令 → tests_v{N}.py）
                   ↓
          run_eval.py
     （計算 TPR / TNR / per-bug 通過率）
                   ↓
        feedback_v{N}.json
    （command_value + S- pass_rates + survivors）
                   ↓
       人工分析回饋 → 修改 commands_v{N+1}.txt
       或新增 gen.py mode
                   ↓
              （下一輪）
```

`feedback_v{N}.json` 記錄：
- 每個命令產出測資的鑑別度（打掉幾個 S-）
- 每個 S- 的通過率（越高代表該 bug 越容易漏網）
- 仍然漏網的 S-（survivors）

### E. 四輪迭代詳述

**Baseline（18 筆，TNR=0.491）**

初始測資由開發者經驗設計，包含 LC 官方範例、邊界值（空字串、單字元）、特殊字元等。評估發現：
- `count_unique`：**94.4% 通過率**（17/18 測資讓其過）
- `no_reset_left`：88.9% 通過率
- 8 筆測資（44%）實際鑑別度只有 1-2/6，屬低價值

**v1（15 筆，TNR=0.689，+20 ppt）**

策略：砍掉 8 筆低價值（空字串、單字元、純標點），加入 `doubled_distinct`、`abba_chain`、`late_window`。測資從 18 筆降至 15 筆，TNR 大幅提升。

**v2（16 筆，TNR=0.729，+4 ppt）**

分析發現：真正攔截 `no_reset_left` 的不是 `abba`（index 12）而是 `dvdf`（index 9）。`dvdf` 符合 XYXZ pattern（第一個字母在第三位重現）。設計 `carry_kill` 模式實作此 pattern 的參數化版本，取代效果不佳的 `abba_chain`。`no_reset_left` 通過率從 87% 降至 63%。

**v3（17 筆，TNR=0.745，+1.5 ppt）**

加大 `doubled_distinct` 比例，希望壓制 `count_unique`（其計算 `len(set(s))` 在 doubled 字串上會算出實際 distinct 數而非答案）。但效果適得其反：大量相似結構的 doubled 字串稀釋了其他 bug 的覆蓋，導致整體 TNR 幾乎停滯。

**v4（17 筆，TNR=0.882，+13 ppt）**

**突破口：`combo_kill` 模式。**

策略轉向：設計能「同時攻擊多個 bug」的字串，而非各自針對單一 bug 的字串。`combo_kill` 字串結構如下：

```
前段：doubled 前綴（如 mm ii cc）
      → 攻擊 count_unique（set 大小 ≠ 答案）
中段：XYZX carry 片段（如 tsc xgYvo）
      → 攻擊 no_reset_left（left 不應跳至 right）
後段：長 distinct 尾段（如 gyvo）
      → 攻擊 inner_return（不能提早 return）
         攻擊 always_len（長度 ≠ 答案）
```

v4 中 10 個 `combo_kill` 案例全部拿到 **6/6** 鑑別度，單輪 TNR 提升 +13 個百分點。

### F. 最終測資集（problem.py，17 筆）

| Index | 輸入字串 | 期望答案 | 來源 | 鑑別度 |
|---|---|---|---|---|
| 1 | `abcabcbb` | 3 | LC 官方範例 | 3/6 |
| 2 | `bbbbb` | 1 | LC 官方範例 | 3/6 |
| 3 | `pwwkew` | 3 | LC 官方範例 | 3/6 |
| 4 | `gogn` | 3 | carry_kill | 5/6 |
| 5 | `qmjqztg` | 6 | carry_kill | 5/6 |
| 6 | `zuxtzrhmqc` | 9 | carry_kill | 5/6 |
| 7 | `aabbccddeeff` | 2 | doubled_distinct | 5/6 |
| 8 | `mmiictscxgyvo` | 8 | combo_kill | **6/6** |
| 9 | `ttdduuycnysbaleg` | 9 | combo_kill | **6/6** |
| 10 | `rroouumszmdgjakhwc` | 11 | combo_kill | **6/6** |
| 11 | `hhjjiinnyduyskmrec` | 9 | combo_kill | **6/6** |
| 12 | `beebcedfeaeadcebbfde` | 5 | random | **6/6** |
| 13 | `aabbccddeeffgghhiijj` | 2 | doubled_distinct | 5/6 |
| 14 | `ffbbuuccgqzgwisanldxtk` | 13 | combo_kill | **6/6** |
| 15 | `ddrrsskkhhbtxbanquoiym` | 11 | combo_kill | **6/6** |
| 16 | `wwzzooueyudmficvgrxnjp` | 15 | combo_kill | **6/6** |
| 17 | `qqccffzzkkidaiwntpherjlm` | 13 | combo_kill | **6/6** |

---

## V. AI 提示系統

### A. 錯誤類型分類

`executor.py` 將每筆測資的執行結果分為四類 `error_type`：

| error_type | 觸發條件 | 判斷方式 |
|---|---|---|
| `syntax_error` | 語法錯誤，無法執行 | `compile()` 前置檢查，或子程序 stderr 含 SyntaxError |
| `runtime_error` | 執行時例外、逾時，或使用被禁止的模組 | 子程序 returncode ≠ 0、逾時，或 AST 黑名單命中 |
| `no_return` | 函式沒有回傳值 | stdout 為 `None` 或空 |
| `None`（wrong_answer） | 執行正常但答案錯 | 輸出與預期不符（`ast.literal_eval` 還原後比對，數值允許 1e-6 誤差） |

`build_prompt` 以**第一筆失敗測資**的 `error_type` 決定使用哪個分支。

### B. Code-blind 的 Prompt 設計

提示產生函式 `build_prompt(results, problem_title, problem_context)` 的簽名中**沒有學生程式碼這個參數**：LLM 只會收到題目名稱與題意、測資的 input／expected／actual，以及錯誤訊息。這是 by-construction 的保證——模型在構造上拿不到程式碼，因此不是靠指令要求它「不要洩漏」。四個分支如下：

| 分支 | 傳入內容 | 指令重點 | 字數上限 |
|---|---|---|---|
| `syntax_error` | 題目名稱、stderr | 一句話白話解釋錯誤、指向行號、以一個問題引導；不給修正後程式碼 | 120 |
| `runtime_error` | 題目名稱與題意、觸發錯誤的輸入、stderr | 解釋錯誤、引導看行號、詢問「這個輸入有什麼特別」；不給修正後程式碼 | 150 |
| `no_return` | 題目名稱 | 說明 return 的作用，並問答案存在哪個變數、有沒有被回傳；不直接說怎麼改 | 100 |
| `wrong_answer` | 題目名稱與題意、**全部**失敗案例的 input／expected／actual | 先歸納失敗的數值 pattern（不輸出分析），再用一個蘇格拉底式問題引導；不給正確程式碼或完整演算法步驟；結尾必須是問句 | 200 |

輸出為純文字，不含結構化格式。**代價**：提示只能依失敗案例的數值 pattern 推斷理解落差，無法指出程式碼中具體哪一行有問題（語法與執行期錯誤例外，因 stderr 含行號）。

### C. 輸出端安全網

LLM 不保證遵守「不要給程式碼」的指令，因此在 `get_hint()` 回傳前再經 `hint_guard.guard()` 檢查：提示含程式碼區塊標記、`def ...(` 函式定義、`class Solution`，或沒有任何問句時，以固定的替代文字取代原提示，並記錄警告。我們選擇「整句替換」而非局部塗黑，因為提示是自然語言敘述，逐詞塗黑會讀不通順。**限制**：這是針對明顯洩漏的啟發式檢查；以文字描述完整演算法步驟的提示不會被攔下，這類情形仍只能靠 V.B 的 prompt 規則約束。

### D. 輸入截斷保護

失敗案例的輸入與實際輸出超過 50 字元時，在組 prompt 前截斷並加上 `...`，避免壓力測資（如 50,000 字元的字串）使 prompt 過大而觸發 API 錯誤。

### E. 模型選擇與失敗處理

LLM 供應商於服務啟動時由環境變數決定：預設為 Groq 的 `openai/gpt-oss-20b`，設定 `GEMINI_API_KEY` 時改用 `gemini-2.0-flash`。這是部署時的靜態選擇，不是執行期的自動切換；呼叫失敗時 `get_hint()` 回傳 `None` 並在伺服器記錄警告。全部測資通過時同樣回傳 `None`，前端目前無法區分這兩種情況。

### F. 設計演進

早期版本曾把完整程式碼交給 LLM，並要求回傳結構化的 JSON 診斷選項（`{intro, options}`），以三層容錯解析處理格式錯誤。實測發現該設計會讓提示洩漏修正後的程式碼片段，且 JSON 解析增加脆弱性，因此改為現行的 code-blind 純文字設計。

---

## VI. Environment Test Observations

本章記錄環境測試中觀察到的數字與現象。每個版本只跑一次、沒有重複，也沒有統計檢定；題目只有一到兩題；錯誤解池由研究者手寫。因此這些數字只描述「這套流程跑起來是什麼樣子」，不構成對準度或效度的主張。

### A. 各輪迭代結果

**表 1. 四輪迭代 TPR/TNR 摘要**

| 版本 | 測資數 | TPR | TNR | 改動策略 | TNR 累積進步 |
|---|---|---|---|---|---|
| Baseline | 18 | 1.0000 | 0.4907 | 經驗設計 | — |
| v1 | 15 | 1.0000 | 0.6889 | 砍低價值 + KILLER 模式 | +19.8 ppt |
| v2 | 16 | 1.0000 | 0.7292 | carry_kill（XYXZ pattern） | +23.9 ppt |
| v3 | 17 | 1.0000 | 0.7451 | 大量 doubled_distinct | +25.4 ppt |
| **v4** | **17** | **1.0000** | **0.8725** | **combo_kill（同殺 4 bug）** | **+38.2 ppt** |
| **最終** | **17** | **1.0000** | **0.8824** | 加回 LC 官方範例 | **+39.1 ppt** |

表 1 的 TNR 皆為訓練池（6 個錯誤解）上的樣本內數字，且漏網數在 baseline、v1–v3 與最終版皆為 0。換言之，baseline 的 0.4907 並非「有錯誤解沒被抓到」，而是每個錯誤解被攔下的測資比例偏低；對未見錯誤的表現見 VI.E。TPR = 1.0 為構造保證下的一致性檢查（見 IV.A、VII.B），不視為實驗成果。

### B. 各 Bug Pattern 攔截率改善

**表 2. 各 S- 錯誤解通過率（越低代表被攔截得越好）**

| Bug Pattern | Baseline 通過率 | v4 通過率 | 絕對改善 | 相對改善 |
|---|---|---|---|---|
| `always_len` | 44.44% | **0.00%** | -44.44 ppt | ∞ |
| `count_unique` | 94.44% | 35.29% | -59.15 ppt | **-62.6%** |
| `inner_return` | 72.22% | 11.76% | -60.46 ppt | **-83.7%** |
| `no_reset_left` | 88.89% | 29.41% | -59.48 ppt | **-66.9%** |
| `off_by_one_window` | 5.56% | **0.00%** | -5.56 ppt | ∞ |
| `no_return` | **0.00%** | **0.00%** | 0 | 維持 |

表 2 的 v4 欄為 v4 測資集（TNR 0.8725）；最終測資集（TNR 0.8824）僅 `count_unique` 不同，為 29.41%，其餘相同。

### C. 測資鑑別度分佈

**表 3. 最終 17 筆測資的鑑別度分佈**

| 鑑別度等級 | 筆數 | 佔比 | 說明 |
|---|---|---|---|
| 6/6（最高） | 9 筆 | 52.9% | 全部為 combo_kill 或 random |
| 5/6（高） | 5 筆 | 29.4% | carry_kill + doubled_distinct |
| 3/6（中） | 3 筆 | 17.6% | LC 官方範例（保留做學生熱身） |
| 1-2/6（低） | 0 筆 | 0% | 全部已砍除 |

相比 baseline，低價值測資（≤ 2/6）從 8 筆（44.4%）降至 **0 筆（0%）**。

### D. 品質守門員（Pytest）實測

```
=== 對舊版 problem.py（baseline）===
PASS  test_tpr_equals_one           TPR=1.0000
FAIL  test_tnr_above_threshold      TNR=0.4907 < 0.85（正確攔截）
PASS  test_every_bug_caught_at_least_once
PASS  test_minimum_test_case_count

=== 對新版 problem.py（v4 導出）===
PASS  test_tpr_equals_one           TPR=1.0000
PASS  test_tnr_above_threshold      TNR=0.8824 >= 0.85（放行）
PASS  test_every_bug_caught_at_least_once
PASS  test_minimum_test_case_count
```

守門員正確區分舊版（應擋）與新版（應通過）。

### E. 驗收池評測與指標解讀

**驗收池。** 迭代結束後，以三個迭代期間不參與評測的錯誤解對最終 17 筆測資評測一次：`if_not_while`（遇重複字元時只移除視窗最左一個字元，用 if 而非 while）、`no_max_left`（更新 left 時沒取 max，left 會往回跳，即經典的 "abba" 錯誤）、`update_only_on_dup`（只在遇到重複字元時才更新答案，漏掉最後一個視窗）。

**表 4. 最終測資集：訓練池與驗收池**

| 評測池 | 錯誤解數 | TPR | TNR | 漏網數 |
|---|---|---|---|---|
| 訓練池 | 6 | 1.0000 | 0.8824 | 0 |
| 驗收池 | 3 | 1.0000 | **0.4706** | 0 |

**表 5. 驗收池各錯誤解的表現**

| 錯誤解 | 通過率 | 被幾筆測資攔下 |
|---|---|---|
| `if_not_while` | 29.41% | 12 / 17 |
| `no_max_left` | 94.12% | **1 / 17** |
| `update_only_on_dup` | 35.29% | 11 / 17 |

驗收 TNR 為 0.4706，比訓練 TNR（0.8824）低 0.4118。三個驗收錯誤解各自仍被至少一筆測資攔下（漏網數 0），但 `no_max_left` 只被 17 筆中的 1 筆攔下：攔得到，但很薄。因此 0.8824 應解讀為測資集對訓練池的擬合程度，而非對一般初學者錯誤的鑑別力；這與 VII.D 所述的泛化性限制一致。

**訓練 TNR 的組成。** 訓練池中 `always_len`、`no_return`、`off_by_one_window` 在最終測資集上的通過率皆為 0%（17 筆全部攔下），三者合計貢獻了 6 個錯誤解攔截率總和（約 5.29）中的 3.00，超過一半。其餘三個（`count_unique`、`inner_return`、`no_reset_left`）的平均攔截率為 0.7647。換言之，訓練 TNR 有相當比例來自對最容易攔下的錯誤解的滿分。

**限制。** 驗收池只有 3 個錯誤解，每個錯誤解最多使驗收 TNR 變動約 0.33，數字本身變異很大；驗收池同樣為人工撰寫的單一錯誤程式，與訓練池來源類型相同，無法排除共同盲點。本節結果應視為方向性證據，而非精確估計。

### F. AI 協作補強測資的環境測試（第二題）

**設定。** 題目為 Longest Valid Parentheses（LeetCode #32），6 個訓練用錯誤解、3 個驗收用錯誤解（本節全程未動用驗收池）。第 0 輪（官方範例）3 筆測資的 TNR 為 0.2778；該題單一輸入最多可同時攔下全部 6 個錯誤解（上限 1.0）。流程為：AI 依題目與參考解提出候選輸入 → 評測工具在訓練池上計分 → 審核者挑選 → 下一輪。審核者目前是 AI（貪婪法，只依 TPR/TNR 數字選入，不看 AI 附的理由），紀錄標註為測試階段；非人工審核。

**觀察一：給 AI 的指示寫法會改變候選的品質。** 第 2 輪在第一版指示下只重跑一次，候選的 TNR 為 0.405；改寫指示（附上各既有測資各攔下幾種錯誤，並要求新候選超過目前的種類數）後為 0.532，12 筆候選全部攔到至少一個錯誤解。這是各一次執行的結果，無法分開「指示的影響」與「取樣的隨機性」。第 2 輪保留 14 筆測資，訓練池 TNR 為 0.5476。

**觀察二：有一個錯誤解（`left_scan_only`）始終攔不到。** 在改寫後的指示下，單次提案與 46 筆的大量取樣共 69 筆候選，沒有任何一筆攔下它。

**觀察三：同一輪內讓 AI 看到分數後再提，是唯一碰得到該錯誤解的條件。**
- 第一組：5 次獨立試驗，每次最多 4 個內層回合，其中 1 次因 API 回傳空內容而無資料（4 次有效）。有效試驗中，第 1 回合 0/44 筆候選攔下該錯誤解，之後回合合計 16/118 筆；貪婪挑選後 TNR 為 0.617–0.655（基準 0.5476），該錯誤解的通過率 0.724–0.885（基準 0.857），僅 2 次明顯下降；沒有任何單筆候選攔下全部 6 個錯誤解。不同試驗之間差異很大（某次一個回合出現 6 筆，其餘多為 0–2 筆）。
- 第二組（固定測資數的對照）：為確認 TNR 上升是否只是測資變多，固定在 14 筆之上加入 10 筆（共 24 筆），比較「看到分數再提」與「不看分數、重抽同一份指示」。5 次中有 2 次因 API 連續失敗（47 次錯誤）而無資料，只有 3 次有效。兩組整體 TNR 接近（貪婪挑選：0.618／0.646／0.646 對 0.583／0.632／0.632；隨機挑 10 筆：約 0.55–0.58 對 0.54–0.58）；但攔下該錯誤解的候選，看到分數的組為 23/98，不看分數的組為 0/93。

**怎麼解讀。** 在這些少量執行中，整體 TNR 的上升看起來主要來自「挑選」（優先選能同時攔下多種錯誤的測資），而非回饋本身；回饋似乎只對最難的那個錯誤解有幫助。但有效試驗只有 3–4 次、失敗的呼叫沒有補跑，回合間波動大，這個差異可能受隨機性影響，不應視為已確認。最好的一次整體 TNR 約 0.65，仍遠低於我們設定的守門員門檻 0.85，且該題目前仍有一個錯誤解的通過率偏高。

**其他需要說明的事。** （1）審核者是 AI，可能與提案者有相同的盲點；（2）密度式 TNR 會因測資數量與組成而改變，因此才做固定數量的對照；（3）本節的原始輸出目前保存在工作目錄之外，尚未納入版本庫；（4）候選的 AI 理由在審核時刻意不看，但提案程式在列出被拒絕的候選時曾有一次顯示出理由片段，已記錄為流程上的小疏失。

---

## VII. Discussion

### A. combo_kill 的設計洞察

v3 的停滯揭示了一個根本問題：針對單一 bug 設計的測資，在組合時容易相互稀釋。例如，大量 doubled 字串雖能攔截 `count_unique`，但其輸入結構對 `no_reset_left` 沒有額外壓力。

`combo_kill` 的設計哲學是「結構化的多目標字串」：在一個字串中安排多個子結構，每個子結構針對一種 bug 的致命弱點。此設計與 Mutation Testing 中的「Strongly Killing Test」概念相通——一個測試應盡可能殺死多個 mutant。

### B. TPR 始終維持 1.0 的設計保障

測資集的 expected 值由 reference solution（`sliding_window.py`）自動計算，而非手動填入。這從根本上消除了「expected 值設錯導致誤殺正解」的風險。只要 reference solution 正確（已由 LeetCode 官方驗證），TPR 就不會因測資生成而受損。

### C. 人工 vs 自動化迭代的取捨

本研究採用人工分析回饋、手動修改命令清單的方式，而非 CodeContests-O [1] 中 LLM 自動修改生成器。優點是：
- 每一次修改都有明確的分析依據，可重現
- 不依賴 LLM API，成本為零
- 過程本身就是研究素材（可直接引用在報告中）

缺點是：人工分析限制了迭代速度，且分析者的偏見可能影響方向。在 v3 → v4 的轉折點，若有自動化的「survivor analysis → generator modification」pipeline，可能更快找到 combo_kill 策略。

### D. 測資集的泛化性限制

目前 S- 池只有 6 種 bug pattern，實際學生的 bug 種類更多。此設計的應對方式是**開放式的 S- 池擴充機制**：發現新 bug 後，加入 `solutions_wrong/` 目錄，品質守門員即自動偵測是否需要補充測資。

---

## VIII. Conclusion

本研究提出一個 Python 程式學習平台的設計，並以環境測試走通其兩個部分：看不到學生程式碼的 LLM 提示（含輸出端檢查），以及以 TNR 為觀察指標的迭代測資構造流程。這是提案與環境測試，**不是**對準度、效度或學習成效的評估。環境測試中的觀察如下：

1. **流程可以跑通。** 在 LeetCode #3 上，人工驅動的四輪迭代使訓練池 TNR 由 0.491 升至 0.882；但在迭代期間未使用的 3 個驗收錯誤解上為 0.471（每個仍被至少一筆測資攔下，但密度低，`no_max_left` 只被 17 筆中的 1 筆攔下）。這顯示 0.882 屬樣本內數字，也促成我們在流程中固定保留驗收池。
2. **`combo_kill` 是一個值得記錄的設計想法**：在訓練池上它是單輪最大的增幅（約 +13 個百分點），但其效果尚未在驗收池上單獨評估。
3. **AI 協作補測資的流程在第二題跑通**，並看到兩件事：給 AI 的指示寫法會影響候選；有一個錯誤解在沒有分數回饋的條件下始終攔不到，而在回饋條件下偶爾可以。後者只有 3–4 次有效試驗，波動大，且審核者是 AI，只能當作線索。
4. **TPR = 1.0 由構造保證**，作為一致性檢查，不計入成果。**Pytest 守門員**用於在維護時避免測資退化。
5. **LLM 提示**依 error_type 分支，以引導式問句為主；以 6 種已知錯誤各跑一次，自動檢查通過，這只說明環境可運作，並不代表提示對學習有效，提示方向是否貼近錯誤根因仍需人工複查。

**限制。** 主要觀察來自 1–2 題、人工撰寫的小型錯誤解池（訓練 6 個、驗收 3 個）；AI 協作部分的審核者是 AI；部分執行因 API 失敗而缺資料；沒有重複與統計檢定；沒有使用者研究。

**接下來。** 短期：改由人工進行審核並補做更多次觀察、把同一輪內「看到分數再改」的做法納入程式庫、擴大並獨立建置驗收池（含真實學生提交）。延伸方向（暫不實作）包括：提示無效時逐階升級——前幾階仍不給學生程式碼，之後給偽代碼骨架，最後把標準答案的關鍵語法挖空讓學生填寫，可參考多層級提示的設計 [11] 與不給解答的助教設計 [12]；以及將流程擴充到更多題目，並與跨題目的測資評測基準 [13] 對照。上述皆未實作，也未評估。

---

## References

[1] J. Cai, J. Zhu, R. Sun, K. Zhao, D. Xue, M. Feng, W. Zhou, and H. Li, "CodeContests-O: Powering LLMs via Feedback-Driven Iterative Test Case Generation," *arXiv preprint arXiv:2601.13682*, 2026.

[2] K. Claessen and J. Hughes, "QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs," *ACM SIGPLAN Notices*, vol. 35, no. 9, pp. 268–279, 2000.

[3] P. Ihantola, T. Ahoniemi, V. Karavirta, and O. Seppälä, "Review of Recent Systems for Automatic Assessment of Programming Assignments," in *Proc. 10th Koli Calling International Conference on Computing Education Research*, 2010, pp. 86–93.

[4] T. Crow, A. Luxton-Reilly, and B. Wünsche, "Intelligent Tutoring Systems for Programming Education: A Systematic Review," in *Proc. ACM Conference on Innovation and Technology in Computer Science Education*, 2018, pp. 53–58.

[5] T. Phung, V.-A. Pădurean, J. Cambronero, S. Gulwani, T. Kohn, R. Majumdar, A. Singla, and G. Soares, "Generative AI for Programming Education: Benchmarking ChatGPT, GPT-4, and Human Tutors," in *Proc. ACM Conference on International Computing Education Research (ICER)*, 2023.

[6] A. Vaswani et al., "Attention Is All You Need," in *Advances in Neural Information Processing Systems (NeurIPS)*, 2017, pp. 5998–6008.

[7] M. Chen et al., "Evaluating Large Language Models Trained on Code," *arXiv preprint arXiv:2107.03374*, 2021.

[8] Z. Austin et al., "Program Synthesis with Large Language Models," *arXiv preprint arXiv:2108.07732*, 2021.

[9] X. Wang, H. Kim, S. Rahman, K. Mitra, and Z. Miao, "Human-LLM Collaborative Annotation Through Effective Verification of LLM Labels," in *Proc. CHI Conference on Human Factors in Computing Systems (CHI '24)*, 2024, pp. 1–21.

[10] J. N. Lane, L. Boussioux, C. Ayoubi, Y. H. Chen, C. Lin, R. Spens, P. Wagh, and P.-H. Wang, "The Narrative AI Advantage? A Field Experiment on AI-Augmented Evaluations of Early-Stage Innovations," *Harvard Business School Working Paper*, no. 25-001, 2024.

[11] R. Xiao, X. Hou, and J. Stamper, "Exploring How Multiple Levels of GPT-Generated Programming Hints Support or Disappoint Novices," *arXiv preprint arXiv:2404.02213*, 2024.

[12] M. Kazemitabaar et al., "CodeAid: Evaluating a Classroom Deployment of an LLM-based Programming Assistant that Balances Student and Educator Needs," *arXiv preprint arXiv:2401.11314*, 2024.

[13] Z. Yang, Z. Kuang, X. Xia, and Y. Zhao, "Can LLMs Generate High-Quality Test Cases for Algorithm Problems? TestCase-Eval: A Systematic Evaluation of Fault Coverage and Exposure," in *Proc. Annual Meeting of the Association for Computational Linguistics (ACL)*, 2025 (arXiv:2506.12278).

---

## Appendix A：測資生成器主要模式說明

### A.1 carry_kill 模式

針對 `no_reset_left` bug 設計。`no_reset_left` 的邏輯是遇到重複字元後直接 `left = right`（左指針跳到右指針），而非從 map 中找重複字元的上一個位置。

XYXZ pattern 的攻擊原理：
```
字串：g o g n
index：0 1 2 3
```
當遇到 index=2 的 `g` 時，正確解應將 `left` 移到 index=1（上一個 `g` 之後）。
`no_reset_left` 錯誤地將 `left` 跳到 `right=2`，導致後續計算 `best = right - left + 1 = 1`，而非正確的 3。

### A.2 combo_kill 模式

字串 `mmiictscxgyvo`（index=8，expected=8）的結構分解：

```
mm ii cc  → doubled 前綴（攻擊 count_unique）
t sc x    → 可選 carry 片段（攻擊 no_reset_left）
g y v o   → 4 個不同字母尾段（確保答案 = 尾段長度，攻擊 always_len / inner_return）
```

此字串讓所有 6 種錯誤解都輸出錯誤答案，因此鑑別度為 6/6。

---

## Appendix B：平台部署資訊

| 服務 | 平台 | URL |
|---|---|---|
| 前端 | Vercel | https://python-learning-platform-chi.vercel.app/ |
| 後端 | Render | https://python-learning-platform-88vh.onrender.com |
| 原始碼 | GitHub | https://github.com/yaoyao218/python-learning-platform |

---

*本論文字數約 6,000 字（含程式碼片段與表格）。IEEE 雙欄格式建議排版為 6-8 頁。*
