"""
test_masking.py — masking 模組的單元與整合測試

asyncio_mode = auto（pytest.ini 已設定），所有 async def test_* 自動執行。

純函式測試（extract_code_blocks、_wrap_if_needed）：不需要 async。
LLM 相關測試（mask_code、sanitize_hint）：用 AsyncMock mock，不需要真實 API Key。
整合測試（is_full_solution）：實際呼叫 judge()，不需要 mock，不需要網路。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from masking import (
    MIN_PASS_TO_FLAG,
    _BLOCK_PLACEHOLDER,
    _wrap_if_needed,
    extract_code_blocks,
    is_full_solution,
    mask_code,
    sanitize_hint,
)


# ═══════════════════════════════════════════════════════════════════════════
# extract_code_blocks
# ═══════════════════════════════════════════════════════════════════════════


def test_extract_no_blocks():
    """純文字，無任何 code block → 空 list。"""
    text = "這是一段提示文字，沒有任何程式碼區塊。"
    assert extract_code_blocks(text) == []


def test_extract_one_block():
    """單一 ```python block，正確抽出 fence 與內容。"""
    code = "def foo():\n    return 1"
    text = f"看這段程式碼：\n```python\n{code}\n```\n試試看。"
    blocks = extract_code_blocks(text)
    assert len(blocks) == 1
    original_fence, code_content = blocks[0]
    assert code in code_content
    assert "```" in original_fence


def test_extract_multiple_blocks():
    """多個 block，全部被抽出，順序正確。"""
    text = "第一段：\n```python\nx = 1\n```\n第二段：\n```\ny = 2\n```"
    blocks = extract_code_blocks(text)
    assert len(blocks) == 2
    assert "x = 1" in blocks[0][1]
    assert "y = 2" in blocks[1][1]


def test_extract_no_language_tag():
    """無 language tag 的 block 也要抓到。"""
    text = "```\nresult = 42\n```"
    blocks = extract_code_blocks(text)
    assert len(blocks) == 1
    assert "result = 42" in blocks[0][1]


# ═══════════════════════════════════════════════════════════════════════════
# _wrap_if_needed
# ═══════════════════════════════════════════════════════════════════════════


def test_wrap_if_needed_bare_def():
    """裸 def（無 self、無 class）→ 在後面附加 class Solution 委派包裝，原始程式碼不縮排。"""
    code = "def lengthOfLongestSubstring(s: str) -> int:\n    return len(s)"
    result = _wrap_if_needed(code, "lengthOfLongestSubstring")
    # 原始程式碼完整保留（未縮排）
    assert "def lengthOfLongestSubstring(s: str) -> int:" in result
    # 後面附加了 class Solution 委派
    assert "class Solution:" in result
    assert "    def lengthOfLongestSubstring(self, *args):" in result
    assert "        return lengthOfLongestSubstring(*args)" in result
    # 原始函式出現在 class 之前
    assert result.index("def lengthOfLongestSubstring(s:") < result.index("class Solution:")


def test_wrap_if_needed_already_wrapped():
    """已有 class Solution → 不重複包裝，原樣回傳。"""
    code = "class Solution:\n    def lengthOfLongestSubstring(self, s):\n        return 0"
    result = _wrap_if_needed(code, "lengthOfLongestSubstring")
    assert result == code
    # 不應該出現巢狀 class
    assert result.count("class Solution") == 1


def test_wrap_if_needed_syntax_error():
    """語法錯誤的 code → 原樣回傳，不 crash。"""
    code = "def foo(\n    broken syntax here"
    result = _wrap_if_needed(code, "foo")
    assert result == code


def test_wrap_if_needed_no_matching_def():
    """有 def 但方法名不符 → fallback 用最後一個頂層函式做委派包裝。

    新邏輯：沒有名稱完全匹配的函式時，使用最後一個頂層函式作為 delegate target。
    這讓 AI 給出不同命名的函式時仍能被 judge 執行（雖然語意上可能不對）。
    """
    code = "def some_other_func(s):\n    return 0"
    result = _wrap_if_needed(code, "lengthOfLongestSubstring")
    # 原始程式碼保留
    assert "def some_other_func(s):" in result
    # fallback：用 some_other_func 做委派
    assert "class Solution:" in result
    assert "    def lengthOfLongestSubstring(self, *args):" in result
    assert "        return some_other_func(*args)" in result


# ═══════════════════════════════════════════════════════════════════════════
# is_full_solution — 整合測試（實際呼叫 judge，不需要網路）
# ═══════════════════════════════════════════════════════════════════════════


CORRECT_SOLUTION = """\
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen = {}
        left = 0
        max_len = 0
        for right, ch in enumerate(s):
            if ch in seen and seen[ch] >= left:
                left = seen[ch] + 1
            seen[ch] = right
            max_len = max(max_len, right - left + 1)
        return max_len
"""

