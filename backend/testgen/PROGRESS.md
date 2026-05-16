# 測資生成研究 — 進度紀錄

> 目標：把現有 `problem.py` 的 18 筆 hardcoded 測資，改成「資料驅動、可驗證品質」的版本。
> 方法論：依據論文 *CodeContests-O: Powering LLMs via Feedback-Driven Iterative Test Case Generation*。

## 為什麼要做這件事

平台目前的 18 筆測資是憑經驗挑的，沒有任何指標證明它能：
1. 不誤殺正確的學生解法（**TPR = True Positive Rate**）
2. 真的抓得到常見 bug（**TNR = True Negative Rate**）

引入論文方法的好處：每筆測資都可以量化它的「鑑別度」，
可以發現哪些測資其實沒抓到任何 bug（廢的），哪些 bug 從沒被任何測資抓到（漏網）。

## 階段 1：算現有 18 筆的 baseline TPR/TNR

### 設計選擇

- **重用平台既有的 `executor.run_code`**：不另寫執行器，這樣 baseline 數字真的反映平台跑學生程式碼的方式（含 AST 過濾、subprocess、timeout 都一致）。
- **S+ / S- 用獨立檔案**：每個解一個 `.py`，方便 diff、加註解、跟原始碼一起 commit。
- **不改 `problem.py`、`judge.py`、`executor.py`、`ai.py`**：testgen 是純離線工具，跟線上 API 完全解耦。

### 步驟

| 編號 | 動作 | 狀態 |
|---|---|---|
| 1 | 建 `backend/testgen/` 目錄與本 PROGRESS.md | ✅ 完成 |
| 2 | 寫 S+ 正確解池（sliding_window、hash_map、brute_force） | ✅ 完成 |
| 3 | 寫 S- 錯誤解池（6 種 bug pattern） | ✅ 完成 |
| 4 | 寫 `run_eval.py`（重用 executor.run_code） | ✅ 完成 |
| 5 | 跑 baseline 評估 → 寫入本檔 | ✅ 完成 |

### S+ / S- 池子內容

**S+（正確解，3 個）：**
- `sliding_window.py` — set 維護當前視窗，O(n)
- `hash_map.py` — dict 紀錄最後出現位置，O(n)
- `brute_force.py` — 暴力雙層迴圈，O(n²)

**S-（錯誤解，6 個常見 bug pattern）：**
- `count_unique.py` — 回傳 `len(set(s))`，誤讀題意
- `always_len.py` — 直接回傳 `len(s)`
- `off_by_one_window.py` — sliding window 但長度算 `right - left` 沒 +1
- `no_reset_left.py` — 遇重複直接清空 set、left 跳到 right
- `inner_return.py` — 內層迴圈就 return（CLAUDE.md 提到的經典陷阱）
- `no_return.py` — 演算法對但忘了 return

### 結果（baseline 數字）

| 指標 | 數值 | 解讀 |
|---|---|---|
| **TPR** | **1.0000** | 三個正解全過 18 筆——測資沒誤殺任何寫法 ✓ |
| **TNR** | **0.4907** | 平均只擋下 49% 錯誤——還有一半的 (測資×錯誤解) 對沒抓到 |
| 漏網的 S- | 0 個 | 每個錯誤解都至少有一筆測資抓到 ✓ |

**最關鍵的發現：**

| S- bug | 通過率 | 問題 |
|---|---|---|
| `count_unique.py` | 94.44% | **嚴重漏洞**——這是最像 LLM 會寫的解，但 18 筆裡只有 1 筆（`tmmzuxt`）抓到 |
| `no_reset_left.py` | 88.89% | 'abba' 的經典陷阱只有 case 12 抓到，其他幾乎沒覆蓋 |
| `inner_return.py` | 72.22% | CLAUDE.md 明確提到要抓的 bug，但只有 5/18 case 抓到 |
| `always_len.py` | 44.44% | 太多有重複字元的測資能輕鬆打掉它 |
| `off_by_one_window.py` | 5.56% | 幾乎全打掉，唯一漏網是空字串 |
| `no_return.py` | 0% | 完美擋下（executor 的 no_return 處理就抓） |

**每筆測資的鑑別度（共 6 個 S-）：**

```
高價值（4-5/6）：#3 pwwkew, #9 dvdf, #10 anviaj, #11 tmmzuxt, #13 aab
中價值（3/6）：  #1 abcabcbb, #2 bbbbb, #7 aa, #12 abba, #17 stress(a*50000)
低價值（1-2/6）：#4 '', #5 'a', #6 'au', #8 abcdefg, #14 'a b',
                #15 '!@#$%', #16 ' ', #18 a-z
```

