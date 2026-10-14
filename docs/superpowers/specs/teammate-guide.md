# 組員指南：實作與使用者說明

## 一頁摘要
- **最終目的**：把**三題**（`longest-substring`、`best-time-stock`、`longest-valid-parentheses`）的測試案例做好，並能在平台上使用，**下次就能給使用者實測**。
- **怎麼做**：用已經決定好的方法把它做出來，不是重新設計方法。
- **分兩類任務**：【主線】= 下次實測前一定要完成；【強化】= 讓流程更完整，**不阻擋實測**，有空再做。
- **遇到問題**：不要自己換方法，照第 4 節處理並寫進第 5 節的問題紀錄，然後繼續其他任務。
- **先讀什麼**：本指南 → 設計文件的「總整理」→ 你那條線的附錄章節。
- **2026-10-13 起的方向**：**拿掉人工審核**。測資審核一律由 `testgen/auto_review.py` 依評測數字自動進行；三題測資的迭代**先以「流程能否運行」為主**，一個指令 `python -m testgen.pipeline` 就能跑完。計畫文件第八節有完整說明與結果。

## 最終目的與完成定義

### 三題現在的狀態
| 題目 | `problem.py` 現有測資 | 現況 | 主線要做的事 |
|---|---|---|---|
| `longest-substring` | 18 道（人工迭代 17 道 + 5 萬字元壓力測資） | 已收斂，品質守門員通過；訓練池 TNR 0.889，驗收池 0.47 | 完成（E1） |
| `best-time-stock` | 10 道（r3 的 4 道 + 實驗外補強 6 道） | 未收斂；實驗紀錄：達成率 0.70、驗收池漏 1 種（K13）。補強後訓練池、驗收池都無漏網 | 完成（E2、E5） |
| `longest-valid-parentheses` | 54 道 | 未收斂（達成率 0.68）；6 種錯誤都擋到；驗收池 0.537、無漏網 | 完成（E3） |

### 什麼叫「做好、可以使用」
**可實測（必須達到，三題都要）**
1. 所有寫對的程式（S+）全部通過（TPR = 1.0）。
2. 每一個寫錯的程式（訓練池 S-）至少被一道測資擋下（沒有漏網）。
3. 測資順序：官方範例在最前面，其餘非壓力測資依輸入長度由短到長，壓力測資在最後（學生看到的「第一個失敗」要有教學意義）。
4. 已寫入 `backend/problem.py`，`python -m pytest -s -q` 全過。
5. 已附上通過往返檢查的虛擬碼（B2），平台能顯示並提供給 AI 提示（C2、C1）。
6. 使用者說明已備好（C3）；同意說明由負責人向老師或系辦確認。

**達標（盡量達到，達不到就如實記錄）**：訓練池達成率（TNR ÷ 天花板）≥ 0.85，並把該題在 `registry` 標為收斂，讓品質守門員（`tests/test_problem_quality.py`）啟用並通過。
- 目前未收斂的兩題在 pytest 中有 **8 個測試被略過（skipped）**；兩題都收斂後，這 8 個會變成實際執行。這是很好的進度指標：`8 skipped` → `0 skipped`。
- 做不到達標也可以進行實測：以「可實測」交付，在問題紀錄註明沒有達標的原因（例如 `left_scan_only`）。**不要為了達標而改門檻或改方法。**

### 下次實測前的檢查清單
- [x] E1、E2、E3、E4、E6 完成（三題測資定稿並寫入 `problem.py`；全自動流程可運行）
- [x] E5 完成（best-time-stock 補到 10 道，擋下 `global_min_then_max`）
- [ ] B2 完成（三題虛擬碼）
- [ ] C1、C2 完成（提示看得到虛擬碼、題目頁顯示虛擬碼）
- [ ] C3 完成（同意說明：負責人已確認同意，2026-10-13；草稿中【待確認】欄位的實際內容仍待負責人填入）
- [ ] 記錄方式已決定（預設：不記錄程式碼）
- [ ] 後端測試全過
- [ ] M1 完成（分支同步 main、開 PR、預覽網址實測過），再合併到 main 上線

---

## 1. 專案一句話
讓 AI 只「提示」不「代寫」；為此需要好的測資。我們用「寫對的程式」和「常見寫錯的程式」當尺來量測資好不好，並讓 AI 協助建池、補測資。給其他人測試時，每人會拿到一份驗證過的虛擬碼，直接操作測試案例與 AI 回饋。

本專題是**提案＋環境測試**，不做準度與效度驗證。文件與程式裡不要寫「準確」「有效」「證明」這類結論，請寫「觀察到」並註明樣本數。

## 2. 要讀的文件（依序）
| 文件 | 內容 | 時間 |
|---|---|---|
| 本指南 | 任務、規則、進度表 | 10 分鐘 |
| `2026-10-10-ai-pool-bootstrapping-design.md` | 設計文件：讀「總整理」A–K | 20 分鐘 |
| `2026-10-10-ai-pool-bootstrapping-design-appendix.md` | 附錄：你那條線需要的章節（每個任務卡會告訴你） | 查閱 |
| `ai-pool-bootstrapping-plain.md` | 白話版（想快速理解時看） | 選讀 |
| `user-facing-draft.md` | 使用者說明頁、常見問題草稿（C3 用） | 負責 C3 者必讀 |

## 3. 進度表（也是唯一的進度來源）

**規則**
1. 只改**自己那幾列**的「負責、狀態、最後更新、證據、備註」，隨 PR 一起改。不需要另外回報進度。
2. 狀態只有五種：`未開始`、`進行中`、`待審`、`完成`、`卡住`。
   - `完成`：「證據」欄要寫 PR 連結或你跑過的測試指令與結果；「產出檔案」都已存在；`python -m pytest -s -q` 全過。
   - `卡住`：「備註」要寫卡在哪、需要誰做什麼決定。
