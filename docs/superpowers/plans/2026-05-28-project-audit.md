# Project Audit — Bug Fix + Learning UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 5 content bugs across backend/README and add 2 learning UX features (success message + constraints) to the frontend.

**Architecture:** Backend changes are pure text (docstrings/comments), zero logic impact. Frontend changes extend existing Vue components — ResultPanel gets a success card, ProblemStatement gets a constraints section. All changes are isolated; no shared state or API contract changes.

**Tech Stack:** Python/FastAPI (backend), Vue 3 + Vite (frontend), pytest (testing)

**Spec:** `docs/superpowers/specs/2026-05-28-project-audit-design.md`

---

## File Map

| Action | File | Change |
|--------|------|--------|
| Modify | `backend/judge.py` | docstring: 18→17 (2 places) |
| Modify | `backend/ai.py` | comment: Grok→Groq/Gemini; docstring: 三種→4種/3個分支 |
| Modify | `backend/main.py` | remove Windows ProactorEventLoop (2 lines) |
| Modify | `README.md` | update 2 deployment URLs |
| Modify | `frontend/src/components/ResultPanel.vue` | add success card + `allPassed` computed |
| Modify | `frontend/src/App.vue` | add `constraints` array to `problem` object |
| Modify | `frontend/src/components/ProblemStatement.vue` | render constraints section |

---

### Task 1: Fix backend text bugs (judge.py, ai.py, main.py)

**Files:**
- Modify: `backend/judge.py:35-42`
- Modify: `backend/ai.py:21-27,109`
- Modify: `backend/main.py:1-8`

- [ ] **Step 1: Fix judge.py docstring**

In `backend/judge.py`, replace the `judge` function docstring (lines 34–43):

```python
async def judge(code: str) -> list[dict]:
    """
    對全部 17 組 test case 並行執行學生程式碼並比對結果。
    永遠跑完全部，不中途停止（停在第一個失敗是前端的責任）。

    Returns:
        list[dict]: 17 筆結果（順序與 TEST_CASES 一致），每筆包含
            index, input（截斷顯示）, expected, actual, passed, error_type, stderr
    """
```

- [ ] **Step 2: Fix ai.py — Grok typo and docstring**

In `backend/ai.py`:

**Line ~21, `build_prompt` docstring** — replace:
```python
    """
    組裝 AI prompt。
    - 全部通過 → 回傳 None
    - 依 first_fail 的 error_type 選擇三種 prompt 分支：
      * syntax_error / runtime_error → 簡化版，傳 stderr
      * no_return → 簡化版，提醒 return
      * None (wrong answer) → 完整版，傳所有失敗 cases 做 pattern 推斷
    """
```
with:
```python
    """
    組裝 AI prompt。
    - 全部通過 → 回傳 None
    - 依 first_fail 的 error_type（4 種）選擇 3 個 prompt 分支：
      * syntax_error / runtime_error → 簡化版，傳 stderr（error_label 不同）
      * no_return → 簡化版，提醒 return
      * None (wrong answer) → 完整版，傳所有失敗 cases 做 pattern 推斷
    """
```

**Line ~109, `get_hint` docstring** — replace:
```python
    """呼叫 Grok API 取得 AI 提示。全部通過時回傳 None。API 失敗時回傳 None。"""
```
with:
```python
    """呼叫 Groq/Gemini API 取得 AI 提示。全部通過時回傳 None。API 失敗時回傳 None。"""
```

- [ ] **Step 3: Fix main.py — remove ProactorEventLoop**