低價值區塊有 **8 筆測資**（佔 44%），它們存在主要是「覆蓋邊界 / 字元類型」，但實際抓 bug 能力不高。

### baseline 對畢業專題的意義

1. **客觀證明：** 第一次有量化指標說「現有測資集大約半的鑑別力是浪費的」
2. **痛點具體化：** `count_unique` 是 LLM 最常寫的解，但 17/18 測資都讓它過——這直接證明「沒系統性方法選測資」會留下大洞
3. **論文方法的應用價值：** 接下來透過迭代設計新測資，可以把 TNR 從 0.49 拉到 0.85+，這個提升就是專題報告最強的數字

---

## 階段 2：Python 生成器 + 閉環迭代

### 設計選擇

| 決策 | 為什麼 |
|---|---|
| 用 Python 寫 `gen.py` 取代 testlib | 平台本身就是 Python，且 LC 3 輸入只是字串，testlib 反而是 overkill |
| 每個 mode 一個函式 | 直接 import 就能用，不用 subprocess |
| `commands_v{N}.txt` 一行一條命令 | 跟論文 `command_list` 一一對應，可 diff、可註解 |
| `synthesize.py` 跑命令 → 用 reference 算 expected → 輸出 `tests_v{N}.py` | 對應論文中 S* 補 ground truth 的步驟 |
| `run_eval.py` 加 `--tests <module>` 切換 | 同一套評估器跑 baseline / v1 / v2 / ... 直接比對 |

### 迭代軌跡

每一輪都根據前一輪 `feedback_v{N-1}.json` 的 `command_value` 跟 `S_minus_pass_rates` 修改命令清單與生成器。

| 版本 | 測資數 | TPR | TNR | 關鍵改動 |
|---|---|---|---|---|
| baseline | 18 | 1.000 | **0.4907** | 平台原本 hardcoded 的 18 筆 |
| v1 | 15 | 1.000 | **0.6889** | 加入 `doubled_distinct` / `abba_chain` / `late_window`；砍掉 baseline 低價值的單字元、空字串等 |
| v2 | 16 | 1.000 | **0.7292** | 加入 `carry_kill`（XYXZ pattern，dvdf 的一般化版本）取代效果不佳的 `abba_chain` |
| v3 | 17 | 1.000 | **0.7451** | 大量 `doubled_distinct` 想壓 count_unique，但反而稀釋了 no_reset_left 的命中比例 |
| **v4** | **17** | **1.000** | **0.8725** | **引入 `combo_kill`：一個字串同時殺 4 種 bug。10 個 combo_kill 案例全部拿 6/6** |

從 baseline 到 v4，**TNR 提升 +38.18 個百分點**，且 TPR 始終維持 1.0（沒誤殺正解）。

### 每輪迭代的洞察

**baseline → v1：** 砍 8 筆低價值（空字串、單字元、純標點），加 KILLER 模式。
TNR +20 ppt。

**v1 → v2：** 發現 `abba_chain` 沒實質殺到 `no_reset_left`——分析 baseline 後察覺真正抓到它的不是 `abba` (case 12) 而是 `dvdf` (case 9)。設計 `carry_kill` 實作 XYXZ pattern。
TNR +4 ppt。`no_reset_left` 通過率 87% → 63%。

**v2 → v3：** count_unique 反升（53% → 69%），因為 carry_kill 輸出的 set_size 通常等於 answer，會 TIE 過 count_unique。加大 doubled_distinct 想補洞，但結果稀釋了其他 bug 的命中比例。
TNR +1.5 ppt（停滯）。

**v3 → v4 突破口：** 改變策略，設計「同殺多 bug」的 `combo_kill` 模式——doubled 前綴（殺 count_unique）+ XYZX carry 中段（殺 no_reset_left）+ 長 distinct 尾段（殺 inner_return 跟 always_len）。10 個 combo_kill 案例每個都拿 6/6。
TNR +13 ppt 一口氣推上 0.87。

### v4 最終狀態

```
=== 每筆測資鑑別度（6 個 S- 中打掉幾個）===
  # 1  ██████  6/6  'beebcedfeaeadcebbfde'      ← random alphabet=abcdef
  # 2  ███···  3/6  'bcaddbaaadcabcc'           ← random
  # 3-10  ██████  6/6  (8 個 combo_kill 案例)
  #11-13 █████·  5/6  (3 個 carry_kill 案例)
  #14-15 █████·  5/6  (2 個 doubled_distinct)
  #16    ████··  4/6  late_window
  #17    ███···  3/6  stress_same (50000 個 'a')
```

