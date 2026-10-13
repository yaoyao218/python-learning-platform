import pytest
from unittest.mock import AsyncMock, patch
from ai import build_prompt, get_hint

TITLE = "Longest Substring Without Repeating Characters"
CONTEXT = '給一個字串，找「不含重複字元的最長子字串」的長度。例如："abcabcbb" → 3，因為 "abc" 是最長的無重複子字串。'


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
    assert build_prompt(results, TITLE, CONTEXT) is None


def test_build_prompt_syntax_error_uses_stderr():
    results = [
        make_result(1, "abc", 3, None, False, "syntax_error", "SyntaxError: invalid syntax (line 3)")
    ]
    prompt = build_prompt(results, TITLE, CONTEXT)
    assert "SyntaxError: invalid syntax (line 3)" in prompt


def test_build_prompt_runtime_error_uses_stderr_and_input():
    results = [
        make_result(1, "abc", 3, None, False, "runtime_error", "IndexError: list index out of range")
    ]
    prompt = build_prompt(results, TITLE, CONTEXT)
    assert "IndexError: list index out of range" in prompt
    assert "abc" in prompt  # 觸發錯誤的 input 也要出現


def test_build_prompt_no_return_mentions_return():
    results = [make_result(1, "abc", 3, None, False, "no_return")]
    prompt = build_prompt(results, TITLE, CONTEXT)
    assert "return" in prompt


def test_build_prompt_wrong_answer_contains_failure_data():
    results = [
        make_result(1, "abcabcbb", 3, "8", False, None),
        make_result(2, "bbbbb", 1, "5", False, None),
    ]
    prompt = build_prompt(results, TITLE, CONTEXT)
    assert "abcabcbb" in prompt
    assert "8" in prompt
    assert "3" in prompt


def test_build_prompt_wrong_answer_includes_all_failures():
    results = [
        make_result(1, "abcabcbb", 3, "3", True),
        make_result(2, "bbbbb", 1, "5", False, None),
        make_result(3, "pwwkew", 3, "6", False, None),
    ]
    prompt = build_prompt(results, TITLE, CONTEXT)
    assert "bbbbb" in prompt
    assert "pwwkew" in prompt
    assert "Actual: '6'" in prompt


def test_build_prompt_wrong_answer_ends_with_question_instruction():
    results = [make_result(1, "abcabcbb", 3, "8", False, None)]
    prompt = build_prompt(results, TITLE, CONTEXT)
    assert "問句" in prompt or "問題" in prompt


def test_build_prompt_uses_given_problem_title_and_context():
    results = [make_result(1, "()", True, "False", False, None)]
    prompt = build_prompt(results, "Valid Parentheses", "括號是否有效配對")
    assert "Valid Parentheses" in prompt
    assert "括號是否有效配對" in prompt


# --- get_hint tests (mock API) ---

@pytest.mark.asyncio
async def test_get_hint_returns_none_when_all_pass():
    results = [make_result(1, "abc", 3, "3", True)]
    hint = await get_hint(results, TITLE, CONTEXT)
    assert hint is None


@pytest.mark.asyncio
async def test_get_hint_calls_api_and_returns_content():
    results = [make_result(1, "abc", 3, "5", False, None)]

    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "這是 AI 提示，你覺得問題在哪裡？"

    with patch("ai.client.chat.completions.create", new_callable=AsyncMock, return_value=mock_response) as mock_create:
        hint = await get_hint(results, TITLE, CONTEXT)

    assert hint == "這是 AI 提示，你覺得問題在哪裡？"
    mock_create.assert_called_once()
    call_kwargs = mock_create.call_args
    assert call_kwargs.kwargs["messages"][0]["content"] == build_prompt(results, TITLE, CONTEXT)


# --- timeout（執行超時）---

def make_timeout(index, input_val, expected, is_stress):
    r = make_result(index, input_val, expected, None, False, "timeout", "執行超時（超過時間限制）")
    r["is_stress"] = is_stress
    return r


def test_build_prompt_timeout_does_not_ask_for_line_number():
    """超時沒有 traceback，不能叫學生去看行號。"""
    prompt = build_prompt([make_timeout(1, "abc", 3, False)], TITLE, CONTEXT)
    assert "去看錯誤訊息中的行號" not in prompt
    assert "超過時間限制" in prompt


def test_build_prompt_timeout_on_short_input_suggests_infinite_loop():
    prompt = build_prompt([make_timeout(1, "abc", 3, False)], TITLE, CONTEXT)
    assert "無窮迴圈" in prompt


def test_build_prompt_timeout_on_stress_input_talks_about_efficiency():
    prompt = build_prompt([make_timeout(18, "abab...", 79, True)], TITLE, CONTEXT)
    assert "效率" in prompt