3. 已決定的事項不要再問（見第 4 節與設計文件 C）。需要決定但還沒決定的，第 4 節都列了**預設做法**，直接照做。

<!-- BOARD:START -->
| ID | 內容 | 負責 | 狀態 | 最後更新 | 產出檔案 | 證據 | 備註 |
|---|---|---|---|---|---|---|---|
| E1 | 【主線】longest-substring 測資確認與記錄 | Claude（代組員） | 完成 | 2026-10-13 | | `run_eval --problem longest-substring`：18 道，TPR 1.0000、訓練池 TNR 0.8889，無漏網；順序：官方範例 3 道在前、其餘由短到長、壓力測資在最後 | 18 道 = 人工迭代 17 道 + main #10 加的 5 萬字元壓力測資（擋 O(n²)，TNR 0.8824→0.8889）；驗收池 0.47 是先前紀錄，已用過一次，本次沒有重跑；不補輪次（K12） |
| E2 | 【主線】best-time-stock 測資定稿 | Claude（代組員） | 完成 | 2026-10-13 | backend/problem.py | r1–r3（gpt-oss-120b 提案、AI 代審）：2→4 道，TPR 1.0、訓練池 TNR 0.5→0.5833（達成率 0.70），訓練池無漏網；驗收池跑一次：TNR 0.4167，`global_min_then_max` 漏網（K13）；已用 E4 寫回 problem.py；pytest 104 passed, 8 skipped | 以「可實測」交付、**未達標**，未標收斂；r3 沒有新增任何測資（K15） |
| E3 | 【主線】longest-valid-parentheses 測資定稿 | Claude（代組員） | 完成 | 2026-10-13 | backend/problem.py | r3–r5（r3 用既有候選、r4–r5 gpt-oss-120b 提案，AI 代審）：14→54 道，TPR 1.0、訓練池 TNR 0.5476→0.6759（達成率 0.68），6 種錯誤都被擋到（含 `left_scan_only`）；驗收池跑一次：TNR 0.5370，無漏網；已用 E4 寫回 problem.py；pytest 104 passed, 8 skipped | 以「可實測」交付、**未達標**（停止條件：3 輪），未標收斂 |
| E4 | 【主線】最終輪測資寫回 `problem.py` 的匯出工具 | 專題負責人 | 完成 | 2026-10-10 | backend/testgen/export_round_to_problem.py, backend/tests/test_export_round.py | 已實作；15 個單元測試（58 passed）；對三題真實資料 dry-run 過；兩個變異檢查被測試抓到 | E2、E3 用它寫回 problem.py |
| E5 | 【主線】best-time-stock 實驗外補強（K13、K15） | Claude（代組員） | 完成 | 2026-10-13 | backend/problem.py, backend/tests/test_export_round.py | 補 6 道（標「實驗外補強（E5）」），共 10 道；`run_eval --problem best-time-stock`：TPR 1.0、訓練池 TNR 0.3833、無漏網；驗收池（實驗外確認，未寫入 rounds/）0.4667、無漏網；pytest 123 passed, 8 skipped | 訓練池 TNR 比實驗紀錄 0.5833 低：新增的邊界案例（只有 1 天、價格相同）抓不到錯誤，會拉低平均；`rounds/` 實驗紀錄不變 |
| E6 | 【主線】全自動流程：`pipeline.py`、`auto_review.py`（自動審核升級為正式元件） | Claude（代組員） | 完成 | 2026-10-13 | backend/testgen/pipeline.py, backend/testgen/auto_review.py, backend/tests/test_pipeline.py | 自動審核對 LC121 r1–r3、LC32 r1–r5 重算全部一致；LC3 全自動跑完 4 輪；三題驗收池結果存成 `rounds/heldout_final.json`；`python -m pytest -q` 108 passed, 8 skipped | 拿掉人工審核後的主要流程；結果見計畫第八節 |
| M1 | 【主線】合併到 main 前的準備 | | 未開始 | 2026-10-13 | | | E5、B2、C1、C2 已完成，可以開始；見任務卡 M1 |
| B2 | 【主線】三題虛擬碼產出與往返檢查（I8） | Claude（代組員） | 完成 | 2026-10-13 | backend/testgen/problems/longest-substring/pseudocode.json, backend/testgen/problems/best-time-stock/pseudocode.json, backend/testgen/problems/longest-valid-parentheses/pseudocode.json | `pseudocode_roundtrip.py --k 3`（寫手 gpt-oss-20b、實作者 gpt-oss-120b）：三題都第 1 次就通過，各 3/3 實作與 S+ 一致（探測輸入 23,848／21,533／10,194 組）；存成 `problems/<id>/pseudocode.json` | 人工閱讀的小瑕疵記在 format_warnings、沒有改寫：longest-valid-parentheses 全文是英文；longest-substring 第 13 步停止條件寫成「超過長度」、第 4 與 13 步重複 |
| C1 | 【主線】提示加入虛擬碼與 `hint_guard` 擴充（I11） | Claude（代組員） | 完成 | 2026-10-13 | backend/ai.py, backend/hint_guard.py, backend/tests/test_ai.py | `build_prompt(..., pseudocode)`：runtime_error／timeout／wrong_answer 放入虛擬碼與「可引用步驟編號、不整段複述、不斷言第 N 步錯」規則；簽名測試確認沒有學生程式碼參數。`hint_guard`：逐字抄超過 2 個步驟就擋；三題虛擬碼本身不會被當成程式碼。pytest 123 passed, 8 skipped；真實模型三題各 4 次共 12/12 正常提示 | 加入虛擬碼後 prompt 變長，gpt-oss-20b 預設推理會把 2048 token 用光、回傳空內容（實測 3/4，同 K3）；提示改用 reasoning_effort=low（只在 gpt-oss，Gemini 不帶） |
| C2 | 【主線】虛擬碼顯示（I15） | Claude（代組員） | 完成 | 2026-10-13 | backend/problem.py, backend/main.py, frontend/src/components/ProblemStatement.vue | `problem.py` 只載入 passed 的 pseudocode.json（version、text）；`GET /problems/{id}` 可選欄位；`ProblemStatement.vue` 收合區塊顯示。新增 3 個測試（有／沒有虛擬碼、未通過不載入）；pytest 112 passed, 8 skipped；瀏覽器實測：沒虛擬碼的題目外觀不變、有的預設收合 | AI 寫的文字先跳脫 HTML，只轉換 **粗體** 與 `程式` 兩種標記 |
| C3 | 【主線】使用者說明與同意說明（I16） | 專題負責人 | 進行中 | 2026-10-13 | docs/superpowers/specs/user-facing-draft.md | 負責人已確認同意（2026-10-13） | 草稿中【待確認】欄位（保存期限、可存取的人、退出後資料處理等）的實際內容待負責人填入 |
| T | 【主線】組員測試 T1–T7 | | 取消 | 2026-10-13 | | | 負責人決定（2026-10-13）：不另做組員測試，直接用目前版本進行報告與測試 |
| A1 | 【強化】安全批次執行器（I1） | | 未開始 | 2026-10-10 | backend/testgen/safe_batch.py, backend/tests/test_safe_batch.py | | 不阻擋實測；規格與效能基準已備 |
| A2 | 【強化】AI 程式的嚴格檢查（I2） | | 未開始 | 2026-10-10 | backend/executor.py, backend/tests/test_executor.py | | 不阻擋實測 |
| A3 | 【強化】檢查關接批次執行器、`pool_meta.json`（I3） | | 未開始 | 2026-10-10 | backend/testgen/assess_problem.py | | 依賴 A1 |
| A4 | 【強化】`registry` 自動化（I13） | | 未開始 | 2026-10-10 | backend/testgen/registry.py | | 依賴 A3 |
| B1 | 【強化】建池腳本（I6） | | 未開始 | 2026-10-10 | backend/testgen/bootstrap.py, backend/tests/test_bootstrap.py | | 依賴 A1 |
| B3 | 【強化】雜湊、候選庫與淘汰迴圈（I4、I5） | | 未開始 | 2026-10-10 | backend/testgen/pool_store.py, backend/tests/test_pool_store.py | | 依賴 A1 |
| B4 | 【強化】標籤審核紀錄 `pool_review.json`（I9） | | 未開始 | 2026-10-10 | backend/testgen/pool_review.py | | 依賴 B1 |
| B5 | 【強化】驗收批用模型 B 產生並隔離（I10） | | 未開始 | 2026-10-10 | | | 依賴 B1 |
| B6 | 【強化】輸入規格自動產生與驗證（I7） | | 未開始 | 2026-10-10 | | | 依賴 A1 |
| C4 | 【強化】失敗模式記錄與離線比對（I12） | | 未開始 | 2026-10-10 | | | 依賴 C3 的同意說明 |
| D1 | 論文、簡報、用語同步（I14） | | 未開始 | 2026-10-10 | docs/IEEE_Paper.md | | 由專題負責人處理 |
<!-- BOARD:END -->