```
=== S- 錯誤解最終通過率（越低越好）===
  ✓  always_len.py              0.00%   ← 全打掉
  ⚠  count_unique.py           35.29%
  ⚠  inner_return.py           11.76%
  ⚠  no_reset_left.py          29.41%
  ✓  no_return.py               0.00%   ← 全打掉
  ✓  off_by_one_window.py       0.00%   ← 全打掉
```

### 對畢業專題報告的關鍵數字

| 指標 | baseline | v4 | 改善 |
|---|---|---|---|
| TPR | 1.0000 | 1.0000 | 維持 |
| **TNR** | **0.4907** | **0.8725** | **+77.8% 相對提升** |
| 漏網 S-（false positive） | 0 | 0 | 維持 |
| 測資數 | 18 | 17 | 數量相當，品質躍升 |
| **count_unique 抓到率** | **5.56%** | **64.71%** | **+11.6 倍** |
| **no_reset_left 抓到率** | **11.11%** | **70.59%** | **+6.4 倍** |
| **inner_return 抓到率** | **27.78%** | **88.24%** | **+3.2 倍** |

### 產出檔案

```
backend/testgen/
├── PROGRESS.md             ← 本檔
├── gen.py                  ← Python 生成器（含 10 個 mode）
├── synthesize.py           ← 命令 → tests_v{N}.py 模組
├── run_eval.py             ← 評估器，支援 --tests 切換
├── commands_v1.txt ~ commands_v4.txt    ← 每輪命令清單
├── tests_v1.py ~ tests_v4.py            ← 每輪測資集
├── feedback_baseline.json, feedback_v1~v4.json   ← 反饋報告
├── solutions_correct/      ← S+ 池 (3 個正解)
└── solutions_wrong/        ← S- 池 (6 個常見 bug)
```

---

## 階段 3：導出 + 品質守門員

### 目標

把離線收斂出來的 `tests_v4.py` 變成可上線的 `problem.py`，並加 pytest 防止
未來有人改測資集時悄悄退化品質。

### 設計選擇

| 決策 | 為什麼 |
|---|---|
| 保留 LC 官方範例（abcabcbb / bbbbb / pwwkew） | 學生看題目敘述時熟悉這三筆，第一筆 AC 的成就感很重要 |
| v4 高鑑別度案例按 input 長度排序 | 學生看到的「第一個失敗」應是有教學意義的小字串，不是 50000 字元 stress |
| 壓力測試最後 | timeout 10 秒，跟 baseline 一致 |
| 用 `_note` 註解標明每筆案例來源 | code review 時看得到「這筆是 v4 combo_kill catch 6/6」 |
| 不直接覆寫 problem.py，先輸出 `problem_v4.py` | 讓人類審視後手動 swap，避免無腦覆蓋 |
| pytest 守門員從 `executor.run_code` 跑相同邏輯 | 跟線上判題用同一條 pipeline，斷言才有意義 |

### 產出

```
backend/
├── problem_v4.py                       ← 新測資集（17 筆，含官方範例 + v4 高鑑別度）
└── tests/
    └── test_problem_quality.py         ← pytest 守門員（4 個斷言）
```

### pytest 守門員的 4 個斷言

| 測試 | 斷言內容 | 違反時的修法 |
|---|---|---|
| `test_tpr_equals_one` | TPR = 1.0（任何 S+ 都該全過） | 找出哪筆測資讓正解輸出對不上預期 |
| `test_tnr_above_threshold` | TNR >= 0.85（論文方法收斂後該達到的水準） | 到 testgen/ 跑新一輪 v5、改進 commands.txt |
| `test_every_bug_caught_at_least_once` | 沒有任何 S- 通過所有測資 | 為漏網 bug 加新的 killer mode 到 gen.py |
| `test_minimum_test_case_count` | TEST_CASES 至少 10 筆 | 避免有人不小心砍到太少 |

### 守門員實測

