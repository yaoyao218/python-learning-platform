import pytest
from judge import judge
from problem import TEST_CASES

CORRECT_CODE = """
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        char_map = {}
        left = 0
        result = 0
        for right, char in enumerate(s):
            if char in char_map and char_map[char] >= left:
                left = char_map[char] + 1
            char_map[char] = right
            result = max(result, right - left + 1)
        return result
"""

WRONG_CODE = """
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return len(s)
"""


@pytest.mark.asyncio
async def test_correct_code_all_pass():
    results = await judge(CORRECT_CODE)
    assert len(results) == len(TEST_CASES)
    assert all(r["passed"] for r in results)


@pytest.mark.asyncio
async def test_wrong_code_test2_fails():
    results = await judge(WRONG_CODE)
    assert len(results) == len(TEST_CASES)
    test2 = next(r for r in results if r["index"] == 2)
    assert not test2["passed"]
    assert test2["actual"] == "5"
    assert test2["expected"] == 1


@pytest.mark.asyncio
async def test_result_has_required_fields():
    results = await judge(WRONG_CODE)
    first = results[0]
    for field in ("index", "input", "expected", "actual", "passed", "error_type", "stderr"):
        assert field in first