> 「產出檔案」是預期產出，檔名有些是建議；調整時請在該列改成實際檔名。

> 【主線】任務**不依賴**【強化】任務：三題測資用現有的人工池與輪次流程就能完成（評測本來就經由 `executor` 的子程序執行）。

**已完成的事（供對照）**：效能基準與答錯集合指紋（`baseline_assess.json`）、Groq 模型與額度限制查明、推理 token 拆解、虛擬碼往返檢查腳本、使用者說明草稿、設計文件整理、全自動測資流程（E6）。後端測試目前：`127 passed, 16 skipped`（16 個 skip = 四題未收斂 × 4 項品質守門員，屬正常）。

## 4. 規則與預設做法

### 4.1 方法凍結（實作時不得改變）
| 類別 | 凍結的決定 |
|---|---|
| 流程 | 設計文件總整理 B 的 9 步 |
| 標準答案 | 通過官方範例、且彼此一致的多份 S+ |
| 池的比較 | 效能＝A（答錯率，越低越稀有）＋B（行為獨特）；淘汰只看與測資無關的指標；驗收批不進淘汰迴圈 |
| 參數 | 設計文件 I 區的暫定值（可做成設定，不得自行調整數值） |
| 虛擬碼 | AI 產生；由別的 AI 只看虛擬碼實作；行為須與 S+ 一致；格式軟規則只記錄警告 |
| 模型 | 訓練組 `openai/gpt-oss-20b`；驗收批 `qwen/qwen3.8-27b`；虛擬碼實作者 `openai/gpt-oss-120b`（驗收批額度不足時，依下表 Q2 切換並標註，不自行換別的模型） |
| 安全 | AI 程式只能在子程序執行，不在主程序 `exec` |
| 提示 | 學生程式碼永遠不傳給 AI；只能加入「虛擬碼」輸入 |
| 測資審核 | **無人工審核**（2026-10-13 決定）。一律由 `auto_review.py` 自動審核：只看評測數字、不看 AI 理由；上一輪正式測資全保留；候選以貪婪法依 TNR 加入，TNR 不再提高就停 |
| 測資流程參數 | `pipeline.py` 預設：`openai/gpt-oss-120b`、temperature 0.7、每輪 12 筆、prompt v2、推理強度 low、回覆上限 4000 tokens、最多 4 輪 |
| 範圍 | 不做準度與效度驗證；不使用網路程式碼；不自動依失敗模式給回饋（只記錄與離線比對） |

