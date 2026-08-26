#!/usr/bin/env python3
"""run_eval.py — 評估 TEST_CASES 對 S+ / S- 兩個池子的鑑別能力。

設計重點：
  * 重用平台既有的 `executor.run_code`，數字真的反映平台跑學生程式碼的方式。
  * 不改動任何既有檔案，純離線分析。
  * 支援 --tests <module> 切換不同版本的測資（baseline vs v1 vs v2 ...）

輸出：
  * stdout：摘要表（TPR、TNR、每筆測資的鑑別度、每個 S- 的存活率）
  * feedback_<label>.json：完整反饋報告，給後續迭代用

執行：
    cd backend
    python -m testgen.run_eval                                    # baseline（problem.TEST_CASES）
    python -m testgen.run_eval --tests testgen.tests_v1 --label v1
"""
from __future__ import annotations
import argparse
import asyncio
import importlib
import json
import sys
from pathlib import Path

# 把 backend/ 加到路徑，這樣可以 import executor 和 problem
HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from executor import run_code          # noqa: E402
from judge import compare, get_args    # noqa: E402

# TEST_CASES 變成 lazy，由 main() 依 --tests 選項決定載入哪個模組
TEST_CASES: list[dict] = []
METHOD = "lengthOfLongestSubstring"


async def run_solution_on_case(solution_code: str, tc: dict, method: str = None) -> dict:
    """跑一個解法在一筆測資上，回傳 pass/fail + 詳細資訊。"""
    timeout = 10.0 if tc["is_stress"] else 5.0
    args = get_args(tc)
    result = await run_code(solution_code, method or METHOD, args, timeout=timeout)
    actual = result["actual"]
    passed = compare(actual, tc["expected"]) and result["error_type"] is None
    return {
        "index": tc["index"],
        "passed": passed,
        "actual": actual,
        "error_type": result["error_type"],
        "stderr": result["stderr"][:200] if result["stderr"] else "",
    }


async def evaluate_pool(pool_dir: Path, method: str = None) -> dict[str, list[dict]]:
    """跑池子裡的每個 .py 解法在所有 TEST_CASES 上。"""
    out = {}
    for sol_file in sorted(pool_dir.glob("*.py")):
        code = sol_file.read_text(encoding="utf-8")
        # 同個解法的 18 筆 case 可以並行
        per_case = await asyncio.gather(
            *(run_solution_on_case(code, tc, method) for tc in TEST_CASES)
        )
        out[sol_file.name] = list(per_case)
    return out


