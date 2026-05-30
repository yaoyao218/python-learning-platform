# Code-Blind AI 提示系統 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓 AI 提示系統完全不讀學生程式碼，改用測試結果（input/expected/actual）推斷 bug 類型並給蘇格拉底式提示。

**Architecture:** `ai.py` 的 `build_prompt` 與 `get_hint` 移除 `code` 參數，改為只依賴 `results` 陣列；四個 prompt 分支（syntax_error / runtime_error / no_return / wrong_answer）全部重寫；`main.py` 移除傳入 `req.code` 的兩個呼叫點。

**Tech Stack:** Python 3.11、FastAPI、openai SDK（Groq/Gemini 相容）、pytest + pytest-asyncio

---

## 影響檔案

| 檔案 | 動作 |
|---|---|
| `backend/tests/test_ai.py` | 修改：更新所有測試，移除 `code` 參數，更新斷言 |
| `backend/ai.py` | 修改：移除 `code` 參數，重寫四個 prompt 分支 |
| `backend/main.py` | 修改：移除兩個呼叫點中的 `req.code` |

---

## Task 1：更新測試（TDD 先寫失敗測試）

**Files:**
- Modify: `backend/tests/test_ai.py`

- [ ] **Step 1：將 `test_ai.py` 全部替換為以下內容**

```python
import pytest
from unittest.mock import AsyncMock, patch
from ai import build_prompt, get_hint


def make_result(index, input_val, expected, actual, passed, error_type=None, stderr=""):
    if passed:
        error_type = None
    return {
        "index": index,
        "input": input_val,
        "expected": expected,
        "actual": actual,
        "passed": passed,
        "error_type": error_type,
        "stderr": stderr,
    }


# --- build_prompt tests (no API call) ---

def test_build_prompt_all_passed_returns_none():
    results = [make_result(1, "abc", 3, "3", True)]
    assert build_prompt(results) is None


def test_build_prompt_syntax_error_uses_stderr():
    results = [
        make_result(1, "abc", 3, None, False, "syntax_error", "SyntaxError: invalid syntax (line 3)")
    ]
    prompt = build_prompt(results)
    assert "SyntaxError: invalid syntax (line 3)" in prompt


def test_build_prompt_runtime_error_uses_stderr_and_input():
    results = [
        make_result(1, "abc", 3, None, False, "runtime_error", "IndexError: list index out of range")
    ]
    prompt = build_prompt(results)
    assert "IndexError: list index out of range" in prompt
    assert "abc" in prompt  # 觸發錯誤的 input 也要出現


def test_build_prompt_no_return_mentions_return():
    results = [make_result(1, "abc", 3, None, False, "no_return")]
    prompt = build_prompt(results)
    assert "return" in prompt


def test_build_prompt_wrong_answer_contains_failure_data():
    results = [
        make_result(1, "abcabcbb", 3, "8", False, None),
        make_result(2, "bbbbb", 1, "5", False, None),
    ]
    prompt = build_prompt(results)
    assert "abcabcbb" in prompt
    assert "8" in prompt
    assert "3" in prompt


def test_build_prompt_wrong_answer_includes_all_failures():
    results = [
        make_result(1, "abcabcbb", 3, "3", True),
        make_result(2, "bbbbb", 1, "5", False, None),
        make_result(3, "pwwkew", 3, "6", False, None),
    ]
    prompt = build_prompt(results)
    assert "bbbbb" in prompt
    assert "pwwkew" in prompt
    assert "Actual: '6'" in prompt


def test_build_prompt_wrong_answer_ends_with_question_instruction():
    results = [make_result(1, "abcabcbb", 3, "8", False, None)]
    prompt = build_prompt(results)
    assert "問句" in prompt or "問題" in prompt


# --- get_hint tests (mock API) ---

@pytest.mark.asyncio
async def test_get_hint_returns_none_when_all_pass():
    results = [make_result(1, "abc", 3, "3", True)]
    hint = await get_hint(results)
    assert hint is None


@pytest.mark.asyncio
async def test_get_hint_calls_api_and_returns_content():
    results = [make_result(1, "abc", 3, "5", False, None)]

    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "這是 AI 提示"

    with patch("ai.client.chat.completions.create", return_value=mock_response) as mock_create:
        hint = await get_hint(results)

    assert hint == "這是 AI 提示"
    mock_create.assert_called_once()
    call_kwargs = mock_create.call_args
    assert call_kwargs.kwargs["messages"][0]["content"] == build_prompt(results)
```

- [ ] **Step 2：確認測試失敗（因為 `ai.py` 還用舊簽名）**

```bash
cd backend && pytest tests/test_ai.py -v 2>&1 | head -30
```

預期：多個 `TypeError` 或 `AssertionError`，表示測試正確捕捉到舊介面。

---

## Task 2：重寫 `ai.py`

**Files:**
- Modify: `backend/ai.py`

- [ ] **Step 1：將 `ai.py` 全部替換為以下內容**