**你可以自己決定的**：函式與檔案命名（任務卡有「固定」標示的除外）、內部資料結構、錯誤訊息、測試寫法、程式風格。

### 4.2 遇到問題怎麼辦（不要換方法）
1. 重現並記錄：命令、輸入、輸出、環境（作業系統、Python 版本）。
2. 看第 5 節「已知問題」與下方速查表，有就直接套用。
3. 沒有的話，讓功能**安全失敗**：丟棄該筆、標記原因、繼續下一筆，不要卡住整批。
4. 確認不是環境因素（金鑰、額度、網路、Windows 與 Linux 差異）。
5. 在第 5 節新增一列；若必須改變 4.1 才能真正解決，「影響方法」填「是」，之後由負責人決定。
6. 繼續做其他任務。

**速查表**
| 現象 | 做法 |
|---|---|
| AI 程式逾時或當機 | 丟棄，原因記 `timeout/crash` |
| AI 程式被 `check_forbidden` 擋下 | 丟棄，原因記 `forbidden`，不放寬規則 |
| S+ 沒過官方範例 | 丟棄，原因記 `official` |
| 多份 S+ 在某輸入上答案不同 | 該輸入不採用並記錄 |
| S- 與正解等價／與另一個答錯集合相同 | 丟棄，原因記 `equivalent`／`duplicate` |
| 虛擬碼實作不一致 | 退回重寫，最多 3 次；仍不過標記「虛擬碼未通過」 |
| API 空回應或連續失敗 | 分類記錄（格式、額度、逾時），有限度重試 |
| 429 額度錯誤 | 等一分鐘，不連續重試；縮小單次要求 |

### 4.3 預設做法（負責人尚未決定的事，先照這個做）
| 編號 | 事項 | 預設做法 |
|---|---|---|
| Q1 | 「初學者」用語要改成什麼 | 先不改 |
| Q2 | 驗收批備援模型 | 優先 qwen；額度不足改用 `openai/gpt-oss-120b`，並在紀錄標註「同系列」 |
| Q3 | 是否記錄使用者的程式碼 | **不記錄**；只記錄失敗的測資、時間、匿名編號 |
| Q4 | 同意說明的正式內容 | 寫成草稿，不上線 |
| Q5 | 是否使用網路程式碼 | **不使用**；只用題庫既有的標準解法 |
| Q6 | 測試人數與題數 | 先做組員內部演練，不對外 |
| Q7 | 暫定門檻（相似度 0.95、退回 30%、ε 0.02、最多 3 輪、k=3、≤15 步） | 做成可設定參數，預設用設計文件 I 區的值 |

### 4.4 工作規則
- **金鑰**：只放 `backend/.env`；不要提交、不要貼到文件或對話。
- **驗收批**：`solutions_heldout`、模型 B 產生的驗收批，在池迭代期間不要打開，也不要放進任何提示。
- **不要改**：`registry` 的天花板與收斂標記、`baseline_assess.json`，除非任務卡明說（E2、E3 可以改自己那題的收斂標記）。
- **分支與 PR**：每個任務一個分支；PR 描述寫：做了什麼、怎麼測、沒做什麼、已知限制。
- **不要提交**：結果 JSON、金鑰、`.env`。
- **測試**：改動前後都跑 `python -m pytest -s -q`；新功能要有測試。
- **設計文件**：不要更改流程或決定，由負責人維護。

## 5. 問題紀錄（排除與紀錄）
「影響方法」＝若要真正解決，必須改變 4.1 凍結的內容；標「是」的只能由負責人決定。新增時 ID 接著編號（K11、K12…），不要刪除舊的列。