def summarise(s_plus: dict, s_minus: dict) -> dict:
    """從原始 pass/fail 矩陣推導 TPR、TNR、command_value、survivors。"""
    n_cases = len(TEST_CASES)

    def pass_rate(per_case_list):
        if not per_case_list: return 0.0
        return sum(1 for r in per_case_list if r["passed"]) / len(per_case_list)

    pos_rates = {name: pass_rate(rs) for name, rs in s_plus.items()}
    neg_rates = {name: pass_rate(rs) for name, rs in s_minus.items()}

    # 論文定義：
    #   TPR = 平均（在 S+ 上的通過率）   ← 越高越好（理想=1.0）
    #   TNR = 平均（在 S- 上的擋下率）   ← 越高越好
    tpr = sum(pos_rates.values()) / max(len(pos_rates), 1)
    tnr = sum(1 - r for r in neg_rates.values()) / max(len(neg_rates), 1)

    # 每筆測資的鑑別度：有多少個 S- 在這筆 case 上被打掉
    cmd_value = {}
    for tc in TEST_CASES:
        idx = tc["index"]
        caught = 0
        for _, per_case in s_minus.items():
            r = next((x for x in per_case if x["index"] == idx), None)
            if r and not r["passed"]:
                caught += 1
        cmd_value[idx] = caught

    # 假陽性（漏網 S-）：通過率 == 1.0 的錯誤解
    false_positives = [name for name, r in neg_rates.items() if r >= 0.999]

    # 假陰性（被誤殺的 S+）：通過率 < 1.0 的正確解
    false_negatives = [
        {"sol": name, "fail_indices": [r["index"] for r in s_plus[name] if not r["passed"]]}
        for name, rate in pos_rates.items() if rate < 0.999
    ]

    return {
        "metrics": {"TPR": round(tpr, 4), "TNR": round(tnr, 4),
                    "n_test_cases": n_cases,
                    "n_S_plus": len(s_plus),
                    "n_S_minus": len(s_minus)},
        "S_plus_pass_rates":  {k: round(v, 4) for k, v in pos_rates.items()},
        "S_minus_pass_rates": {k: round(v, 4) for k, v in neg_rates.items()},
        "command_value": cmd_value,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def print_report(report: dict, s_plus: dict, s_minus: dict):
    m = report["metrics"]
    n_minus = m["n_S_minus"]
    print(f"\n=== baseline 評估摘要 ===")
    print(f"TPR  = {m['TPR']:.4f}  (理想 1.0 — 正確解不該被誤殺)")
    print(f"TNR  = {m['TNR']:.4f}  (越高越好 — 錯誤解該被打掉)")
    print(f"     測資數 = {m['n_test_cases']}   S+ = {m['n_S_plus']}   S- = {m['n_S_minus']}")

    print(f"\n=== S+ 正確解通過率 ===")
    for name, rate in report["S_plus_pass_rates"].items():
        flag = "✓" if rate >= 0.999 else "⚠"
        print(f"  {flag}  {name:<24s} {rate*100:6.2f}%")

    print(f"\n=== S- 錯誤解通過率（越低越好）===")
    for name, rate in report["S_minus_pass_rates"].items():
        flag = "✓" if rate < 0.001 else "⚠" if rate < 0.999 else "✗"
        print(f"  {flag}  {name:<24s} {rate*100:6.2f}%")

    print(f"\n=== 每筆測資鑑別度（在 {n_minus} 個錯誤解上各打掉幾個）===")
    for idx, caught in sorted(report["command_value"].items()):
        tc = next(t for t in TEST_CASES if t["index"] == idx)
        bar = "█" * caught + "·" * (n_minus - caught)
        input_preview = repr(tc.get("input", tc.get("args")))[:30]
        print(f"  #{idx:>2}  {bar}  {caught}/{n_minus}  {input_preview}")

    if report["false_positives"]:
        print(f"\n⚠ 漏網的 S-（沒有任何測資打掉它們）：{report['false_positives']}")
    else:
        print(f"\n✓ 沒有漏網的 S-")

    if report["false_negatives"]:
        print(f"\n⚠ 被誤殺的 S+：")
        for fn in report["false_negatives"]:
            print(f"    {fn['sol']} 在測資 {fn['fail_indices']} 失敗")


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tests", default="problem",
                   help="Python 模組路徑（含 TEST_CASES）。default: problem (= 原本的 problem.py)")
    p.add_argument("--label", default="baseline",
                   help="輸出 feedback_<label>.json 的標籤")
    args = p.parse_args()

    # 動態載入指定模組的 TEST_CASES / METHOD
    global TEST_CASES, METHOD
    mod = importlib.import_module(args.tests)
    TEST_CASES = mod.TEST_CASES
    METHOD = getattr(mod, "METHOD", "lengthOfLongestSubstring")
    print(f"[testgen] 載入 {args.tests}.TEST_CASES（{len(TEST_CASES)} 筆，method={METHOD}）、S+、S- ...")

    s_plus = await evaluate_pool(HERE / "solutions_correct", METHOD)
    s_minus = await evaluate_pool(HERE / "solutions_wrong", METHOD)
    report = summarise(s_plus, s_minus)
    report["tests_module"] = args.tests
    report["raw_S_plus"] = s_plus
    report["raw_S_minus"] = s_minus

    out_path = HERE / f"feedback_{args.label}.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print_report(report, s_plus, s_minus)
    print(f"\n完整反饋已寫入 {out_path.name}")


if __name__ == "__main__":
    asyncio.run(main())