```
==== 對 `problem` 跑測試（舊版 baseline）====
  TPR=1.0000  TNR=0.4907  cases=18
  ✓ test_tpr_equals_one: PASS
  ✗ test_tnr_above_threshold: FAIL：TNR=0.4907 < 0.85；
       通過率>=50% 的 bug：[count_unique 94%, inner_return 72%, no_reset_left 89%]
  ✓ test_every_bug_caught_at_least_once: PASS
  ✓ test_minimum_test_case_count: PASS

==== 對 `problem_v4` 跑測試（新版）====
  TPR=1.0000  TNR=0.8824  cases=17
  ✓ test_tpr_equals_one: PASS
  ✓ test_tnr_above_threshold: PASS
  ✓ test_every_bug_caught_at_least_once: PASS
  ✓ test_minimum_test_case_count: PASS
```

守門員邏輯驗證：**舊版被擋（正確）、新版放行（正確）**。

### 怎麼把新測資集上線

```bash
cd backend
# 1. 備份原本的（之後若想回滾）
cp problem.py problem_old.py

# 2. 用新測資集覆蓋
cp problem_v4.py problem.py

# 3. 跑 pytest 確認品質達標
pytest tests/test_problem_quality.py -v

# 4. 跑既有測試確認線上行為沒壞
pytest -v
```

`judge.py`、`executor.py`、`ai.py`、`main.py` 完全不用改——schema 跟原本 `problem.py` 一模一樣。

### 未來迭代流程

新發現一個學生 bug pattern 時：
1. 在 `testgen/solutions_wrong/` 加新的 `xxx_bug.py`
2. 在 `backend/` 跑 `python -m testgen.run_eval`——若新 bug 通過全部測資 → 守門員擋下
3. 在 `testgen/gen.py` 加對應 killer mode 或在 `commands_v5.txt` 加新命令
4. `python -m testgen.synthesize --commands testgen/commands_v5.txt --out testgen/tests_v5.py`
5. `python -m testgen.export_to_problem_py --tests testgen.tests_v5 --out problem_v5.py`
6. 跑 pytest 確認 → swap 上線

每一步都有客觀指標，不是憑感覺。

### 最終整套架構

```
backend/
├── problem.py                ← 線上跑的測資集（換成 v4 導出版後 TNR=0.88）
├── problem_v4.py             ← 待替換的新版
├── judge.py / executor.py / ai.py / main.py    ← 全部沒動
├── testgen/                  ← 離線工具
│   ├── gen.py                ← 10 個生成 mode（含 combo_kill）
│   ├── synthesize.py         ← 命令 → tests_v{N}.py
│   ├── run_eval.py           ← TPR/TNR 評估器
│   ├── export_to_problem_py.py   ← 收斂結果 → problem.py 格式
│   ├── commands_v1~v4.txt
│   ├── tests_v1~v4.py
│   ├── feedback_baseline.json + feedback_v1~v4.json
│   ├── solutions_correct/    ← 3 個 S+
│   └── solutions_wrong/      ← 6 個 S-
└── tests/
    ├── test_main.py          ← 既有測試（沒動）
    ├── test_executor.py
    ├── test_judge.py
    ├── test_ai.py
    └── test_problem_quality.py   ← 新增：論文方法的品質守門員
```

### 對畢業專題的最終結論

從 baseline TNR=0.4907 → v4 TNR=0.8824，**測資鑑別度提升 +79.8%**，
且全程 TPR 維持 1.0（沒誤殺任何正解）。

完整實驗章節數字：

| 階段 | TPR | TNR | 主要改動 | 累積進步 |
|---|---|---|---|---|
| baseline | 1.0000 | 0.4907 | 平台原 hardcoded 18 筆 | — |
| v1 | 1.0000 | 0.6889 | 砍低價值 + 加 KILLER 模式 | +20 ppt |
| v2 | 1.0000 | 0.7292 | 設計 carry_kill 模式 | +24 ppt |
| v3 | 1.0000 | 0.7451 | 大量 doubled_distinct（被稀釋） | +25 ppt |
| **v4** | **1.0000** | **0.8725** | **combo_kill：單字串同殺 4 bug** | **+38 ppt** |
| **export** | **1.0000** | **0.8824** | **加回 LC 官方範例後** | **+39 ppt** |

論文方法的三個核心元素全部實踐：
1. ✅ **客觀指標**：用 TPR/TNR 量化測資品質，不靠直覺
2. ✅ **閉環迭代**：每輪都用執行回饋（command_value、survivor analysis）驅動下一輪
3. ✅ **search-and-replace 精準改動**：不重做整個測資集，逐輪改命令/生成器

唯一沒做的論文元素：用 LLM 自動產生 `search_replace_generator_blocks`——
我們是手動分析回饋來決定下一輪改什麼。這是預留的延伸方向。

