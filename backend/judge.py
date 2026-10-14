import ast
import asyncio
import json

from executor import run_code
from problem import PROBLEMS

_DISPLAY_MAX_LEN = 50


def get_args(tc: dict) -> tuple:
    """從測資取出呼叫參數。優先用 'args'（多參數題目），否則把 'input' 包成單參數 tuple。"""
    return tc["args"] if "args" in tc else (tc["input"],)


def _show(value) -> str:
    """字串加雙引號（與題目範例 s = "..." 一致），其他型別照 Python 寫法（例如 [7, 1, 5]）。"""
    return json.dumps(value, ensure_ascii=False) if isinstance(value, str) else repr(value)


def _display_input(tc: dict) -> str:
    """給前端與 AI 看的輸入。字串會帶引號、陣列不帶，才分得出 "[1, 2]"（字串）和 [1, 2]（陣列）。"""
    s = ", ".join(_show(a) for a in get_args(tc))
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
        "is_stress": tc["is_stress"],
    }


async def judge(code: str, problem_id: str) -> list[dict]:
    """
    對指定題目的全部 test case 並行執行學生程式碼並比對結果。
    一般會跑完全部（停在第一個失敗是前端的責任）；例外是**執行超時**：
    只要有一筆超時，還沒開始的測資就不再執行，直接標成 skipped。
    否則無窮迴圈會讓每一筆都等滿 5 秒，54 道測資 ÷ 8 個執行緒要 40 秒以上，逼近前端 60 秒逾時。
    測資依編號依序開始，所以被略過的一定排在已執行的後面，前端顯示的「第一個失敗」仍是真的結果。

    Returns:
        list[dict]: 結果（順序與該題 test_cases 一致），每筆包含
            index, input（截斷顯示）, expected, actual, passed, error_type, stderr, is_stress
            （被略過的測資另有 skipped=True，error_type 為 "timeout"）
    """
    problem = PROBLEMS[problem_id]
    test_cases = problem["test_cases"]
    method = problem["method"]
    slots = asyncio.Semaphore(_PARALLEL)
    timed_out = asyncio.Event()

    async def run(tc: dict) -> dict:
        async with slots:
            if timed_out.is_set():
                return _skipped(tc)
            result = await _run_one(code, method, tc)
            if result["error_type"] == "timeout":
                timed_out.set()
            return result

    results = await asyncio.gather(*(run(tc) for tc in test_cases))
    return list(results)


# 與 executor 的執行緒數相同：同時最多跑這麼多筆，其餘排隊（排隊中的才有機會被略過）
_PARALLEL = 8


def _skipped(tc: dict) -> dict:
    return {
        "index": tc["index"],
        "input": _display_input(tc),
        "expected": tc["expected"],
        "actual": None,
        "passed": False,
        "error_type": "timeout",
        "stderr": "前面的測資已經執行超時，這筆沒有執行。",
        "is_stress": tc["is_stress"],
        "skipped": True,
    }
