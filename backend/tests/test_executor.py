import pytest
from executor import run_code


@pytest.mark.asyncio
async def test_correct_code_returns_output():
    code = """
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return len(set(s))
"""
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] is None
    assert result["actual"] == "3"
    assert result["stderr"] == ""


@pytest.mark.asyncio
async def test_syntax_error():
    code = """
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return len(s  # missing paren
"""
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] == "syntax_error"
    assert result["actual"] is None
    assert "SyntaxError" in result["stderr"]


@pytest.mark.asyncio
async def test_runtime_error():
    code = """
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return s[999]
"""
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] == "runtime_error"
    assert result["actual"] is None


@pytest.mark.asyncio
async def test_no_return():
    code = """
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        pass
"""
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] == "no_return"
    assert result["actual"] is None


@pytest.mark.asyncio
async def test_forbidden_import_os():
    code = """
import os
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return 1
"""
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] == "runtime_error"
    assert "os" in result["stderr"]


@pytest.mark.asyncio
async def test_timeout():
    code = """
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        while True:
            pass
"""
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",), timeout=1.0)
    assert result["error_type"] == "runtime_error"
    assert "超時" in result["stderr"]


@pytest.mark.asyncio
async def test_multi_arg_call():
    code = """
class Solution:
    def findMedianSortedArrays(self, nums1, nums2) -> float:
        merged = sorted(nums1 + nums2)
        n = len(merged)
        mid = n // 2
        if n % 2 == 1:
            return float(merged[mid])
        return (merged[mid - 1] + merged[mid]) / 2
"""
    result = await run_code(code, "findMedianSortedArrays", ([1, 3], [2]))
    assert result["error_type"] is None
    assert result["actual"] == "2.0"


@pytest.mark.asyncio
async def test_bool_return():
    code = """
class Solution:
    def isValid(self, s: str) -> bool:
        return len(s) % 2 == 0
"""
    result = await run_code(code, "isValid", ("()",))
    assert result["error_type"] is None
    assert result["actual"] == "True"