In `backend/main.py`, remove lines 5–6:
```python
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

After removal, also remove the now-unused `sys` and `asyncio` imports if they appear only for this purpose. Check: `asyncio` is used elsewhere? No — `asyncio` is not used anywhere else in main.py after this removal. `sys` is also only used here. Remove both imports.

The top of `main.py` should become:
```python
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from judge import judge
from ai import get_hint, build_prompt
```

- [ ] **Step 4: Run pytest to confirm no regressions**

```bash
cd backend
pytest -v
```

Expected: all tests pass (same result as before — these were text-only changes).

- [ ] **Step 5: Commit**

```bash
git add backend/judge.py backend/ai.py backend/main.py
git commit -m "fix: 修正 docstring 數字(18→17)、Grok→Groq、移除無用 ProactorEventLoop"
```

---

### Task 2: Fix README deployment URLs

**Files:**
- Modify: `README.md:189-190`

- [ ] **Step 1: Update the deployment table**

In `README.md`, find the deployment table (around line 187–192):

Replace:
```markdown
| 前端 | Vercel（自動部署） | https://python-learning-platform-one.vercel.app/ |
| 後端 | Render（自動部署） | https://python-learning-platform-quf0.onrender.com |
```
with:
```markdown
| 前端 | Vercel（自動部署） | https://python-learning-platform-chi.vercel.app/ |
| 後端 | Render（自動部署） | https://python-learning-platform-88vh.onrender.com |
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "fix: 更新 README 部署 URL 至現行正確網址"
```

---

### Task 3: ResultPanel — add success card when all tests pass

**Files:**
- Modify: `frontend/src/components/ResultPanel.vue`

- [ ] **Step 1: Add `allPassed` computed property**

In the `<script setup>` block, after the existing `passCount` computed, add:

```js
const allPassed = computed(() =>
  props.results.length > 0 && props.results.every((r) => r.passed)
)
```

- [ ] **Step 2: Add success card to template**

In the `<template>`, find the `<!-- AI Hint -->` section:

```html
      <!-- AI Hint -->
      <div v-if="hint" class="panel-section hint-section">
        <div class="section-header">
          <span class="section-label hint-label">AI 分析</span>
        </div>
        <div class="hint-body">{{ hint }}</div>
      </div>
```

Replace it with:

```html
      <!-- Success card (all passed, no hint) -->
      <div v-if="allPassed && !hint" class="panel-section success-section">
        <div class="section-header">
          <span class="section-label success-label">全部通過</span>
        </div>
        <div class="success-body">
          太棒了！你的解法通過了所有 {{ results.length }} 個測試案例。<br>
          試試看能不能讓解法更有效率？
        </div>
      </div>

      <!-- AI Hint -->
      <div v-if="hint" class="panel-section hint-section">
        <div class="section-header">
          <span class="section-label hint-label">AI 分析</span>
        </div>
        <div class="hint-body">{{ hint }}</div>
      </div>
```

- [ ] **Step 3: Add success styles**

In the `<style scoped>` block, after the `.hint-body` animation block, add:

```css
/* Success card */
.success-section { border-bottom: none; }

.success-label { color: var(--green); }

.success-body {
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-2);
  border-left: 2px solid var(--green);
  margin: 16px 20px;
  padding: 16px;
  background: var(--green-dim);
  border-radius: 0 4px 4px 0;
  animation: hint-in 0.4s ease both;
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ResultPanel.vue
git commit -m "feat: 全部通過時顯示成功回饋訊息"
```

---

### Task 4: Add Constraints to problem statement

**Files:**
- Modify: `frontend/src/App.vue:52-60`
- Modify: `frontend/src/components/ProblemStatement.vue`

- [ ] **Step 1: Add constraints to problem object in App.vue**

In `frontend/src/App.vue`, find the `problem` object in `<script setup>`:

```js
const problem = {
  title: 'Longest Substring Without Repeating Characters',
  description: '給定一個字串 <code>s</code>，請找出不含重複字元的<strong>最長子字串</strong>的長度。',
  examples: [
    { input: 'abcabcbb', output: 3, explanation: '最長不重複子字串為 "abc"，長度為 3' },
    { input: 'bbbbb',    output: 1, explanation: '最長子字串為 "b"，長度為 1' },
    { input: 'pwwkew',   output: 3, explanation: '最長不重複子字串為 "wke"，長度為 3' },
  ],
}
```

Replace with:

```js
const problem = {
  title: 'Longest Substring Without Repeating Characters',
  description: '給定一個字串 <code>s</code>，請找出不含重複字元的<strong>最長子字串</strong>的長度。',
  examples: [
    { input: 'abcabcbb', output: 3, explanation: '最長不重複子字串為 "abc"，長度為 3' },
    { input: 'bbbbb',    output: 1, explanation: '最長子字串為 "b"，長度為 1' },
    { input: 'pwwkew',   output: 3, explanation: '最長不重複子字串為 "wke"，長度為 3' },
  ],
  constraints: [
    '0 ≤ s.length ≤ 5 × 10⁴',
    's 只包含英文字母、數字、符號與空白字元',
  ],
}
```

- [ ] **Step 2: Render constraints in ProblemStatement.vue**

In `frontend/src/components/ProblemStatement.vue`, find the closing `</div>` of the `.problem` root (after the `.examples` grid). Add a constraints block **inside** `.problem`, after `.examples`:

```html
    <div v-if="problem.constraints && problem.constraints.length" class="constraints">
      <div class="constraints-header">限制條件</div>
      <ul class="constraints-list">
        <li v-for="(c, i) in problem.constraints" :key="i" class="constraint-item">
          {{ c }}
        </li>
      </ul>
    </div>