WRONG_SOLUTION = """\
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return len(set(s))
"""


async def test_is_full_solution_correct():
    """正確解法應回傳 True（通過筆數 >= MIN_PASS_TO_FLAG）。"""
    result = await is_full_solution(CORRECT_SOLUTION, "longest-substring")
    assert result is True


async def test_is_full_solution_wrong():
    """count_unique bug 解法，多筆測資會失敗，應回傳 False。

    注意：此解法對前 3 筆 LeetCode 官方範例（abcabcbb=3, bbbbb=1, pwwkew=3）
    其中 bbbbb 通過（set大小=1），abcabcbb 失敗（set大小=8≠3）。
    若 MIN_PASS_TO_FLAG=1，此測試依賴至少一筆失敗才有意義。
    這裡換用一個保證全部失敗的解法。
    """
    # always_len bug：永遠回傳字串長度，全部測資都失敗（因為多數長度 ≠ 答案）
    always_len = """\
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return len(s)
"""
    # always_len 在 bbbbb（len=5, expected=1）時就失敗，但 abcabcbb（len=8≠3）也失敗
    # 重點是：若 MIN_PASS_TO_FLAG=1 且任一筆通過就視為洩漏，
    # 我們需要一個「完全不會通過任何一筆」的解法
    never_pass = """\
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return -9999
"""
    result = await is_full_solution(never_pass, "longest-substring")
    assert result is False


async def test_is_full_solution_bad_problem_id():
    """無效 problem_id → 回傳 False，不 crash。"""
    result = await is_full_solution(CORRECT_SOLUTION, "nonexistent-problem")
    assert result is False


async def test_is_full_solution_bare_def_auto_wrapped():
    """裸 def（無 self、無 class）應被自動補委派包裝後正確執行。"""
    bare_def_no_self = """\
def lengthOfLongestSubstring(s: str) -> int:
    seen = {}
    left = 0
    max_len = 0
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1
        seen[ch] = right
        max_len = max(max_len, right - left + 1)
    return max_len
"""
    result = await is_full_solution(bare_def_no_self, "longest-substring")
    assert result is True


# ═══════════════════════════════════════════════════════════════════════════
# mask_code — mock LLM，不需要 API Key
# ═══════════════════════════════════════════════════════════════════════════


def _make_mock_client(content: str | None):
    """建立回傳固定 content 的 mock AsyncOpenAI client。"""
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client


async def test_mask_code_success():
    """mock LLM 回傳 masked code，mask_code 應回傳該內容。"""
    masked_code = "class Solution:\n    def lengthOfLongestSubstring(self, s):\n        # TODO"
    mock_client = _make_mock_client(masked_code)

    result = await mask_code(
        code=CORRECT_SOLUTION,
        title="Longest Substring Without Repeating Characters",
        client=mock_client,
        model="test-model",
    )
    assert result == masked_code
    mock_client.chat.completions.create.assert_called_once()


async def test_mask_code_strips_fence():
    """LLM 回傳有 markdown fence 包裝時，mask_code 應自動去除。"""
    inner = "class Solution:\n    def foo(self):\n        # TODO"
    content_with_fence = f"```python\n{inner}\n```"
    mock_client = _make_mock_client(content_with_fence)

    result = await mask_code(
        code="some code",
        title="Test",
        client=mock_client,
        model="test-model",
    )
    assert result == inner
    assert "```" not in result


async def test_mask_code_api_failure():
    """LLM 拋出 OpenAIError → mask_code 回傳 None。"""
    import openai

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=openai.OpenAIError("API error")
    )

    result = await mask_code(
        code=CORRECT_SOLUTION,
        title="Test",
        client=mock_client,
        model="test-model",
    )
    assert result is None


async def test_mask_code_none_content():
    """LLM 回傳 None content → mask_code 回傳 None。"""
    mock_client = _make_mock_client(None)
    result = await mask_code("code", "Title", mock_client, "model")
    assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# sanitize_hint — mock is_full_solution & mask_code 以獨立測試流程
# ═══════════════════════════════════════════════════════════════════════════

_HINT_WITH_CODE = f"看這段程式碼：\n```python\n{CORRECT_SOLUTION.strip()}\n```\n試試看。"
_HINT_NO_CODE = "你的方向是對的，但有個邊界條件沒處理好。"

MOCK_CLIENT = MagicMock()
MOCK_MODEL = "test-model"


async def test_sanitize_hint_none_input():
    """hint=None → 直接回傳 None。"""
    result = await sanitize_hint(None, "longest-substring", "Title", MOCK_CLIENT, MOCK_MODEL)
    assert result is None


