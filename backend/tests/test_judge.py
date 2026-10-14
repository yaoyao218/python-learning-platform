import pytest
from judge import judge, compare
from problem import PROBLEMS

TEST_CASES = PROBLEMS["longest-substring"]["test_cases"]

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
    results = await judge(CORRECT_CODE, "longest-substring")
    assert len(results) == len(TEST_CASES)
    assert all(r["passed"] for r in results)


@pytest.mark.asyncio
async def test_wrong_code_test2_fails():
    results = await judge(WRONG_CODE, "longest-substring")
    assert len(results) == len(TEST_CASES)
    test2 = next(r for r in results if r["index"] == 2)
    assert not test2["passed"]
    assert test2["actual"] == "5"
    assert test2["expected"] == 1


@pytest.mark.asyncio
async def test_result_has_required_fields():
    results = await judge(WRONG_CODE, "longest-substring")
    first = results[0]
    for field in ("index", "input", "expected", "actual", "passed", "error_type", "stderr"):
        assert field in first


def test_compare_float_tolerance_accepts_int_actual():
    # 學生解法回傳 int（如 2）而非 float（如 2.0）時仍應判定為 PASS
    assert compare("2", 2.0) is True


def test_compare_float_tolerance_rejects_wrong_value():
    assert compare("1", 2.0) is False


def test_compare_bool():
    assert compare("True", True) is True
    assert compare("False", True) is False


@pytest.mark.asyncio
async def test_judge_results_include_is_stress():
    code = "class Solution:\n    def isValid(self, s):\n        return True\n"
    results = await judge(code, "valid-parentheses")
    flags = [tc["is_stress"] for tc in PROBLEMS["valid-parentheses"]["test_cases"]]
    assert [r["is_stress"] for r in results] == flags


@pytest.mark.asyncio
async def test_infinite_loop_stops_early_instead_of_waiting_for_every_case():
    """有一筆超時後，還沒開始的測資不再執行；54 道的題目不該等滿 7 批 × 5 秒。"""
    import time
    code = "class Solution:\n    def longestValidParentheses(self, s):\n        while True:\n            pass\n"
    t0 = time.perf_counter()
    results = await judge(code, "longest-valid-parentheses")
    elapsed = time.perf_counter() - t0
    assert len(results) == 54
    assert elapsed < 15
    ran = [r for r in results if not r.get("skipped")]
    skipped = [r for r in results if r.get("skipped")]
    assert skipped and all(r["error_type"] == "timeout" and not r["passed"] for r in skipped)
    assert results[0]["error_type"] == "timeout" and not results[0].get("skipped")
    assert max(r["index"] for r in ran) < min(r["index"] for r in skipped)


@pytest.mark.asyncio
async def test_no_case_is_skipped_without_a_timeout():
    code = "class Solution:\n    def longestValidParentheses(self, s):\n        return 0\n"
    results = await judge(code, "longest-valid-parentheses")
    assert not any(r.get("skipped") for r in results)
