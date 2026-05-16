import asyncio

from executor import run_code
from problem import TEST_CASES

_DISPLAY_MAX_LEN = 50


async def _run_one(code: str, tc: dict) -> dict:
    timeout = 10.0 if tc["is_stress"] else 5.0
    exec_result = await run_code(code, tc["input"], timeout=timeout)

    actual = exec_result["actual"]
    passed = (actual == str(tc["expected"])) and exec_result["error_type"] is None

    display_input = (
        tc["input"]
        if len(tc["input"]) <= _DISPLAY_MAX_LEN
        else tc["input"][:_DISPLAY_MAX_LEN] + "..."
    )

    return {
        "index": tc["index"],
        "input": display_input,
        "expected": tc["expected"],
        "actual": actual,
        "passed": passed,
        "error_type": exec_result["error_type"],
        "stderr": exec_result["stderr"],
    }


async def judge(code: str) -> list[dict]:
    """
    對全部 18 組 test case 並行執行學生程式碼並比對結果。
    永遠跑完全部，不中途停止（停在第一個失敗是前端的責任）。

    Returns:
        list[dict]: 18 筆結果（順序與 TEST_CASES 一致），每筆包含
            index, input（截斷顯示）, expected, actual, passed, error_type, stderr
    """
    results = await asyncio.gather(*(_run_one(code, tc) for tc in TEST_CASES))
    return list(results)