<!-- ISSUES:START -->
| ID | 現象 | 排除結果／已知原因 | 暫行處理（不改方法） | 影響方法 | 狀態 | 負責 | 日期 |
|---|---|---|---|---|---|---|---|
| K1 | qwen 呼叫回 429「輸出 token 每分鐘上限」 | 已知：每分鐘約 1,000 tokens，且以要求的 max tokens 檢查 | 單次要求 ≤ 900 tokens、呼叫間排隊、一次一份程式 | 否 | 已知 | | 2026-10-10 |
| K2 | 模型回覆的 JSON 解析失敗 | 已知：含程式碼的 JSON 易壞（重複試驗 2/5） | 用分隔標記的純文字區塊由程式切分；解析失敗記為「格式錯」並丟棄該筆 | 否 | 已知 | | 2026-10-10 |
| K3 | JSON 模式回傳空內容（`json_validate_failed`） | 已知：qwen 與 gpt-oss 都出現過 | 不使用 JSON 模式；降低推理 | 否 | 已知 | | 2026-10-10 |
| K4 | 寫手不遵守「禁止索引寫法 `x[i]`」 | 已知：3 次重寫都未遵守 | 索引寫法等軟規則只記錄警告，不退回 | 否 | 已知 | | 2026-10-10 |
| K5 | 效能基準耗時波動（同機重跑差約 3 倍） | 已知：與機器負載有關 | 在自己的機器上重量基準，以指紋（非耗時）判定一致性 | 否 | 已知 | | 2026-10-10 |
| K6 | `pytest` 出現 `WinError 6` | 已知：Windows 的輸出擷取問題 | 加 `-s` | 否 | 已知 | | 2026-10-10 |
| K7 | 虛擬碼實作者與寫手同系列，可能有共同盲點 | 已知、接受 | 在紀錄標註「同系列」 | 否 | 已知 | | 2026-10-10 |
| K8 | 標籤由 AI 代審，可能自己審自己 | 已知、接受（測試階段） | 審核記錄標註「測試階段」；審核與產生分開呼叫 | 否 | 已知 | | 2026-10-10 |
| K9 | 單次結果、無重複，穩定度未知 | 已知 | 文件與輸出一律標明樣本數，不稱為穩定結果 | 否 | 已知 | | 2026-10-10 |
| K10 | 黑名單是名稱檢查，`getattr(__builtins__, 'open')` 等繞過手法擋不住 | 已知、接受（威脅模型：無意誤用） | 嚴格模式只擋名稱；AI 程式另走子程序＋逾時；覺得可疑的程式先人工看 | 否 | 已知 | | 2026-10-10 |
| K11 | longest-valid-parentheses 的 `left_scan_only` 一直擋不到（單次提案與大量取樣共 69 筆候選 0 筆；看分數再改僅少數次擋到） | 已知：這種錯誤只在特定括號結構才出錯 | 照 E3 的停止條件；未達標就以「可實測」交付並保持未收斂 | 否 | 已知 | | 2026-10-10 |
| K12 | longest-substring 的 `r0_tests.json` 是舊基準（18 道），不是目前 `problem.py` 的 17 道 | 已確認（r0 的 source 是 `problem_old.TEST_CASES`，TNR 0.4907） | **負責人已決定（2026-10-10）：不補輪次，直接使用現有 17 道**；匯出工具會拒絕丟掉現有案例；不要對這題的 r0 使用匯出 | 否 | 已知 | 專題負責人 | 2026-10-10 |
| K13 | best-time-stock 驗收池 `global_min_then_max` 沒有被任何測資擋下（實驗紀錄：驗收 TNR 0.4167） | 實驗紀錄照實保留 | **已處理（E5，2026-10-13）**：實驗外補強加入 `[3, 2, 4, 3, 5, 1]`，補強後驗收池無漏網（0.4667，實驗外確認、未寫入 rounds/） | 否 | 已處理 | 專題負責人 | 2026-10-13 |
| K14 | `propose --reasoning-effort` 在 `openai==1.51.0`（requirements.txt 釘的版本）會 TypeError | SDK 太舊，不支援 `reasoning_effort` 參數 | **已修正**：requirements.txt 升到 `openai==1.82.0`；`tests/test_openai_sdk.py` 檢查 SDK 支援 propose 用到的參數；實際呼叫 `ai.get_hint`（gpt-oss-20b）與 `propose.call_model`（gpt-oss-120b、reasoning_effort=low）皆正常 | 否 | 已解決 | Claude（代組員） | 2026-10-13 |
| K15 | best-time-stock 最終只有 4 道測資 | AI 代審的貪婪規則只收「提高平均抓錯數」的候選；r1、r2 各收 1 筆，r3 0 筆 | **已處理（E5，2026-10-13）**：負責人決定補到 10 道（6 道實驗外補強，含教學用邊界案例）；匯出工具會擋下重新匯出 r3（否則會丟掉這 6 道），有測試保護 | 否 | 已處理 | 專題負責人 | 2026-10-13 |
| K16 | longest-substring 在 2026-10-13 用 pipeline 從 `r0_tests.json` 跑了全自動 4 輪，與 K12「不補輪次」的決定不一致 | 只存在 `rounds/r1–r4`，沒有寫回 `problem.py` | **負責人決定刪除（2026-10-13）**：已刪除 r1–r4、`heldout_final.json`、`pipeline_summary.json`，只保留 `r0_tests.json`；論文不引用這 4 輪的數字 | 否 | 已處理 | 專題負責人 | 2026-10-13 |
| K17 | Groq 回 413「Request too large」，每分鐘 token 上限 8000 | 已知：prompt 和 `max_completion_tokens` 加總計算；推理強度預設時回覆可用滿 8000 | pipeline 預設 `--reasoning-effort low`、`--max-tokens 4000`；propose 遇到 429 等 60 秒重試一次 | 否 | 已排除 | | 2026-10-13 |
| K18 | 拿掉人工審核 | 2026-10-13 負責人決定：研究改為驗證全自動流程能否運行 | 原計畫的人工效率指標（細看比例、審核秒數、看理由後改判）不再量測，列為研究限制與未來工作；K8 的「測試階段」標註改為正式做法 | 是（已決定） | 已決定 | 專題負責人 | 2026-10-13 |
| K19 | 虛擬碼是完整解法的逐步說明，C2 會在題目頁顯示給所有人 | 設計上是給受測者用的 | **負責人決定（2026-10-13）：全部開放**，正式網站上所有人都看得到；不加開關 | 是（已決定） | 已決定 | 專題負責人 | 2026-10-13 |
<!-- ISSUES:END -->

## 6. 任務卡

### 開工前（第一天，約 20 分鐘）
```bash
cd backend
python -m pytest -s -q      # 預期：123 passed, 8 skipped（需要 backend/.env 有 GROQ_API_KEY，只跑測試的話填任意值如 dummy 也可以）
python ../docs/superpowers/specs/teammate-tests/baseline_assess.py --repeats 3   # 量你機器上的效能基準
python ../docs/superpowers/specs/teammate-tests/pseudocode_roundtrip.py --problem longest-substring   # 需要 backend/.env 的 GROQ_API_KEY
git status      # 預期：只多了腳本產生的結果 JSON
```

### 軌道 E：三題測資交付（主線）

