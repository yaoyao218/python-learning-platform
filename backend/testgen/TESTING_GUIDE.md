# 上線前端到端測試指引

新 `problem.py`（17 筆測資、TNR=0.88）已 swap 到位、`problem_old.py` 是備份。
此檔列出本機完整測試清單，**所有步驟都跑通才能 push 到 Vercel/Render**。

## 0. 前置（一次）

```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio          # 跑測試用
```

## 1. 後端單元測試（自動化）

```bash
cd backend
pytest -v
```

期望結果：所有測試 PASS，包括新增的：

```
tests/test_problem_quality.py::test_tpr_equals_one ........... PASSED
tests/test_problem_quality.py::test_tnr_above_threshold ...... PASSED
tests/test_problem_quality.py::test_every_bug_caught .......... PASSED
tests/test_problem_quality.py::test_minimum_test_case_count ... PASSED
```

如果 `test_tnr_above_threshold` FAIL：表示你或他人改測資後鑑別度掉了，
回到 `testgen/` 跑一輪迭代。

## 2. 啟動後端

```bash
cd backend
uvicorn main:app --reload --port 8000
```

確認 stdout 看到 `Uvicorn running on http://0.0.0.0:8000`。

## 3. 啟動前端

```bash
cd frontend
npm install   # 第一次跑
npm run dev
```

打開瀏覽器到 `http://localhost:5173`（或 5174）。

## 4. 端到端手動測試清單

把下面 6 種典型 bug 解貼進 Monaco 編輯器，按提交，**逐個確認預期行為**。

---

### Test 4-A：正確解（應全綠 18/17 PASS）

```python
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen = set()
        left = best = 0
        for right in range(len(s)):
            while s[right] in seen:
                seen.remove(s[left])
                left += 1
            seen.add(s[right])
            best = max(best, right - left + 1)
        return best
```

**預期：** 17/17 PASS，沒有 AI 提示框出現。

---

### Test 4-B：直接回 `len(s)`（最弱 bug，馬上被擋）

```python
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return len(s)
```

**預期：**
- 第一個失敗：`index=1`，`input='abcabcbb'`，`expected=3, got 8`
- AI 提示分支：`wrong_answer`（提示「檢查你的演算法是否真的有處理重複字元」）
- 通過 0/17

---

### Test 4-C：誤讀題意，回 `len(set(s))`

```python
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return len(set(s))
```

**預期：**
- 第一個失敗：`index=3`，`input='pwwkew'`，`expected=3, got 4`
- AI 提示應該點到「你算的是不重複字元的總數，不是『連續的最長不重複子字串』」
- 通過 5/17

---

### Test 4-D：內層迴圈就 return（典型 LLM bug）

```python
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        best = 0
        seen = set()
        for ch in s:
            if ch in seen:
                return best
            seen.add(ch)
            best = len(seen)
        return best
```

**預期：**
- 第一個失敗：`index=3`，`input='pwwkew'`，`expected=3, got 2`
- AI 提示分支：`wrong_answer`，會特別提醒 `return` 縮排與迴圈早退（ai.py 第 104 行那段）
- 通過 2/17

---

### Test 4-E：忘記 return（觸發 no_return 分支）

```python
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen = set()
        left = best = 0
        for right in range(len(s)):
            while s[right] in seen:
                seen.remove(s[left])
                left += 1
            seen.add(s[right])
            best = max(best, right - left + 1)
        # 故意不 return
```

**預期：**
- 全部 17 筆 fail，error_type 全是 `no_return`
- AI 提示分支：`no_return`（提醒函式要 return 值）

---

### Test 4-F：語法錯誤（觸發 syntax_error 分支）

```python
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int
        return 0
```

**預期：**
- 全部 fail，error_type 是 `syntax_error`
- AI 提示分支：`syntax_error`（指出冒號錯誤）

---

## 5. 觀察重點

| 觀察項 | 期望 |
|---|---|
| `result.input` 在前端顯示 | 短字串完整顯示；長字串會被截斷加 `...` |
| 第一個失敗 index | 應該落在 #1-3（LC 範例）上，學生熟悉 |
| AI 提示是否出現 | 不通過時應該有；全通過時不該有 |
| 載入速度 | 第一次提交可能 5-30 秒（Render 冷啟動），之後 <3 秒 |

## 6. 跑完後

如果以上 6 項全部如預期：

```bash
# 移除備份（確認新版穩定後）
rm backend/problem_old.py    # 或保留作為歷史

# 加入 testgen 跟新 problem 進 git
git add backend/testgen/ backend/problem.py backend/tests/test_problem_quality.py
git commit -m "feat: 套用論文方法重做測資集（TNR 0.49 → 0.88）"
git push   # 自動觸發 Vercel/Render 重新部署
```

## 7. 線上驗證

部署完成後到 https://python-learning-platform-one.vercel.app/ 重複 Test 4-A、4-B、4-C，確認線上跟本機行為一致。

---

## 回滾方案

若上線後發現問題：

```bash
cd backend
cp problem_old.py problem.py    # 回到 18 筆 baseline
git commit -am "revert: 暫時回滾測資集"
git push
```