def test_build_prompt_wrong_answer_summary_excludes_timeouts():
    """前面答錯、後面壓力測資超時：超時那筆的 Actual 是 None，不該混進數值 pattern 分析。"""
    results = [
        make_result(1, "abcabcbb", 3, "8", False, None),
        make_timeout(18, "ababab...", 79, True),
    ]
    prompt = build_prompt(results, TITLE, CONTEXT)
    assert "abcabcbb" in prompt
    assert "ababab" not in prompt


# --- hint_guard: output-side safety net (second line of defense) ---

@pytest.mark.asyncio
async def test_get_hint_falls_back_when_llm_leaks_code():
    """就算 LLM 沒聽話、夾了程式碼，學生也不該看到它。"""
    results = [make_result(1, "abc", 3, "5", False, None)]

    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = (
        "你可以這樣寫：\n```python\ndef lengthOfLongestSubstring(self, s):\n    return len(set(s))\n```"
    )

    with patch("ai.client.chat.completions.create", new_callable=AsyncMock, return_value=mock_response):
        hint = await get_hint(results, TITLE, CONTEXT)

    from hint_guard import FALLBACK_HINT
    assert hint == FALLBACK_HINT
    assert "```" not in hint and "def " not in hint


@pytest.mark.asyncio
async def test_get_hint_falls_back_when_no_question_mark():
    """沒有問句代表 AI 直接給了答案而不是引導，一樣不該原樣顯示。"""
    results = [make_result(1, "abc", 3, "5", False, None)]

    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "你的程式碼邏輯是對的，只是少了一個條件判斷。"

    with patch("ai.client.chat.completions.create", new_callable=AsyncMock, return_value=mock_response):
        hint = await get_hint(results, TITLE, CONTEXT)

    from hint_guard import FALLBACK_HINT
    assert hint == FALLBACK_HINT


# --- masking + hint_guard 串接 ---
# 有 problem_id 時 masking 已經檢查過 ``` 程式碼區塊（遮罩或保留），
# hint_guard 不該再因為看到 ``` 就整段換掉，只檢查區塊以外的文字。

_FULL_SOLUTION_HINT = (
    "參考看看這個寫法：\n"
    "```python\n"
    "class Solution:\n"
    "    def lengthOfLongestSubstring(self, s):\n"
    "        seen = {}\n"
    "        left = best = 0\n"
    "        for right, c in enumerate(s):\n"
    "            if c in seen and seen[c] >= left:\n"
    "                left = seen[c] + 1\n"
    "            seen[c] = right\n"
    "            best = max(best, right - left + 1)\n"
    "        return best\n"
    "```\n"
    "你覺得 left 為什麼要這樣移動？"
)

_MASKED_CODE = (
    "class Solution:\n"
    "    def lengthOfLongestSubstring(self, s):\n"
    "        seen = {}\n"
    "        left = best = 0\n"
    "        # TODO\n"
    "        return best\n"
)


def _llm_reply(text):
    response = AsyncMock()
    response.choices = [AsyncMock()]
    response.choices[0].message.content = text
    return response


@pytest.mark.asyncio
async def test_masked_code_block_survives_hint_guard():
    """masking 遮罩成功的程式碼區塊，不該被 hint_guard 整段換掉。"""
    results = [make_result(1, "abc", 3, "5", False, None)]
    replies = [_llm_reply(_FULL_SOLUTION_HINT), _llm_reply(_MASKED_CODE)]

    with patch("ai.client.chat.completions.create", new_callable=AsyncMock, side_effect=replies):
        hint = await get_hint(results, TITLE, CONTEXT, problem_id="longest-substring")

    from hint_guard import FALLBACK_HINT
    assert hint != FALLBACK_HINT
    assert "# TODO" in hint
    assert "seen[c] = right" not in hint          # 關鍵邏輯已經被遮掉
    assert "你覺得 left 為什麼要這樣移動？" in hint  # 程式碼以外的文字保留


@pytest.mark.asyncio
async def test_harmless_code_block_survives_hint_guard():
    """跑不過任何測資的小片段，masking 會保留，hint_guard 也不該擋。"""
    results = [make_result(1, "abc", 3, "5", False, None)]
    text = "想想看這行在做什麼：\n```python\nseen = set()\n```\n它能幫你記住什麼？"

    with patch("ai.client.chat.completions.create", new_callable=AsyncMock, return_value=_llm_reply(text)):
        hint = await get_hint(results, TITLE, CONTEXT, problem_id="longest-substring")

    assert hint == text


@pytest.mark.asyncio
async def test_unfenced_code_still_blocked_with_masking():
    """AI 沒用 ``` 包起來的程式碼，masking 看不到，要由 hint_guard 擋下。"""
    results = [make_result(1, "abc", 3, "5", False, None)]
    text = "你可以寫 def lengthOfLongestSubstring(self, s): return len(set(s)) 試試看？"

    with patch("ai.client.chat.completions.create", new_callable=AsyncMock, return_value=_llm_reply(text)):
        hint = await get_hint(results, TITLE, CONTEXT, problem_id="longest-substring")

    from hint_guard import FALLBACK_HINT
    assert hint == FALLBACK_HINT


