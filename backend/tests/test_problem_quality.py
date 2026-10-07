"""test_problem_quality.py — 測資集品質守門員。

對 testgen/registry.py 登記的每一題，套用論文的兩個指標：
  * TPR（True Positive Rate）= S+ 通過率平均，必須 = 1.0（測資不該誤殺正確寫法）
  * TNR 達成率 = TNR ÷ 該題 TNR 上限，必須 >= 0.85（測資要抓得到 bug）
    TNR 上限因題目而異（例如布林輸出的題目到不了 1.0），所以不直接用固定的 TNR 門檻；
    LC3 的上限是 1.0，達成率等於 TNR，與舊版標準相同。

把這個測試加進 pytest 後，未來任何人改 problem.py 都會被擋退化：
  * 加新測資但稀釋了鑑別度 → TNR 下降 → 測試 fail
  * 加了壞測資誤殺正解 → TPR 下降 → 測試 fail
  * 對應論文 Pareto 前緣的「右上角」概念，在 CI 裡守門。

執行：
    cd backend
    pytest tests/test_problem_quality.py -v

若要跑舊版 baseline（應該 fail），把 PROBLEM_MODULE 環境變數設成 problem_old：
    PROBLEM_MODULE=problem_old pytest tests/test_problem_quality.py
（problem_old / problem_v4 只有 LC3 的 TEST_CASES，其他題目會 skip）
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

from testgen.run_eval import evaluate_pool, summarise   # noqa: E402
from testgen import run_eval as run_eval_mod            # noqa: E402
from testgen import registry                            # noqa: E402
from problem import PROBLEMS                            # noqa: E402

PROBLEM_MODULE = os.environ.get("PROBLEM_MODULE", "problem")
MIN_TPR = 1.0
MIN_TNR_ACHIEVEMENT = 0.85


def _load_test_cases(problem_id: str) -> list[dict]:
    mod = importlib.import_module(PROBLEM_MODULE)
    if hasattr(mod, "PROBLEMS") and problem_id in mod.PROBLEMS:
        return mod.PROBLEMS[problem_id]["test_cases"]
    if problem_id == "longest-substring":
        return mod.TEST_CASES          # problem_old / problem_v4 只有 LC3 的 TEST_CASES
    pytest.skip(f"{PROBLEM_MODULE} 沒有 {problem_id} 的測資")


@pytest.fixture(scope="module", params=list(registry.TESTGEN_PROBLEMS))
def quality_report(request):
    """對一題跑一次 S+/S- × 測資，回傳 summarise 出來的 metrics + 細節。"""
    problem_id = request.param
    if not registry.converged(problem_id):
        pytest.skip(f"{problem_id} 的測資尚未收斂（registry converged=False），不套用守門員")
    test_cases = _load_test_cases(problem_id)
    # 把測資注入 run_eval 模組（它的 evaluate_pool 從 module-global 讀）
    run_eval_mod.TEST_CASES = test_cases
    method = PROBLEMS[problem_id]["method"]

    async def run():
        s_plus = await evaluate_pool(registry.pool_dir(problem_id, "correct"), method)
        s_minus = await evaluate_pool(registry.pool_dir(problem_id, "wrong"), method)
        return summarise(s_plus, s_minus), s_plus, s_minus

    report, s_plus, s_minus = asyncio.run(run())
    report["_problem"] = problem_id
    report["_ceiling"] = registry.ceiling(problem_id)
    report["_s_plus"] = s_plus
    report["_s_minus"] = s_minus
    report["_test_count"] = len(test_cases)
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
    """TNR 達成率（TNR ÷ 該題上限）必須 >= 0.85：論文方法收斂後應該達到的水準。"""
    tnr = quality_report["metrics"]["TNR"]
    ceiling = quality_report["_ceiling"]
    achievement = tnr / ceiling
    weak = [
        (sol, rate) for sol, rate in quality_report["S_minus_pass_rates"].items()
        if rate >= 0.5
    ]
    assert achievement >= MIN_TNR_ACHIEVEMENT, (
        f"[{quality_report['_problem']}] TNR 達成率={achievement:.4f}"
        f"（TNR={tnr:.4f} ÷ 上限 {ceiling}）< {MIN_TNR_ACHIEVEMENT}（測資鑑別度不足）。"
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