```

- [ ] **Step 3: Add constraints styles to ProblemStatement.vue**

In the `<style scoped>` block, add after the last rule:

```css
.constraints {
  padding: 16px 32px 20px;
  border-top: 1px solid var(--border);
}

.constraints-header {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-3);
  margin-bottom: 10px;
}

.constraints-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.constraint-item {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-2);
  padding-left: 14px;
  position: relative;
}

.constraint-item::before {
  content: '·';
  position: absolute;
  left: 0;
  color: var(--amber);
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.vue frontend/src/components/ProblemStatement.vue
git commit -m "feat: 題目加入 Constraints 限制條件欄位"
```

---

### Task 5: Final verification

- [ ] **Step 1: Run full pytest suite**

```bash
cd backend
pytest -v
```

Expected output (all green):
```
tests/test_ai.py::test_build_prompt_all_passed_returns_none PASSED
tests/test_ai.py::test_build_prompt_syntax_error_uses_stderr PASSED
tests/test_ai.py::test_build_prompt_runtime_error_uses_stderr PASSED
tests/test_ai.py::test_build_prompt_no_return_mentions_return PASSED
tests/test_ai.py::test_build_prompt_wrong_answer_focuses_on_output_gap PASSED
tests/test_ai.py::test_build_prompt_wrong_answer_includes_all_failures PASSED
tests/test_ai.py::test_get_hint_returns_none_when_all_pass PASSED
tests/test_ai.py::test_get_hint_calls_api_and_returns_content PASSED
tests/test_executor.py::... PASSED (all)
tests/test_judge.py::... PASSED (all)
tests/test_main.py::... PASSED (all)
tests/test_problem_quality.py::... PASSED (all)
```

- [ ] **Step 2: Verify frontend — constraints visible**

Start backend and frontend:
```bash
# Terminal 1
cd backend && python -m uvicorn main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

Open browser at `http://localhost:5173`. Confirm:
- Constraints section visible below the 3 example cards: `0 ≤ s.length ≤ 5 × 10⁴` and `s 只包含英文字母...`

- [ ] **Step 3: Verify frontend — success message**

Submit a correct solution. Example correct code to paste:

```python
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen = {}
        left = 0
        best = 0
        for right, ch in enumerate(s):
            if ch in seen and seen[ch] >= left:
                left = seen[ch] + 1
            seen[ch] = right
            best = max(best, right - left + 1)
        return best
```

Expected: result panel shows 17/17 通過 + green success card "太棒了！你的解法通過了所有 17 個測試案例。"

- [ ] **Step 4: Verify frontend — AI hint still works on failure**

Clear editor, leave only `pass`, submit. Expected: failure on test 1 + AI hint card appears (not the success card).

- [ ] **Step 5: Final commit (if any loose files)**

```bash
git status
# If clean, nothing to do. If any files unstaged:
git add <files>
git commit -m "chore: audit complete — 5 content bugs fixed, 2 learning UX features added"
```
