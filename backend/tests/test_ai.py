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
    assert build_prompt("code", results) is None


def test_build_prompt_syntax_error_uses_stderr():
    results = [
        make_result(1, "abc", 3, None, False, "syntax_error", "SyntaxError: invalid syntax (line 3)")
    ]
    prompt = build_prompt("code", results)
    assert "SyntaxError: invalid syntax (line 3)" in prompt
    assert "步驟一" not in prompt


def test_build_prompt_runtime_error_uses_stderr():
    results = [
        make_result(1, "abc", 3, None, False, "runtime_error", "IndexError: list index out of range")
    ]
    prompt = build_prompt("code", results)
    assert "IndexError: list index out of range" in prompt
    assert "步驟一" not in prompt


def test_build_prompt_no_return_mentions_return():
    results = [make_result(1, "abc", 3, None, False, "no_return")]
    prompt = build_prompt("code", results)
    assert "return" in prompt
    assert "步驟一" not in prompt


def test_build_prompt_wrong_answer_focuses_on_output_gap():
    # error_type=None means: ran successfully but returned wrong value
    results = [
        make_result(1, "abcabcbb", 3, "8", False, None),
        make_result(2, "bbbbb", 1, "5", False, None),
    ]
    prompt = build_prompt("code", results)
    # prompt should highlight the input/output gap, not use rigid step format
    assert "abcabcbb" in prompt   # first fail input
    assert "8" in prompt          # first fail actual output
    assert "3" in prompt          # first fail expected
    assert "步驟一" not in prompt  # new design: no rigid step headers


def test_build_prompt_wrong_answer_includes_all_failures():
    results = [
        make_result(1, "abcabcbb", 3, "3", True),       # passed
        make_result(2, "bbbbb", 1, "5", False, None),    # first fail (ran, wrong answer)
        make_result(3, "pwwkew", 3, "6", False, None),   # second fail
    ]
    prompt = build_prompt("code", results)
    # all failures should appear in the pattern section
    assert "bbbbb" in prompt
    assert "pwwkew" in prompt
    # first_fail actual should appear in its own labeled line
    assert "學生程式碼的輸出：5" in prompt
    # other failures appear in the failed_summary with Actual: format
    assert "Actual: '6'" in prompt


# --- get_hint tests (mock API) ---

@pytest.mark.asyncio
async def test_get_hint_returns_none_when_all_pass():
    results = [make_result(1, "abc", 3, "3", True)]
    hint = await get_hint("code", results)
    assert hint is None


@pytest.mark.asyncio
async def test_get_hint_calls_api_and_returns_content():
    results = [make_result(1, "abc", 3, "5", False, None)]  # ran fine, wrong answer

    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "這是 AI 提示"

    with patch("ai.client.chat.completions.create", return_value=mock_response) as mock_create:
        hint = await get_hint("code", results)

    assert hint == "這是 AI 提示"
    mock_create.assert_called_once()
    call_kwargs = mock_create.call_args
    assert call_kwargs.kwargs["messages"][0]["content"] == build_prompt("code", results)
