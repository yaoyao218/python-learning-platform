# 交接文件：AI 輔助測資實驗（給組員實作與測試）

> 更新日期：2026-10-07　分支：`feat/ai-assisted-testgen`
> 完整設計與所有數據：[`docs/superpowers/plans/2026-10-07-ai-assisted-testgen.md`](superpowers/plans/2026-10-07-ai-assisted-testgen.md)（以下簡稱「計畫」）
> 本文件只講：**現在做到哪、怎麼跑起來、接下來誰做什麼、哪些規則不能破。**

---

## 0. 一分鐘看懂

- **研究要回答：** 「AI 提案測資 → 客觀評測 → 人先看數字再看理由」這套流程，能不能在不同難度的題目上，產出**穩定**的測資？
- **實驗題目：** 易 LC121 Best Time to Buy and Sell Stock／中 LC3 Longest Substring／難 LC32 Longest Valid Parentheses
- **現在進度：** Phase 0–2 完成（工具鏈、解法池、AI 提案器）。**Phase 3–4（評測分流、人工審核介面）是正式實驗前最後要寫的工具**，寫完就能開始跑實驗。

```
第 0 輪測資 ──► propose.py（AI 提案）──► score_candidates.py（評測 + 分流）──► review.py（人工審核）
   ▲               ✅ 已完成                 ⬜ 待實作（任務 A）                  ⬜ 待實作（任務 B）
   │                                                                                    │
   └──────────── 第 N 輪正式測資 r{N}_tests.json ◄────── 合併通過的候選 ◄──────────────────┘
                     │
                     └─ 收斂後：跑一次驗收池（run_eval --heldout）→ 匯出上線
```

---

## 1. 環境設定

```bash
git fetch
git checkout feat/ai-assisted-testgen
cd backend
pip install -r requirements.txt
```

- Python **3.10 以上**（程式用了 `str | None` 型別語法）
- `backend/.env` 放 `GROQ_API_KEY=...`（**不要 commit**，跟組長拿或自己到 console.groq.com 申請）
- Windows 終端機中文亂碼：指令前加 `PYTHONIOENCODING=utf-8`（PowerShell：`$env:PYTHONIOENCODING="utf-8"`）

**確認環境正常：**

```bash
cd backend
pytest -q
# 預期：43 passed, 8 skipped
# 8 個 skip = 兩題尚未收斂 × 4 項品質守門員，屬正常
```

---

## 2. 已完成的成果（可以直接引用到報告）

| # | 成果 | 關鍵數字 | 驗證方式 |
|---|---|---|---|
| 1 | 題目適用性判斷方法（四關） | 實測 6 題，選出起點達成率 0.60／0.49／0.28 的難度梯度 | `python -m testgen.assess_problem --problem <id>` |
| 2 | **TNR 達成率**：固定門檻 0.85 不適用所有題目 | Valid Parentheses 上限 0.667、LC121 上限 0.833 | 計畫第五節 |
| 3 | **測資「背答案」問題** | LC3 現行測資：訓練池 TNR 0.882 → 驗收池 **0.471** | `python -m testgen.run_eval --problem longest-substring --heldout --label x` |
| 4 | 修好 executor 輸入長度上限 | 原本 Windows 超過 3.2 萬字元就失敗；現在 10 萬筆輸入正常 | `pytest tests/test_executor.py` |
| 5 | AI 提案器試跑（**不算實驗數據**） | LC32：0 筆不合法、target_hit 91%、補到第 0 輪漏掉的 2 種錯 | `rounds/pilot/` |

---

## 3. 程式架構速覽