**共同流程（2026-10-13 起：一個指令跑完）**——不需要手動分輪：
```bash
cd backend
python -m testgen.pipeline --problem <題目id> --plan   # 先看狀態與接下來會做什麼（不呼叫 API、不寫檔）
python -m testgen.pipeline --problem <題目id>          # 提案 → 自動審核，一輪一輪跑到停止
```
- 每一輪：`propose.py` 提案（已有候選檔就沿用，不重抽）→ `auto_review.py` 自動審核。
- **停止條件**（依序）：收斂（TPR = 1、訓練池無漏網、達成率 ≥ 0.85）→ 停滯（上一輪沒保留新測資）→ 達到第 4 輪。
- **驗收池自動處理**：結束後只跑一次，存成 `rounds/heldout_final.json`；檔案已存在就只讀出，不會重跑。看了結果也不要回頭改測資。
- 結束後會寫 `rounds/pipeline_summary.json`，並印出可以貼進報告的表格。
- 中途失敗（例如額度用完）修正後重跑同一個指令，會從失敗的那一輪接續。
- 定稿後用 E4 的工具把最後一輪測資寫回 `problem.py`（先不加 `--write` 看差異），再跑 `python -m pytest -s -q`。
- 單獨看某一輪的審核結果：`python -m testgen.auto_review --problem <題目id> --round <N> --dry-run`（舊路徑 `teammate-tests/ai_review_round.py` 仍可用，會呼叫同一份程式）。

**E1 longest-substring（確認與記錄；預設不新增輪次）**
- **注意陷阱**：這題的 `rounds/r0_tests.json` 是**舊基準（18 道，TNR 0.49）**，不是現在 `problem.py` 裡的 17 道（那是人工迭代四輪的結果）。它是先前「從舊基準由 AI 協助迭代」的實驗起點，**不要拿它當起點去跑新輪次，也不要匯出它**（匯出工具會拒絕，因為會丟掉現有案例）。
- 這題已經登記為收斂，品質守門員通過，所以對「下次實測」來說已經可用。
- 要做的事：(1) 確認官方範例在最前面、其餘由短到長（目前就是）；(2) 在 PR 或問題紀錄記下目前的數字：訓練池 TNR 0.88、驗收池 0.47（已知落差；驗收池先前已用過一次）；(3) 在進度表填證據。
- **已決定（2026-10-10）：不補輪次**，直接使用現有 17 道（問題紀錄 K12）。AI 試驗指出缺空字串這類邊界案例，只當觀察記錄，不新增測資。
- 大小：小。

**E2 best-time-stock**：起點是 2 道官方範例（r0，TNR 0.5，天花板 5/6，漏掉 `skip_last_day`）。從第 1 輪開始跑，定稿後在 `registry` 把收斂標記改為 `True`（僅在達成率 ≥ 0.85 時）。大小：中。

**E3 longest-valid-parentheses**：已有 r0～r2（r2 為 14 道，AI 代審）與 r3 候選（46 道過取樣，可直接審）。從第 3 輪續跑。`left_scan_only` 是已知難點（K11）：照停止條件走，未達標就以「可實測」交付並保持未收斂。大小：中。

**E5 best-time-stock 實驗外補強（已完成，2026-10-13）**
- 為什麼：自動審核只收「提高平均 TNR」的候選，這題停在 4 道（K15），驗收池也漏掉 `global_min_then_max`（K13）。品質守門員要求至少 10 道，只是因為這題未收斂才被略過。
- **實驗紀錄不動**：`rounds/` 底下的檔案（含 `heldout_final.json`）都是實驗結果，不修改、不重跑。補強只改 `problem.py`，並在註解標 `# 實驗外補強`。
- 建議補的測資（已實測）：`[3, 2, 4, 3, 5, 1]`，答案 3。它擋下 `global_min_then_max`，同時抓到訓練池 4 種、驗收池 3 種錯誤。其餘補教學用的邊界案例到總數 ≥ 10，例如只有 1 天、一路上漲、價格全部相同、最低點在最後一天。expected 一律用參考解 `one_pass.py` 算，不要手算。
- 完成條件：`python -m testgen.run_eval --problem best-time-stock --label e5_check` 的 TPR = 1.0、訓練池無漏網；`python -m pytest -s -q` 全過；在問題紀錄 K13、K15 寫上處理結果。
- 大小：小。

**E6 全自動流程（已完成）**：`backend/testgen/pipeline.py`、`backend/testgen/auto_review.py`
- 用法見上方「共同流程」。自動審核的規則與 2026-10-13 之前各輪使用的完全相同，對既有 8 輪重算都一致。
- 預設參數見 4.1。Groq 免費方案每分鐘 8000 tokens，**prompt 和回覆上限加總**計算（K17），所以 pipeline 預設低推理強度、回覆上限 4000；遇到 429 會等 60 秒重試一次。
- 測試：`backend/tests/test_pipeline.py`（停止條件與彙整，讀真實紀錄，不呼叫 API）。

**M1 合併到 main 前的準備（E5、B2、C1、C2 完成後）**
1. 把 main 的最新內容同步進 `feat/ai-assisted-testgen`，解決衝突後跑 `python -m pytest -s -q`。
2. 開 PR 到 main，描述照第 7 節模板，附上三題最終的 TPR、TNR、達成率與驗收池結果。
3. Vercel 會替 PR 建預覽網址：在預覽網址上把三題都實際提交一次正解與一個錯解，確認判題與 AI 提示正常。
4. 確認 `registry` 裡兩題的收斂標記維持 `False`（沒達標就不要改）。
5. 由負責人合併；合併後 main 會自動部署到 Vercel 與 Render。
- 大小：小。

