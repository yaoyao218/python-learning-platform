#!/usr/bin/env python3
"""rounds.py — AI 輔助迭代每一輪的正式測資與評測紀錄。

每題的紀錄放在 testgen/problems/<problem_id>/rounds/：

    r0_tests.json            第 0 輪（起點）測資 + 評測
    r{N}_candidates.json     第 N 輪 AI 提案（propose.py）
    r{N}_review.json         第 N 輪人工審核（review.py）
    r{N}_tests.json          第 N 輪結束後的正式測資 + 評測

評測一律經平台 executor（run_eval.evaluate_pool），數字與 run_eval.py 一致。
評測只用 S- 訓練池；驗收池只在最後一輪結束後用 `run_eval --heldout` 跑一次。

執行：
    cd backend
    python -m testgen.rounds init --problem longest-valid-parentheses
    python -m testgen.rounds init --problem longest-substring --from-module problem_old   # 實驗一
    python -m testgen.rounds show --problem longest-valid-parentheses --round 0
"""
from __future__ import annotations
import argparse
import asyncio
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from problem import PROBLEMS                           # noqa: E402
from testgen import registry                           # noqa: E402
from testgen import run_eval                           # noqa: E402


def rounds_dir(problem_id: str) -> Path:
    return registry.problem_dir(problem_id) / "rounds"


def round_path(problem_id: str, n: int, kind: str) -> Path:
    """kind: tests / candidates / review"""
    return rounds_dir(problem_id) / f"r{n}_{kind}.json"


def _to_json_case(tc: dict) -> dict:
    out = {k: v for k, v in tc.items() if not k.startswith("_")}
    if "args" in out:
        out["args"] = list(out["args"])
    return out


def _from_json_case(tc: dict) -> dict:
    tc = dict(tc)
    if "args" in tc:
        tc["args"] = tuple(tc["args"])
    return tc


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_round_tests(problem_id: str, n: int) -> dict:
    path = round_path(problem_id, n, "tests")
    if not path.exists():
        raise SystemExit(f"找不到 {path.relative_to(HERE.parent)}；第 0 輪請先跑 "
                         f"python -m testgen.rounds init --problem {problem_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["cases"] = [_from_json_case(c) for c in data["cases"]]
    return data


async def evaluate(problem_id: str, cases: list[dict]) -> dict:
    """對 S+ / S- 訓練池跑 cases，回傳精簡的評測結果（含每個 S- 抓到的測資 index）。"""
    method = PROBLEMS[problem_id]["method"]
    run_eval.TEST_CASES = cases
    s_plus = await run_eval.evaluate_pool(registry.pool_dir(problem_id, "correct"), method)
    s_minus = await run_eval.evaluate_pool(registry.pool_dir(problem_id, "wrong"), method)
    summary = run_eval.summarise(s_plus, s_minus)
    ceiling = registry.ceiling(problem_id)
    return {
        "TPR": summary["metrics"]["TPR"],
        "TNR": summary["metrics"]["TNR"],
        "ceiling": round(ceiling, 4),
        "achievement": round(summary["metrics"]["TNR"] / ceiling, 4),
        "S_minus_pass_rates": {Path(k).stem: v for k, v in summary["S_minus_pass_rates"].items()},
        "S_minus_caught_by": {Path(k).stem: [r["index"] for r in rs if not r["passed"]]
                              for k, rs in s_minus.items()},
        "uncaught": [Path(k).stem for k in summary["false_positives"]],
        "S_plus_failures": summary["false_negatives"],
    }


def save_round_tests(problem_id: str, n: int, cases: list[dict], source: str, evaluation: dict) -> Path:
    path = round_path(problem_id, n, "tests")
    write_json(path, {
        "problem": problem_id,
        "round": n,
        "source": source,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "evaluation": evaluation,
        "cases": [_to_json_case(c) for c in cases],
    })
    return path


def print_evaluation(ev: dict, n_cases: int) -> None:
    print(f"  測資 {n_cases} 筆  TPR={ev['TPR']:.4f}  TNR={ev['TNR']:.4f}  "
          f"上限={ev['ceiling']:.4f}  達成率={ev['achievement']:.4f}")
    for name, rate in ev["S_minus_pass_rates"].items():
        print(f"    {name:<24} 通過率 {rate * 100:6.2f}%  被抓到的測資 {ev['S_minus_caught_by'][name]}")
    if ev["uncaught"]:
        print(f"  ⚠ 完全沒被抓到：{ev['uncaught']}")
    if ev["S_plus_failures"]:
        print(f"  ⚠ S+ 被誤殺：{ev['S_plus_failures']}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("init", help="建立第 0 輪（起點）測資與評測")
    pi.add_argument("--problem", required=True)
    pi.add_argument("--from-module", default=None,
                    help="從指定模組的 TEST_CASES 取起點測資（例：problem_old）；不給則用 problem.PROBLEMS")
    pi.add_argument("--force", action="store_true", help="覆寫已存在的 r0_tests.json")
    ps = sub.add_parser("show", help="顯示某一輪的正式測資評測")
    ps.add_argument("--problem", required=True)
    ps.add_argument("--round", type=int, required=True)
    args = p.parse_args()

    if args.cmd == "init":
        path = round_path(args.problem, 0, "tests")
        if path.exists() and not args.force:
            raise SystemExit(f"{path.relative_to(HERE.parent)} 已存在；第 0 輪是實驗起點，確定要重建才加 --force")
        if args.from_module:
            cases = list(importlib.import_module(args.from_module).TEST_CASES)
            source = f"{args.from_module}.TEST_CASES"
        else:
            cases = list(PROBLEMS[args.problem]["test_cases"])
            source = f"problem.PROBLEMS[{args.problem!r}]['test_cases']"
        ev = asyncio.run(evaluate(args.problem, cases))
        out = save_round_tests(args.problem, 0, cases, source, ev)
        print(f"[rounds] 第 0 輪：{source}")
        print_evaluation(ev, len(cases))
        print(f"已寫入 {out.relative_to(HERE.parent)}")
    else:
        data = load_round_tests(args.problem, args.round)
        print(f"[rounds] {args.problem} 第 {args.round} 輪（來源：{data['source']}）")
        print_evaluation(data["evaluation"], len(data["cases"]))


if __name__ == "__main__":
    main()