```
backend/testgen/
├── registry.py            各題登記：池子位置、參考解、TNR 上限、converged 旗標
├── run_eval.py            正式 TPR/TNR 評測（經平台 executor）；--problem、--heldout
├── assess_problem.py      題目評分卡（適用性第二、三關）
├── rounds.py              每輪正式測資與評測：init / show；evaluate() 可直接 import
├── propose.py             AI 提案器：--dry-run、--pilot、--force
├── solutions_correct/ solutions_wrong/      LC3 的歷史池子（不要動）
└── problems/<problem_id>/
    ├── solutions_correct/     S+ 正解池（3 個）
    ├── solutions_wrong/       S- 訓練池（6 個）——檔頭第一行是給 AI 的錯誤描述
    ├── solutions_heldout/     S- 驗收池（3 個）——迭代期間不准用
    ├── spec.py                validate / random_args / small_args
    ├── assessment.json        評分卡
    └── rounds/
        ├── r0_tests.json      第 0 輪（已建立）
        ├── r{N}_candidates.json   AI 提案（propose.py 產生）
        ├── r{N}_scores.json       評測與分流（任務 A 產生）
        ├── r{N}_review.json       人工審核（任務 B 產生）
        ├── r{N}_tests.json        第 N 輪結束後的正式測資（任務 B 產生）
        └── pilot/                 試跑，不計入實驗
```

**常用指令：**

```bash
cd backend
python -m testgen.rounds show --problem longest-valid-parentheses --round 0     # 看某輪評測
python -m testgen.propose --problem longest-valid-parentheses --round 1 --dry-run   # 看給 AI 的 prompt
python -m testgen.propose --problem longest-valid-parentheses --round 1 --pilot     # 試跑（不計入實驗）
python -m testgen.assess_problem --problem best-time-stock                          # 評分卡
```

---

## 4. 待實作任務

建議分工：**任務 A、B 可以平行**（介面已在下面定好），任務 C、D 在 A、B 完成後做。

### 任務 A：`testgen/score_candidates.py`（評測 + 分流）

**用法：** `python -m testgen.score_candidates --problem <id> --round N`

**輸入：** `rounds/r{N}_candidates.json`、`rounds/r{N-1}_tests.json`
**輸出：** `rounds/r{N}_scores.json`

對每一筆候選**單獨**計算：

| 欄位 | 怎麼算 |
|---|---|
| `expected` | 用參考解 S* 算（`registry.reference_path`）。**不要用 AI 給的任何值** |
| `s_plus_ok` | 3 個 S+ 都答對 |
| `kills` | 答錯的 S- 名稱清單（只用訓練池 `solutions_wrong/`） |
| `new_kills` | `kills` 裡「目前正式測資通過率 ≥ 50% 或完全沒被抓到」的 S- |
| `delta_tnr` | 把這筆加進上一輪正式測資後，TNR 的變化 |
| `target_hit` | `target_bug in kills` |
| `triage` | `fast_accept` / `fast_reject` / `ambiguous` |

**分流規則（⚠️ 實驗前全組要先定案、寫進計畫，跑過資料後不能再改）**，建議版本：

- `fast_reject`：`s_plus_ok` 為 False，或 `kills` 為空
- `fast_accept`：`s_plus_ok` 為 True，且 `new_kills` 非空，且 `delta_tnr > 0`
- `ambiguous`：其他

**實作提示：**
- 評測用平台 executor，保持與 `run_eval` 一致：可以參考 `rounds.evaluate()`，把「上一輪測資 + 這一筆」組成新的 case list 丟進去算 TNR，再減掉上一輪的 TNR 就是 `delta_tnr`。
- 單筆的 `kills` 可以用 `run_eval.run_solution_on_case()` 對每個 S- 跑。
- 每筆候選要給一個 `index`（接在上一輪最大 index 後面）。
- **輸出檔不要包含 `rationale`**，避免審核前被看到。
- 注意 TNR 是「平均」：一筆只抓到 1 種錯的測資，就算補到漏網的錯，也可能讓 TNR 下降（`delta_tnr < 0`）。這是正常現象，所以才需要 `ambiguous` 讓人判斷。