**E4 匯出工具（已完成）**：`backend/testgen/export_round_to_problem.py`
- 用法：`python -m testgen.export_round_to_problem --problem <id> --round <N> --official <K> [--write]`。**預設只印出差異，不寫檔**；確認後加 `--write`。官方範例筆數 K：longest-substring 3、best-time-stock 2、longest-valid-parentheses 3。
- 規則：前 K 道官方範例照原順序（必須和 `problem.py` 目前最前面的 K 道相同，否則報錯）；其餘非壓力測資由短到長；壓力測資在最後；`index` 重新編號；沿用該題現有的 `input`／`args` 寫法；保留現有案例前面的註解，新案例標 `# rN`。
- **保護**：這一輪的測資必須包含 `problem.py` 目前所有案例，否則中止並列出會被丟掉的案例（`--allow-drop` 才能略過）；有重複輸入、`--official` 不符也會中止。連續執行兩次結果相同。
- 驗證：`backend/tests/test_export_round.py`（15 項，全程使用暫存複本）；對三題的真實資料做過 dry-run；故意拿掉排序、拿掉保護兩種破壞，測試都會失敗。
- 用法提醒：E2、E3 定稿後各跑一次 `--write`，再跑 `python -m pytest -s -q`。**不要對 longest-substring 的 `r0` 使用。**

### 組員測試 T（主線）：把做好的東西都實際跑過一遍
目的：確認腳本與流程在不同人、不同機器上都跑得起來，並收集人讀虛擬碼的意見。**所有人都可以做，不需要寫程式。**結果是觀察，不是準度或效度的結論。

| 編號 | 內容 | 要記錄 |
|---|---|---|
| T1 | `pseudocode_roundtrip.py --problem longest-substring` 重跑 5 次（預設參數） | 每次是否一次通過、嘗試次數 |
| T2 | 同題各跑 3 次，分別用預設與 `--strict-format` | 兩者通過率、被格式規則退回的次數 |
| T3 | 另外兩題（`best-time-stock`、`longest-valid-parentheses`）各跑 3 次 | 是否跑通、錯誤訊息 |
| T4 | 實作者換成不同系列的模型（`--impl`；注意額度，qwen 要 `--effort none`，見 K1） | 不一致次數是否上升 |
| T5 | 至少 2 人用檢查表（附錄 18.6）審 3 份通過的虛擬碼 | 可讀性評分與備註 |
| T6 | 每次執行前後各做一次 `git status` | 確認腳本沒有改到 repo |
| T7 | 試跑全自動流程（不呼叫 API、不寫檔）：① 三題各跑 `python -m testgen.pipeline --problem <題目id> --plan`；② `python -m testgen.auto_review --problem longest-valid-parentheses --round 3 --dry-run`（預期印出各候選的保留或丟棄、最後的 TNR，並註明沒有寫入任何檔案）；③ 跑完後 `git status` 應該沒有任何變動 | 能不能跑通、輸出看不看得懂、錯誤訊息 |

- 怎麼回報：照附錄 18.7 的格式（日期、執行者、題目、參數、嘗試次數、通過與否、失敗原因分類、備註）貼在 PR 描述或群組，**不要提交結果 JSON**。
- 失敗原因請分類：格式不合格、實作不一致、逾時或當機、API 錯誤（額度或格式）。
- 遇到問題照 4.2 處理，並寫進第 5 節的問題紀錄。

### 軌道 A：安全執行（強化，不阻擋實測）

**A1 安全批次執行器**（附錄九）
- 目標：`backend/testgen/safe_batch.py`，一個子程序處理一批輸入；逾時、輸出上限、例外都不會讓整批失敗。
- **介面（固定，名稱不可更動）**：
  - 模組常數 `ERR`（該輸入出錯或沒跑到）；
  - 類別 `BatchResult`，屬性 `outputs`、`status`、`timed_out_at`、`elapsed`；
  - 函式 `evaluate_solution(code, method, inputs, *, chunk_size=200, chunk_timeout=5.0, total_timeout=120.0, max_output_bytes=1_000_000) -> BatchResult`，後四個為 keyword-only；
  - `status` 只能是 `ok`、`timeout`、`crash`、`too_much_output`、`forbidden`、`memory`。
- 為什麼需要：`assess_problem.py` 現在用 `exec` 在主程序跑程式，AI 寫的無窮迴圈會卡死整個檢查；`executor.run_code` 每個輸入開一個子程序，太慢（約 3 萬～4 萬次啟動）。
- 已決定的做法：整塊逾時時**不**二分定位；已完成的塊保留，其餘輸入標為 `ERR`，`status="timeout"`。第一版**不做**記憶體與 CPU 限制，只預留 `status="memory"` 並記入問題紀錄。逾時後子程序（含子孫）必須被終止；Windows 上若做不到，寫進問題紀錄並讓該次評估安全失敗。
- 不要做：不要在主程序 `exec` 任何 AI 程式；不要為了過測試而放寬黑名單。
- 完成條件：附錄 9.5 的 8 項；尤其是**一致性**（答錯的輸入集合與 `baseline_assess.json` 完全相同）與**效能**（不超過你自己機器上基準的 5 倍）。
- 大小：中。

**A2 AI 程式的嚴格檢查**
- 目標：`executor.check_forbidden` 目前不擋 `open`、`eval`、`exec`、`__import__`。
- 已決定的做法：新增**只給 AI 程式路徑使用**的嚴格模式，除原有規則外再擋上述內建函式（含別名，例如 `o = open`）；**學生提交的路徑維持現狀、行為不變**。`safe_batch` 一律使用嚴格模式。
- **介面（固定）**：`check_forbidden(code: str, strict: bool = False) -> str | None`。
- 不要做：不要改動學生提交的行為；不要為了讓某份程式通過而放寬規則。
- 完成條件：越權樣本在嚴格模式被擋；既有測試全過。
- 大小：小。

**A3 接進檢查關**：`assess_problem.py` 新增 `--isolated`；每個池新增 `pool_meta.json`（`source: human|ai`、模型、時間）；`source == ai` 時一律走 A1。完成條件：人工池的結果與基準一致；AI 池不會走 `exec`。大小：小。

