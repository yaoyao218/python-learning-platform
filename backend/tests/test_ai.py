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
    mock_response.choices[0].message.content = "這是 AI 提示"

    with patch("ai.client.chat.completions.create", new_callable=AsyncMock, return_value=mock_response) as mock_create:
        hint = await get_hint(results, TITLE, CONTEXT)

    assert hint == "這是 AI 提示"
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