async def test_sanitize_hint_no_code():
    """hint 無程式碼 block → 原樣回傳。"""
    result = await sanitize_hint(_HINT_NO_CODE, "longest-substring", "Title", MOCK_CLIENT, MOCK_MODEL)
    assert result == _HINT_NO_CODE


async def test_sanitize_hint_not_full_solution():
    """code block 跑不過任何測資 → 原樣回傳。"""
    with patch("masking.is_full_solution", new=AsyncMock(return_value=False)):
        result = await sanitize_hint(_HINT_WITH_CODE, "longest-substring", "Title", MOCK_CLIENT, MOCK_MODEL)
    assert result == _HINT_WITH_CODE


async def test_sanitize_hint_leaks_masked_ok():
    """偵測洩漏 → mask 成功且遮蔽後不再洩漏 → 替換 block 後回傳。"""
    masked = "class Solution:\n    def lengthOfLongestSubstring(self, s):\n        # TODO"

    # is_full_solution 第一次（偵測）回 True，第二次（驗證）回 False
    call_count = {"n": 0}

    async def mock_is_full(code, pid):
        call_count["n"] += 1
        return call_count["n"] == 1  # 第一次 True，之後 False

    with patch("masking.is_full_solution", new=mock_is_full):
        with patch("masking.mask_code", new=AsyncMock(return_value=masked)):
            result = await sanitize_hint(_HINT_WITH_CODE, "longest-substring", "Title", MOCK_CLIENT, MOCK_MODEL)

    assert result is not None
    assert result != _HINT_WITH_CODE          # 有被修改
    assert "# TODO" in result                 # masked code 出現在 hint 裡
    assert CORRECT_SOLUTION.strip() not in result  # 原始解法被移除


async def test_sanitize_hint_mask_fails():
    """偵測洩漏 → mask_code 回傳 None → 只把該程式碼區塊替換成佔位文字，其餘文字保留。"""
    with patch("masking.is_full_solution", new=AsyncMock(return_value=True)):
        with patch("masking.mask_code", new=AsyncMock(return_value=None)):
            result = await sanitize_hint(_HINT_WITH_CODE, "longest-substring", "Title", MOCK_CLIENT, MOCK_MODEL)
    assert result is not None
    assert _BLOCK_PLACEHOLDER in result        # 佔位文字出現
    assert "看這段程式碼：" in result           # 區塊前的文字保留
    assert "試試看。" in result                 # 區塊後的文字保留
    assert "```" not in result                 # 原始程式碼 fence 已被移除


async def test_sanitize_hint_mask_still_passes():
    """偵測洩漏 → mask 成功但遮蔽後仍能通過 → 只把該區塊替換成佔位文字，其餘文字保留。"""
    masked = "# 這段遮蔽不完全"

    # 兩次 is_full_solution 都回 True（洩漏 + 遮蔽後仍洩漏）
    with patch("masking.is_full_solution", new=AsyncMock(return_value=True)):
        with patch("masking.mask_code", new=AsyncMock(return_value=masked)):
            result = await sanitize_hint(_HINT_WITH_CODE, "longest-substring", "Title", MOCK_CLIENT, MOCK_MODEL)
    assert result is not None
    assert _BLOCK_PLACEHOLDER in result        # 佔位文字出現
    assert "看這段程式碼：" in result           # 區塊前的文字保留
    assert "試試看。" in result                 # 區塊後的文字保留


# ═══════════════════════════════════════════════════════════════════════════
# 新增：真實 judge 整合測試（裸函式，不 monkeypatch）
# ═══════════════════════════════════════════════════════════════════════════


async def test_is_full_solution_correct_bare_func_no_self():
    """正確的裸函式（無 self、無 class）→ is_full_solution 應回傳 True。

    使用真實 judge，不 monkeypatch。
    委派包裝邏輯：_wrap_if_needed 附加 class Solution 後，
    executor 執行 Solution().lengthOfLongestSubstring("abcabcbb") 應得到 3。
    """
    correct_bare = """\
def lengthOfLongestSubstring(s):
    seen = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1
        seen[ch] = right
        best = max(best, right - left + 1)
    return best
"""
    result = await is_full_solution(correct_bare, "longest-substring")
    assert result is True


async def test_is_full_solution_wrong_bare_func_no_self():
    """明顯錯誤的裸函式（return 0）→ is_full_solution 應回傳 False。

    使用真實 judge，不 monkeypatch。
    所有測資 expected >= 1，因此 return 0 全部失敗，passed_count = 0 < MIN_PASS_TO_FLAG。
    """
    wrong_bare = """\
def lengthOfLongestSubstring(s):
    return 0
"""
    result = await is_full_solution(wrong_bare, "longest-substring")
    assert result is False
