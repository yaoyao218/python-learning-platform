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
    assert result["error_type"] == "timeout"
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


# ── 學生的 print 不能干擾判題 ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_print_in_method_does_not_affect_answer():
    code = """
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        print("debug", s)
        return len(set(s))
"""
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] is None
    assert result["actual"] == "3"


@pytest.mark.asyncio
async def test_module_level_print_does_not_affect_answer():
    code = """
print("hello")
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return 3
"""
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] is None
    assert result["actual"] == "3"


@pytest.mark.asyncio
async def test_print_then_return_none_is_no_return():
    code = """
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        print(len(set(s)))
"""
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] == "no_return"
    assert result["actual"] is None


@pytest.mark.asyncio
async def test_runtime_error_line_number_points_to_student_code():
    code = """class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return s[999]
"""
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] == "runtime_error"
    assert "line 3" in result["stderr"]
    assert "IndexError" in result["stderr"]


# ── 學生程式碼不能讀到後端的密鑰 ─────────────────────────────────────────────

def _returning(expr: str) -> str:
    return f"""
class Solution:
    def lengthOfLongestSubstring(self, s: str):
        return {expr}
"""


@pytest.mark.asyncio
async def test_env_vars_not_inherited(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_SECRET_SHOULD_NOT_LEAK")
    code = _returning("__import__('os').environ.get('GROQ_API_KEY')")
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert "SECRET" not in (result["actual"] or "") + result["stderr"]


@pytest.mark.asyncio
async def test_cannot_read_parent_proc_environ():
    code = _returning("open(f'/proc/{__import__(\"os\").getppid()}/environ').read()")
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] == "runtime_error"
    assert result["actual"] is None


@pytest.mark.asyncio
async def test_cannot_read_dotenv_file(tmp_path):
    secret = tmp_path / ".env"
    secret.write_text("GROQ_API_KEY=gsk_SECRET_SHOULD_NOT_LEAK")
    code = _returning(f"open({str(secret)!r}).read()")
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] == "runtime_error"
    assert "SECRET" not in result["stderr"]


@pytest.mark.asyncio
async def test_cannot_spawn_subprocess_via_dynamic_import():
    code = _returning("__import__('subprocess').run(['echo', 'pwned'], capture_output=True).stdout")
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] == "runtime_error"
    assert result["actual"] is None


@pytest.mark.asyncio
async def test_stdlib_imports_still_work():
    code = """
from typing import List
from collections import defaultdict
import heapq, bisect, math
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return len(defaultdict(int, {c: 1 for c in s}))
"""
    result = await run_code(code, "lengthOfLongestSubstring", ("abc",))
    assert result["error_type"] is None
    assert result["actual"] == "3"
