import ast
import asyncio

from executor import run_code
from problem import PROBLEMS

_DISPLAY_MAX_LEN = 50


def get_args(tc: dict) -> tuple:
    """從測資取出呼叫參數。優先用 'args'（多參數題目），否則把 'input' 包成單參數 tuple。"""
    return tc["args"] if "args" in tc else (tc["input"],)


def _display_input(tc: dict) -> str:
    if "args" in tc:
        s = ", ".join(repr(a) for a in tc["args"])
    else:
        s = tc["input"]
    return s if len(s) <= _DISPLAY_MAX_LEN else s[:_DISPLAY_MAX_LEN] + "..."


def compare(actual_str: str | None, expected) -> bool:
    """比對學生輸出（repr 字串）與預期值，數字類型有浮點容錯。"""
    if actual_str is None:
        return False
    try:
        actual_val = ast.literal_eval(actual_str)
    except (ValueError, SyntaxError):
        return actual_str == str(expected)
    if isinstance(expected, float) or isinstance(actual_val, float):
        try:
            return abs(float(actual_val) - float(expected)) < 1e-6
        except (TypeError, ValueError):
            return False
    return actual_val == expected


async def _run_one(code: str, method: str, tc: dict) -> dict:
    timeout = 10.0 if tc["is_stress"] else 5.0
    args = get_args(tc)
    exec_result = await run_code(code, method, args, timeout=timeout)

    actual = exec_result["actual"]
    passed = compare(actual, tc["expected"]) and exec_result["error_type"] is None

    return {
        "index": tc["index"],
        "input": _display_input(tc),
        "expected": tc["expected"],
        "actual": actual,
        "passed": passed,
        "error_type": exec_result["error_type"],
        "stderr": exec_result["stderr"],
    }


async def judge(code: str, problem_id: str) -> list[dict]:
    """
    對指定題目的全部 test case 並行執行學生程式碼並比對結果。
    永遠跑完全部，不中途停止（停在第一個失敗是前端的責任）。

    Returns:
        list[dict]: 結果（順序與該題 test_cases 一致），每筆包含
            index, input（截斷顯示）, expected, actual, passed, error_type, stderr
    """
    problem = PROBLEMS[problem_id]
    test_cases = problem["test_cases"]
    method = problem["method"]
    results = await asyncio.gather(*(_run_one(code, method, tc) for tc in test_cases))
    return list(results)