```python
import os
import inspect
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY", "")
_use_gemini = bool(os.environ.get("GEMINI_API_KEY"))

client = AsyncOpenAI(
    api_key=_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/" if _use_gemini else "https://api.groq.com/openai/v1",
)

_MODEL = "gemini-2.0-flash" if _use_gemini else "llama-3.1-8b-instant"


def build_prompt(results: list[dict]) -> str | None:
    """
    組裝 AI prompt，完全不讀學生程式碼。
    - 全部通過 → 回傳 None
    - syntax_error  → 只送 stderr
    - runtime_error → 送觸發錯誤的 input + stderr
    - no_return     → 固定提示
    - wrong_answer  → 送所有失敗的 (input, expected, actual)，蘇格拉底式
    """
    failed = [r for r in results if not r["passed"]]
    if not failed:
        return None

    first_fail = failed[0]
    error_type = first_fail["error_type"]

    if error_type == "syntax_error":
        return f"""你是一個程式學習助教，幫助大一學生學習 Python。

學生在解 Longest Substring Without Repeating Characters 時發生語法錯誤：

{first_fail['stderr']}

請依序做三件事：
1. 用一句白話文解釋這個錯誤訊息的意思（20 字以內）
2. 提示學生根據行號找到問題位置
3. 用一個問題引導學生思考那個位置哪裡不對

規則：不要給出修正後的程式碼。繁體中文，語氣像陪學生 debug 的學長姐。120 字以內。"""

    if error_type == "runtime_error":
        return f"""你是一個程式學習助教，幫助大一學生學習 Python。

題目：Longest Substring Without Repeating Characters
（給一個字串，找不含重複字元的最長子字串長度）

學生程式在以下輸入時發生執行期錯誤：
- 輸入：{first_fail['input']!r}
- 錯誤訊息：{first_fail['stderr']}

請依序做三件事：
1. 用白話文解釋這個錯誤是什麼意思
2. 引導學生去看錯誤訊息中的行號
3. 問學生：「這個輸入有什麼特別的地方，可能讓程式在那行出錯？」

規則：不要給出修正後的程式碼。繁體中文，語氣友善鼓勵。150 字以內。"""

    if error_type == "no_return":
        return """你是一個程式學習助教，幫助大一學生學習 Python。

題目：Longest Substring Without Repeating Characters

學生的函式執行完後回傳了 None，代表答案沒有被傳出來。

請做兩件事：
1. 解釋 Python 函式為什麼需要 return 語句
2. 用一個問題讓學生思考：「你計算出來的答案，存在哪個變數裡？那個變數最後有沒有被回傳？」

規則：不要直接說程式碼要怎麼改。繁體中文，語氣像幫學生釐清思路的學長姐。100 字以內。"""

    # wrong_answer（error_type is None）
    def truncate(v, n=50):
        s = repr(v)
        return s if len(s) <= n else s[:n] + "..."

    n_fail = len(failed)
    failed_summary = "\n".join(
        f"- Input: {truncate(r['input'])} / Expected: {r['expected']} / Actual: {truncate(r['actual'])}"
        for r in failed
    )

    return f"""你是一個程式學習助教，專門幫助大一學生學習解題思維。

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
- 200 字以內"""


async def get_hint(results: list[dict]) -> str | None:
    """呼叫 Groq/Gemini API 取得 AI 提示。全部通過時回傳 None。API 失敗時回傳 None。"""
    prompt = build_prompt(results)
    if prompt is None:
        return None

    try:
        result = client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        response = await result if inspect.isawaitable(result) else result
        content = response.choices[0].message.content
        if content is None:
            return None
        return content
    except openai.OpenAIError:
        return None
```

- [ ] **Step 2：確認 test_ai.py 全部通過**

```bash
cd backend && pytest tests/test_ai.py -v
```

預期：全部 PASS，沒有 FAILED。

- [ ] **Step 3：Commit**

```bash
cd backend && git add ai.py tests/test_ai.py
git commit -m "feat: rewrite ai.py to code-blind prompt design

移除 build_prompt / get_hint 的 code 參數，
改用 results 的 (input, expected, actual) 推斷 bug 類型。
四個 prompt 分支全部重寫，wrong_answer 採蘇格拉底式提問。"
```

---

## Task 3：更新 `main.py`

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1：修改兩個呼叫點**

找到 `main.py` 第 35 行，將：
```python
hint = await get_hint(req.code, results)
```
改為：
```python
hint = await get_hint(results)
```

找到第 43 行的 session logger 呼叫，將：
```python
ai_prompt=build_prompt(req.code, results),
```
改為：
```python
ai_prompt=build_prompt(results),
```

- [ ] **Step 2：確認 main.py 相關測試通過**

```bash
cd backend && pytest tests/test_main.py -v
```

預期：全部 PASS。

- [ ] **Step 3：跑完整測試套件**

```bash
cd backend && pytest -v
```

預期：全部 PASS，包含 `test_problem_quality.py`。

- [ ] **Step 4：Commit**

```bash
git add backend/main.py
git commit -m "fix: remove code param from get_hint and build_prompt calls in main.py"
```

---

## Task 4：手動驗證（可選但建議）

- [ ] **Step 1：啟動後端**

```bash
cd backend && python -m uvicorn main:app --reload --port 8000
```

- [ ] **Step 2：送一個 wrong_answer 請求，確認 AI 不提及程式碼細節**

```bash
curl -s -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{"code": "class Solution:\n    def lengthOfLongestSubstring(self, s):\n        return len(set(s))"}' \
  | python3 -m json.tool | grep -A3 '"hint"'
```

預期：hint 內容是引導式問句，不含「你的第 X 行」或「你的變數 Y」。

- [ ] **Step 3：送一個 syntax_error 請求**

```bash
curl -s -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{"code": "class Solution:\n    def lengthOfLongestSubstring(self, s)\n        return 0"}' \
  | python3 -m json.tool | grep -A3 '"hint"'
```

預期：hint 說明語法錯誤意思，並引導學生看行號。