**A4 `registry` 自動化**：天花板由檢查關算出後寫入；「是否收斂」由流程判定，不再手填。不改變既有題目的登記值。大小：小。

### 軌道 B：建池與池管理（B2 為主線，其餘為強化）

**B1 建池腳本**（附錄八、十、十一）
- 目標：`testgen/bootstrap.py`——題意摘要、S+（標準解法）、S-（依虛擬碼步驟偏離，標「偏離第幾步」）。
- 必須遵守（都是實測得到的）：
  1. qwen 每分鐘輸出上限約 1,000 tokens，單次 `max_completion_tokens` 超過約 900 會被拒絕 → **一次只請它寫一份程式**，呼叫間排隊。
  2. 不要要求「含程式碼的 JSON」→ 用固定標記分隔的純文字區塊，由程式切分。
  3. 不使用 JSON 模式（有時回傳空內容）。
  4. 關閉或壓低推理可省很多 tokens（單次小測：低度推理約為關閉的 5 倍）。
- 完成條件：模擬壞格式、429、空回應時不崩潰並分類記錄；在 longest-substring 能產出 S+ 與帶標籤的 S-。
- 依賴：A1。大小：大。

**B2 三題虛擬碼（主線）**（附錄十四、十七、十八）
- 目標：為三題各產出一份虛擬碼，通過往返檢查，並存成 `backend/testgen/problems/<題目id>/pseudocode.json`。
- 做法：用現有的 `teammate-tests/pseudocode_roundtrip.py`（三題各試跑過一次都通過，k=2；這不是穩定結果）。正式產出建議 `--k 3`。
- `pseudocode.json` 欄位：`version`（文字的雜湊）、`text`、`source_s_plus`（來源檔名）、`writer`／`implementer`（模型）、`k`、`attempts`、`passed`、`created_at`、`format_warnings`。
- 已決定的做法：格式軟規則（索引寫法等）維持「只記錄警告、不退回」（K4）；不做自動改寫；可讀性由人工檢查表處理（附錄 18.6）。我們看過的小瑕疵（例如重複描述、夾雜簡體字「顶」）請記在警告欄，不要自行重寫內容。
- 完成條件：三題的 `pseudocode.json` 都存在且 `passed = true`；若某題 3 次都不過，照 4.2 標記「虛擬碼未通過」，該題暫不顯示虛擬碼並記入問題紀錄。大小：小～中。

**B3 雜湊與淘汰迴圈**（附錄十二）
- 目標：候選庫以雜湊索引；計算 A（答錯率）、B（獨特度）；近似重複分群；退回改寫；平穩停止；凍結 `pool_version`。
- 原則：**淘汰只看與測資無關的指標**；驗收批不進這個迴圈；參數全為暫定，做成可設定。
- 大小：大。

**B4 標籤審核紀錄**：`pool_review.json`，欄位含審核者、依據（偏離第幾步）、是否測試階段。**B5 驗收批**：用模型 B 產生並隔離，迭代期間不出現在任何提案或審核提示。**B6 輸入規格自動產生與驗證**：`validate`／`random_args`／`small_args` 須通過一致性檢查。

### 軌道 C：提示與使用者面向（C1–C3 為主線，C4 為強化）

**C1 提示加入虛擬碼**（附錄十六；設計文件 G1）
- 目標：`build_prompt` 新增「虛擬碼」輸入（題目材料）；**不得**加入學生程式碼參數。`hint_guard` 擴充：不得整段複述虛擬碼；虛擬碼本身不能被誤判為程式碼；允許引用步驟編號。
- 完成條件：既有 `test_ai.py` 全過；新增對應測試。大小：中。

**C2 虛擬碼顯示**
- 目標：讓使用者在題目頁看到虛擬碼。
- 資料來源：B2 產出的 `backend/testgen/problems/<題目id>/pseudocode.json`（只讀 `version`、`text`、`passed`）。`problem.py`／後端載入後放進 `PROBLEMS[pid]["pseudocode"]`；`GET /problems/{id}` 回傳可選欄位；`ProblemStatement.vue` 有欄位才顯示。
- 注意：只有通過往返檢查的虛擬碼才能上線；測資內容仍不可送到前端。
- 完成條件：沒有虛擬碼的題目外觀不變；兩種情況都有 API 測試。大小：小～中。

**C3 使用者說明與同意**
- 目標：給測試者的說明頁與同意說明。**完整草稿已寫好：`user-facing-draft.md`**，請在它的基礎上修改，不要從零開始。
- 注意：同意說明牽涉學校與倫理規定，**由負責人向老師或系辦確認**；草稿中標【待確認】的欄位等負責人決定，沒決定前不要自行填寫。
- 完成條件：一位沒參與開發的人讀完說明，能自己說出「要做什麼、AI 看不看得到我的程式、資料怎麼記錄」。大小：小～中。

**C4 失敗模式記錄與離線比對**：記錄每位使用者（匿名編號）的測資失敗模式，離線與各 S- 的簽章比對。**本次不做自動提示。**預設不記錄程式碼；開啟記錄前必須完成 C3 的同意。大小：中。

## 7. 順序與回報

**順序（不訂日期）**
- 主線：E1–E6、B2、C1、C2 已完成；T 取消（2026-10-13 負責人決定）。**剩下：C3【待確認】欄位填入、M1（合併前準備）**，再對照「下次實測前的檢查清單」。
- 強化（有空再做，不阻擋實測）：A1 → A2、A3 → B1 → B3、B4、B5；A4、B6、C4 可穿插。

**回報模板**（放在 PR 描述）
```
任務：（例如 A1）
做了什麼：
怎麼測：（命令與結果）
沒做／未解：
已知限制：
環境：（作業系統、Python 版本）
需要決策：
```