@pytest.mark.asyncio
async def test_missing_question_still_blocked_with_masking():
    results = [make_result(1, "abc", 3, "5", False, None)]
    text = "你的程式碼邏輯是對的，只是少了一個條件判斷。"

    with patch("ai.client.chat.completions.create", new_callable=AsyncMock, return_value=_llm_reply(text)):
        hint = await get_hint(results, TITLE, CONTEXT, problem_id="longest-substring")

    from hint_guard import FALLBACK_HINT
    assert hint == FALLBACK_HINT


# --- C1：提示加入虛擬碼（題目材料；學生程式碼仍然不給 AI）---

import inspect  # noqa: E402

from hint_guard import check_hint_quality, guard  # noqa: E402
from problem import PROBLEMS  # noqa: E402

PSEUDO = PROBLEMS["best-time-stock"]["pseudocode"]["text"]


def test_build_prompt_has_no_student_code_parameter():
    params = set(inspect.signature(build_prompt).parameters)
    assert params == {"results", "problem_title", "problem_context", "pseudocode"}


def test_build_prompt_wrong_answer_includes_pseudocode_and_step_rules():
    results = [make_result(1, "abba", 2, "3", False)]
    prompt = build_prompt(results, TITLE, CONTEXT, pseudocode=PSEUDO)
    assert PSEUDO in prompt
    assert "步驟編號" in prompt
    assert "不要整段複述虛擬碼" in prompt


def test_build_prompt_without_pseudocode_is_unchanged():
    results = [make_result(1, "abba", 2, "3", False)]
    assert build_prompt(results, TITLE, CONTEXT) == build_prompt(results, TITLE, CONTEXT, pseudocode=None)
    assert "虛擬碼" not in build_prompt(results, TITLE, CONTEXT)


@pytest.mark.parametrize("pid", ["longest-substring", "best-time-stock", "longest-valid-parentheses"])
def test_pseudocode_itself_not_mistaken_for_code(pid):
    text = PROBLEMS[pid]["pseudocode"]["text"]
    problems = check_hint_quality(text + "\n你覺得呢？", pseudocode=text)
    assert not [p for p in problems if "程式碼" in p or "def" in p or "class" in p]


def test_hint_citing_a_step_passes_guard():
    hint = "想想看第 4 步：當 p 比 lowest 小時，lowest 會變成多少？之後的利潤要怎麼算？"
    assert guard(hint, pseudocode=PSEUDO) == (hint, [])


def test_hint_restating_whole_pseudocode_is_blocked():
    hint = "照著做就好：\n" + PSEUDO + "\n這樣懂了嗎？"
    safe, problems = guard(hint, pseudocode=PSEUDO)
    assert safe != hint
    assert any("複述虛擬碼" in p for p in problems)


@pytest.mark.asyncio
async def test_get_hint_passes_pseudocode_to_prompt_and_guard():
    results = [make_result(1, [2, 4, 1], 2, "0", False)]
    reply = "照著做：\n" + PSEUDO + "\n懂了嗎？"
    with patch("ai.client.chat.completions.create", new_callable=AsyncMock, return_value=_llm_reply(reply)) as mock_create:
        hint = await get_hint(results, TITLE, CONTEXT, pseudocode=PSEUDO)
    assert PSEUDO in mock_create.call_args.kwargs["messages"][0]["content"]
    assert hint != reply


@pytest.mark.asyncio
async def test_get_hint_uses_low_reasoning_effort_on_gpt_oss():
    """gpt-oss 預設推理會把 token 用光、回傳空內容（K3）；提示一律用 low。"""
    results = [make_result(1, "abba", 2, "3", False)]
    with patch("ai._MODEL", "openai/gpt-oss-20b"), \
         patch("ai.client.chat.completions.create", new_callable=AsyncMock,
               return_value=_llm_reply("想想看？")) as mock_create:
        await get_hint(results, TITLE, CONTEXT)
    assert mock_create.call_args.kwargs.get("reasoning_effort") == "low"


@pytest.mark.asyncio
async def test_get_hint_no_reasoning_effort_on_gemini():
    results = [make_result(1, "abba", 2, "3", False)]
    with patch("ai._MODEL", "gemini-2.0-flash"), \
         patch("ai.client.chat.completions.create", new_callable=AsyncMock,
               return_value=_llm_reply("想想看？")) as mock_create:
        await get_hint(results, TITLE, CONTEXT)
    assert "reasoning_effort" not in mock_create.call_args.kwargs
