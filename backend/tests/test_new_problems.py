"""驗證 Valid Parentheses / Median of Two Sorted Arrays 兩題新測資的行為：
正解應全過，指定的錯誤解法應在指定的 index 第一次失敗。
"""
import pytest
from judge import judge
from problem import PROBLEMS

VP_CASES = PROBLEMS["valid-parentheses"]["test_cases"]
MEDIAN_CASES = PROBLEMS["median-two-sorted-arrays"]["test_cases"]


def first_fail_index(results):
    fails = [r for r in results if not r["passed"]]
    return fails[0]["index"] if fails else None


# ---------- Valid Parentheses ----------

VP_CORRECT = """
class Solution:
    def isValid(self, s: str) -> bool:
        pairs = {')': '(', ']': '[', '}': '{'}
        stack = []
        for ch in s:
            if ch in pairs:
                if not stack or stack.pop() != pairs[ch]:
                    return False
            else:
                stack.append(ch)
        return not stack
"""

VP_BUG_COUNT_ONLY = """
class Solution:
    def isValid(self, s: str) -> bool:
        return (
            s.count('(') == s.count(')')
            and s.count('[') == s.count(']')
            and s.count('{') == s.count('}')
        )
"""

VP_BUG_STACK_NOT_CHECKED = """
class Solution:
    def isValid(self, s: str) -> bool:
        pairs = {')': '(', ']': '[', '}': '{'}
        stack = []
        for ch in s:
            if ch in pairs:
                if stack and stack[-1] == pairs[ch]:
                    stack.pop()
            else:
                stack.append(ch)
        return True  # 忘記檢查 stack 是否為空
"""


@pytest.mark.asyncio
async def test_valid_parentheses_correct_all_pass():
    results = await judge(VP_CORRECT, "valid-parentheses")
    assert len(results) == len(VP_CASES)
    assert all(r["passed"] for r in results)


@pytest.mark.asyncio
async def test_valid_parentheses_count_only_bug_fails_at_5():
    results = await judge(VP_BUG_COUNT_ONLY, "valid-parentheses")
    assert first_fail_index(results) == 5


@pytest.mark.asyncio
async def test_valid_parentheses_stack_not_checked_bug_fails_at_4():
    results = await judge(VP_BUG_STACK_NOT_CHECKED, "valid-parentheses")
    assert first_fail_index(results) == 4


# ---------- Median of Two Sorted Arrays ----------

MEDIAN_CORRECT = """
from typing import List

class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = sorted(nums1 + nums2)
        n = len(merged)
        mid = n // 2
        if n % 2 == 1:
            return float(merged[mid])
        return (merged[mid - 1] + merged[mid]) / 2
"""

MEDIAN_BUG_FORGOT_SORT = """
from typing import List

class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = nums1 + nums2  # 忘記排序
        n = len(merged)
        mid = n // 2
        if n % 2 == 1:
            return float(merged[mid])
        return (merged[mid - 1] + merged[mid]) / 2
"""

MEDIAN_BUG_IGNORES_NUMS2 = """
from typing import List

class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = sorted(nums1)  # 忘記把 nums2 併進來
        n = len(merged)
        if n == 0:
            return 0.0
        mid = n // 2
        if n % 2 == 1:
            return float(merged[mid])
        return (merged[mid - 1] + merged[mid]) / 2
"""


@pytest.mark.asyncio
async def test_median_correct_all_pass():
    results = await judge(MEDIAN_CORRECT, "median-two-sorted-arrays")
    assert len(results) == len(MEDIAN_CASES)
    assert all(r["passed"] for r in results)


@pytest.mark.asyncio
async def test_median_correct_int_return_still_passes_float_tolerance():
    # 正解對奇數長度回傳 float(...)；驗證即使解法直接回傳 int，compare() 仍容錯判 PASS
    code = """
from typing import List

class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = sorted(nums1 + nums2)
        n = len(merged)
        mid = n // 2
        if n % 2 == 1:
            return merged[mid]  # 故意回傳 int 而非 float
        return (merged[mid - 1] + merged[mid]) / 2
"""
    results = await judge(code, "median-two-sorted-arrays")
    assert all(r["passed"] for r in results)


@pytest.mark.asyncio
async def test_median_forgot_sort_bug_fails_at_1():
    results = await judge(MEDIAN_BUG_FORGOT_SORT, "median-two-sorted-arrays")
    assert first_fail_index(results) == 1


@pytest.mark.asyncio
async def test_median_ignores_nums2_bug_fails():
    results = await judge(MEDIAN_BUG_IGNORES_NUMS2, "median-two-sorted-arrays")
    assert first_fail_index(results) is not None
