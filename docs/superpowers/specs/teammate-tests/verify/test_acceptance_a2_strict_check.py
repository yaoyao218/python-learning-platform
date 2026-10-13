# -*- coding: utf-8 -*-
"""A2 AI 程式嚴格檢查的驗收測試（負責人用）。

約定的介面（見 teammate-guide.md 的 A2 任務卡）：
    executor.check_forbidden(code: str, strict: bool = False) -> str | None
      * strict=False（預設）：行為與現在完全相同（學生提交路徑不變）
      * strict=True：除原有規則外，再擋下 open、eval、exec、__import__ 的使用（包含別名，例如 o = open）
"""
import inspect

import pytest

import _support as S

PROBLEMS = ["longest-substring", "best-time-stock", "longest-valid-parentheses"]

STRICT_BLOCKED = {
    "open 呼叫": "x = open('a.txt')",
    "eval 呼叫": "y = eval('1+1')",
    "exec 呼叫": "exec('pass')",
    "__import__ 呼叫": "m = __import__('math')",
    "open 別名": "o = open\no('a.txt')",
    "eval 在函式內": "def f():\n    return eval('1')",
}


@pytest.fixture(scope="module")
def ex():
    if not S.EXECUTOR_FILE.exists():
        pytest.fail(f"找不到 {S.EXECUTOR_FILE}", pytrace=False)
    return S.load_module("executor_under_test", S.EXECUTOR_FILE)


def test_signature(ex):
    sig = inspect.signature(ex.check_forbidden)
    assert "strict" in sig.parameters, "check_forbidden 必須有參數 strict"
    assert sig.parameters["strict"].default is False, "strict 的預設值必須是 False"


@pytest.mark.parametrize("label,snippet", list(STRICT_BLOCKED.items()))
def test_strict_blocks(ex, label, snippet):
    msg = ex.check_forbidden(snippet, strict=True)
    assert msg, f"strict=True 應擋下：{label}"


@pytest.mark.parametrize("label,snippet", list(STRICT_BLOCKED.items()))
def test_default_unchanged_for_student_path(ex, label, snippet):
    assert ex.check_forbidden(snippet) is None, f"預設（學生路徑）不應改變行為：{label} 在預設模式下不該被擋"
    assert ex.check_forbidden(snippet, strict=False) is None


def test_default_still_blocks_forbidden_modules(ex):
    for mod in ("os", "sys", "subprocess", "socket", "multiprocessing", "threading", "ctypes", "importlib"):
        assert ex.check_forbidden(f"import {mod}"), f"預設模式仍應擋下 import {mod}"
        assert ex.check_forbidden(f"from {mod} import x"), f"預設模式仍應擋下 from {mod} import"
        assert ex.check_forbidden(f"import {mod}", strict=True), f"strict 模式也要擋下 import {mod}"


@pytest.mark.parametrize("pid", PROBLEMS)
def test_strict_does_not_over_block_real_solutions(ex, pid):
    for (kind, name), code in S.pools(pid).items():
        assert ex.check_forbidden(code, strict=True) is None, f"strict 誤擋了正常的人工解法 {pid}/{kind}/{name}"


def test_normal_code_passes_strict(ex):
    code = "class Solution:\n    def f(self, s):\n        seen = set()\n        return len(s)\n"
    assert ex.check_forbidden(code, strict=True) is None
