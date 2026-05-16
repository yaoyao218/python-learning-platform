"""test_problem_quality.py — 測資集品質守門員。

對 problem.py 的 TEST_CASES 套用論文的兩個指標：
  * TPR（True Positive Rate）= S+ 通過率平均，必須 = 1.0（測資不該誤殺正確寫法）
  * TNR（True Negative Rate）= S- 擋下率平均，必須 >= 0.85（測資要抓得到 bug）

把這個測試加進 pytest 後，未來任何人改 problem.py 都會被擋退化：
  * 加新測資但稀釋了鑑別度 → TNR 下降 → 測試 fail
  * 加了壞測資誤殺正解 → TPR 下降 → 測試 fail
  * 對應論文 Pareto 前緣的「右上角」概念，在 CI 裡守門。

執行：
    cd backend
    pytest tests/test_problem_quality.py -v

若要跑舊版 baseline（應該 fail），把 PROBLEM_MODULE 環境變數設成 problem_old：
    PROBLEM_MODULE=problem_old pytest tests/test_problem_quality.py
"""
from __future__ import annotations
import asyncio
import importlib
import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from executor import run_code               # noqa: E402
from testgen.run_eval import evaluate_pool, summarise   # noqa: E402
from testgen import run_eval as run_eval_mod            # noqa: E402

PROBLEM_MODULE = os.environ.get("PROBLEM_MODULE", "problem")
MIN_TPR = 1.0
MIN_TNR = 0.85


@pytest.fixture(scope="module")
def quality_report():
    """跑一次 S+/S- × TEST_CASES，回傳 summarise 出來的 metrics + 細節。"""
    # 把 TEST_CASES 注入 run_eval 模組（它的 evaluate_pool 從 module-global 讀）
    mod = importlib.import_module(PROBLEM_MODULE)
    run_eval_mod.TEST_CASES = mod.TEST_CASES

    testgen_dir = BACKEND / "testgen"

    async def run():
        s_plus = await evaluate_pool(testgen_dir / "solutions_correct")
        s_minus = await evaluate_pool(testgen_dir / "solutions_wrong")
        return summarise(s_plus, s_minus), s_plus, s_minus

    report, s_plus, s_minus = asyncio.run(run())
    report["_s_plus"] = s_plus
    report["_s_minus"] = s_minus
    report["_test_count"] = len(mod.TEST_CASES)
    return report


def test_tpr_equals_one(quality_report):
    """TPR 必須 = 1.0：任何正確解法都應該全過。"""
    tpr = quality_report["metrics"]["TPR"]
    failing = [
        sol for sol, rate in quality_report["S_plus_pass_rates"].items()
        if rate < 1.0
    ]
    assert tpr >= MIN_TPR, (
        f"TPR={tpr:.4f} < {MIN_TPR}（有正確解被測資誤殺）。"
        f"\n失敗的 S+ 解法：{failing}"
        f"\n→ 修法：找出哪筆測資讓正確解輸出對不上預期，"
        f"通常是 expected 寫錯或測資本身格式不合理。"
    )


def test_tnr_above_threshold(quality_report):
    """TNR 必須 >= 0.85：論文方法收斂後應該達到的水準。"""
    tnr = quality_report["metrics"]["TNR"]
    weak = [
        (sol, rate) for sol, rate in quality_report["S_minus_pass_rates"].items()
        if rate >= 0.5
    ]
    assert tnr >= MIN_TNR, (
        f"TNR={tnr:.4f} < {MIN_TNR}（測資鑑別度不足）。"
        f"\n通過率 >= 50% 的 bug solution：{weak}"
        f"\n→ 修法：到 testgen/ 跑迭代產出新測資集，"
        f"用 export_to_problem_py.py 替換 problem.py。"
    )


def test_every_bug_caught_at_least_once(quality_report):
    """沒有任何 S- 解可以通過全部測資（漏網 bug）。"""
    fp = quality_report["false_positives"]
    assert fp == [], (
        f"以下錯誤解通過了所有測資（false positive）：{fp}"
        f"\n→ 修法：為這幾個 bug 加專屬的 killer mode 進 testgen/gen.py，"
        f"再產一輪測資。"
    )


def test_minimum_test_case_count(quality_report):
    """確保測資數量不少於合理下限。"""
    count = quality_report["_test_count"]
    assert count >= 10, f"TEST_CASES 只有 {count} 筆，少於 10 筆下限"