**驗收標準：**
- [ ] 用 `rounds/pilot/` 的試跑檔（複製一份改名成 `r1_candidates.json` 放到暫存目錄測，**不要放進正式 rounds/**）跑出合理的結果
- [ ] 每筆的 `expected` 與 `assess_problem.py` 用同程序算出來的一致
- [ ] 把上一輪測資原封不動當成候選時，`delta_tnr` 應該約為 0、`new_kills` 為空

### 任務 B：`testgen/review.py`（人工審核 CLI）

**用法：** `python -m testgen.review --problem <id> --round N --reviewer <名字>`

**輸入：** `r{N}_scores.json`、`r{N}_candidates.json`（只在審核者按下查看時讀 `rationale`）
**輸出：** `r{N}_review.json`、`r{N}_tests.json`

**每一筆的畫面流程（順序固定，是實驗設計的核心）：**

1. 顯示：輸入、expected、`kills`、`new_kills`、`delta_tnr`、`triage` 標籤。**不顯示 AI 理由。**
2. 審核者輸入裁決：`k`=留下、`d`=丟棄、`e`=修改後留下（修改後的輸入要先過 `spec.validate`，expected 由 S* 重算）
3. 裁決送出**之後**才能按 `r` 看 AI 理由；看完可以改判，但要記錄「改判了」

**`r{N}_review.json` 格式（⚠️ `propose.py` 第 2 輪會讀這個檔，key 名稱不能改）：**

```json
{
  "problem": "longest-valid-parentheses",
  "round": 1,
  "reviewer": "名字",
  "started_at": "...", "finished_at": "...",
  "items": [
    {
      "id": "r1c1",
      "args": ["(()())"],
      "target_bug": "total_pairs",
      "kills": ["total_pairs", "max_depth"],
      "triage": "fast_accept",
      "decision": "keep",
      "edited_args": null,
      "seconds": 12.4,
      "viewed_rationale": false,
      "changed_after_view": false
    }
  ]
}
```

- `decision` 只能是 `keep` / `drop` / `edit`
- `seconds`：從畫面顯示到「第一次」送出裁決的秒數（看理由、改判的時間不算進去）

**審核結束後：** 把 `keep` / `edit` 的候選合併到上一輪測資，用 `rounds.evaluate()` 評測，再用 `rounds.save_round_tests()` 存成 `r{N}_tests.json`。

**驗收標準：**
- [ ] 沒送出裁決之前，畫面上任何地方都看不到 `rationale`
- [ ] 中途中斷（Ctrl+C）再開啟，可以從上次停下的地方繼續，已審的不重審、秒數不重算
- [ ] 產出的 `r{N}_review.json` 能被 `propose.py --round N+1 --dry-run` 正確讀取（prompt 裡會出現上一輪的候選與裁決）

### 任務 C：`testgen/experiment_summary.py`（彙整數據）

每題每輪一列：候選數、validator 擋掉數、三種分流各幾筆、人工細看比例、審核總秒數、「全部細看」的估計秒數、TPR／TNR／達成率、`target_hit` 率、看理由後改判次數。輸出 Markdown 表格（直接貼進報告）與 CSV。

### 任務 D：收尾工具

- [ ] `export_to_problem_py.py` 支援 `--problem`：官方範例放前面，其他依輸入長度排序
- [ ] **重建腳本（S3 可重現）：** 只讀 `rounds/` 紀錄、不呼叫 AI，就能重建最終測資，並確認與上線版本一致
- [ ] 品質守門員加上 S2：驗收池每個錯誤解至少被抓一次
- [ ] 題目收斂後把 `registry.py` 的 `converged` 改成 `True`

---

## 5. 實驗紀律（⚠️ 違反任何一條，實驗數據就不能用）

1. **S- 訓練池與驗收池已凍結**，不能增刪改。發現錯誤解寫錯，先回報組長、記錄在計畫裡，不要直接改。
2. **迭代期間不准跑 `--heldout`，也不准打開 `solutions_heldout/` 對照測資。** 驗收池只在每題最後一輪結束後跑一次，結果照實記錄，**不能看了結果再回頭改測資**。
3. **不能重抽到滿意為止。** 每輪只跑一次 `propose.py`；真的要重跑（例如 API 失敗）用 `--force`，舊檔會自動保留，並在計畫裡記錄原因。
4. **審核者在審核前不能看 `r{N}_candidates.json` 和 `pilot/` 的內容**（裡面有 AI 理由）。
5. **審核者固定同一人**，而且審核時要專心，不要同時做別的事（秒數是實驗數據）。
6. 每輪的參數固定：`--model openai/gpt-oss-120b --temperature 0.7 --n 12`，中途不換。
7. 分流規則（任務 A）在第一筆正式資料出現前定案。
8. 所有 `rounds/` 紀錄都要 commit（`pilot/` 除外，見第 7 節待決事項）。

---

## 6. 測試方式

| 測什麼 | 指令 | 預期 |
|---|---|---|
| 全部單元測試 | `pytest -q` | 43 passed, 8 skipped |
| LC3 正式數字沒被改壞 | `python -m testgen.run_eval --tests problem --label check` | TPR 1.0000／TNR 0.8824（測完刪掉 `feedback_check.json`） |
| 新題目的解法池 | `python -m testgen.assess_problem --problem <id>` | 2a–2e 全部 ✓ |
| 第 0 輪 | `python -m testgen.rounds show --problem <id> --round 0` | LC121 0.500、LC32 0.278、LC3 0.4907 |
| AI 提案 prompt | `python -m testgen.propose --problem <id> --round 1 --dry-run` | 不呼叫 API，印出完整 prompt |

**寫新工具時建議：** 先用 `--pilot` 或暫存目錄的資料測，確認沒問題再跑正式輪次。正式 `rounds/` 裡的檔案一旦產生就是實驗紀錄。

---

## 7. 提示與注意事項

**程式上的坑（已踩過）：**
- 單一參數是 list 的題目（LC121），測資要寫成 `"args": ([...],)`，不能寫成 `"input": [...]`：`judge.py` 的截斷顯示只處理字串
- LC3 的 S+/S- 訓練池和 feedback 在 `testgen/` 根目錄（歷史紀錄），驗收池和 rounds 在 `problems/longest-substring/`。一律透過 `registry.pool_dir()` 取路徑，不要寫死
- `assess_problem.py` 在同一程序內直接呼叫解法（為了速度）；正式數字一律以 `run_eval` / `rounds.evaluate()`（經 executor）為準
- Windows 上程式寫出的檔案是 CRLF，git commit 時會出現 LF/CRLF 警告，屬正常
- Groq 模型會下架（Llama 系列已經沒了）。每次開工前可用 `--pilot` 確認模型還在

**建議（可以提升報告品質）：**
- **找一位沒參與設計 S- 池的組員，獨立再寫 2–3 個驗收用錯誤解。** 目前訓練池和驗收池都是同一人設計，可能有共同盲點，這是計畫裡列出的研究限制；換人獨立設計可以直接緩解
- 分流規則定案後寫進計畫，並註明日期（等於事先登記實驗方法）
- 跑實驗時順便記錄每輪的 token 用量和 API 秒數，報告可以算成本

**還沒處理的已知問題：**

| 問題 | 處理時機 |
|---|---|
| LC3 線上測資有 `"abba"` 漏洞（17 筆只有 1 筆抓到 `no_max_left`） | **實驗一紀錄凍結後**再補，避免改變人工版起點 |
| `CLAUDE.md` 的 AI 模型說明過時（寫 Llama，實際是 `gpt-oss-20b`） | 隨時可修 |
| Valid Parentheses 第 6 筆測資是空字串，違反題目限制 `1 ≤ s.length` | 不在實驗範圍，隨時可修 |
| 兩道新題已出現在前端題目列表，但只有官方範例測資 | **收斂前這個分支不能合併到 `main`**（main 會自動部署） |

---

## 8. 待全組決定的事

| 事項 | 選項 | 建議 |
|---|---|---|
| 分流規則 | 見任務 A | 用建議版本，實驗前定案 |
| 審核者是誰 | — | 固定一人；最好**不是**設計 S- 池的人 |
| `rounds/pilot/` 要不要 commit | commit／加入 `.gitignore` | 加入 `.gitignore`，試跑不屬於實驗紀錄 |
| 是否做 gpt-oss-20b vs 120b 比較 | 做／不做 | 時間不夠第一個砍 |
| 時程 | 計畫第三節估 8–9 週 | 依截止日回推，必要時照計畫的「範圍控制」砍題 |
