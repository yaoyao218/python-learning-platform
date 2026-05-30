# Code-Blind AI 提示系統設計

## 核心理念

學生提交程式碼後，AI **完全不看程式碼**，只根據測試結果給引導式提示。

17 筆測資讓各種 bug 確實失敗（高 TNR），失敗時產生的 `(input, expected, actual)` 三元組本身就足以讓 AI 推斷根本原因——每種 bug 的 actual 值規律都足夠清晰。

提示風格採蘇格拉底式問句，結尾必須是問題，讓學生有下一步可以主動思考。

---

## 架構

### 職責分工（不變的部分）

| 檔案 | 職責 |
|---|---|
| `executor.py` | 執行一筆程式碼，偵測 syntax / runtime 錯誤 |
| `judge.py` | 並行跑 17 筆測資，回傳完整 results 陣列 |
| `main.py` | HTTP 入口，呼叫 judge + ai，回傳結果 |

### 唯一主要變動：`ai.py`

移除 `code` 參數，改為只依賴 `results` 陣列。

---

## 函式簽名變更

```python
# 舊
def build_prompt(code: str, results: list[dict]) -> str | None
async def get_hint(code: str, results: list[dict]) -> str | None

# 新
def build_prompt(results: list[dict]) -> str | None
async def get_hint(results: list[dict]) -> str | None
```

`main.py` 唯一改動（第 35 行）：

```python
# 舊
hint = await get_hint(req.code, results)

# 新
hint = await get_hint(results)
```

session logger 同步移除 `ai_prompt=build_prompt(req.code, results)` 中的 `req.code`。

---

## 資料流

```
學生提交 code
    ↓
executor.py：語法檢查（compile）+ 執行 subprocess
    ↓
judge.py：17 筆測資並行比對 → results[]
    ↓
ai.py：只讀 results，不讀 code
    ├─ syntax_error  → 送 stderr
    ├─ runtime_error → 送 first_fail.input + stderr
    ├─ no_return     → 固定文字，無動態資料
    └─ wrong_answer  → 送所有失敗的 (input, expected, actual)
    ↓
前端顯示提示
```

---

## 四個 Prompt 分支

### 1. `syntax_error`

送入資料：`first_fail['stderr']`

```
你是一個程式學習助教，幫助大一學生學習 Python。

學生在解 Longest Substring Without Repeating Characters 時發生語法錯誤：

{stderr}

請依序做三件事：
1. 用一句白話文解釋這個錯誤訊息的意思（20 字以內）
2. 提示學生根據行號找到問題位置
3. 用一個問題引導學生思考那個位置哪裡不對

規則：不要給出修正後的程式碼。繁體中文，語氣像陪學生 debug 的學長姐。120 字以內。
```

---

### 2. `runtime_error`

送入資料：`first_fail['input']`、`first_fail['stderr']`

```
你是一個程式學習助教，幫助大一學生學習 Python。

題目：Longest Substring Without Repeating Characters
（給一個字串，找不含重複字元的最長子字串長度）

學生程式在以下輸入時發生執行期錯誤：
- 輸入：{input}
- 錯誤訊息：{stderr}

請依序做三件事：
1. 用白話文解釋這個錯誤是什麼意思
2. 引導學生去看錯誤訊息中的行號
3. 問學生：「這個輸入有什麼特別的地方，可能讓程式在那行出錯？」

規則：不要給出修正後的程式碼。繁體中文，語氣友善鼓勵。150 字以內。
```

---

### 3. `no_return`

送入資料：無（固定 prompt）

```
你是一個程式學習助教，幫助大一學生學習 Python。

題目：Longest Substring Without Repeating Characters

學生的函式執行完後回傳了 None，代表答案沒有被傳出來。

請做兩件事：
1. 解釋 Python 函式為什麼需要 return 語句
2. 用一個問題讓學生思考：「你計算出來的答案，存在哪個變數裡？那個變數最後有沒有被回傳？」

規則：不要直接說程式碼要怎麼改。繁體中文，語氣像幫學生釐清思路的學長姐。100 字以內。
```

---

### 4. `wrong_answer`

送入資料：所有失敗的 `(input, expected, actual)` 三元組

AI 自行從數值規律推斷 bug 類型，決定提示深度：

| 觀察到的規律 | AI 應推斷的方向 |
|---|---|
| actual ≈ 輸入字串長度 | 沒有理解「子字串」概念 |
| actual 持續大於 expected | 可能計算整體不重複字元數，而非視窗長度 |
| 只通過前 1～2 筆 | 程式可能提早終止或提早回傳 |
| 特定測資通過，特定失敗 | 滑動視窗左邊界沒有正確移動 |
| actual 恆比 expected 少 1 | 視窗大小計算有 off-by-one |

```
你是一個程式學習助教，專門幫助大一學生學習解題思維。

題目：Longest Substring Without Repeating Characters
定義：給一個字串，找「不含重複字元的最長子字串」的長度。
例如："abcabcbb" → 3，因為 "abc" 是最長的無重複子字串。

學生有 {n_fail}/17 筆測資失敗，以下是全部失敗案例：
{failed_summary}

請先分析這些失敗案例的數值 pattern（不要輸出分析過程），
再根據推斷出的理解落差，用一個蘇格拉底式問題引導學生。

提示深度原則：
- 學生答案方向完全錯誤 → 從觀念入手（子字串的定義、滑動視窗的概念）
- 學生方向正確但細節錯 → 從具體數字追問（為什麼這個 input 得到這個 output）

輸出規則：
- 只輸出給學生看的提示，不要輸出分析
- 不要給出正確程式碼或完整演算法步驟
- 結尾必須是一個問句
- 繁體中文，語氣像在討論題目的學長姐
- 200 字以內
```

---

## 診斷能力確認

17 筆測資對 6 種已知 bug 的可辨別性（資料來自 `feedback_current.json`）：

| Bug | actual 規律 | AI 可辨別？ |
|---|---|---|
| `no_return` | actual = None | ✅ error_type 直接攔截，不進 wrong_answer |
| `always_len` | actual = 輸入字串長度 | ✅ 數值規律明顯 |
| `off_by_one_window` | actual = expected − 1 | ✅ 差值恆定 |
| `count_unique` | actual = 整串不重複字元數 | ✅ 數值規律明顯 |
| `inner_return` | 只通過測資 1、2 | ✅ pass pattern 獨特 |
| `no_reset_left` | 通過測資 1、2、3、7、13 | ✅ pass pattern 獨特 |

---

## 不在本次範圍內

- `executor.py`、`judge.py` 邏輯不動
- 前端不動
- 測資（`problem.py`）不動
- session logger 只移除 `code` 參數，結構不變
