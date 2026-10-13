#!/usr/bin/env python3
"""pipeline.py — 全自動測資迭代：一個指令從目前進度跑到結束。

每一輪：
  1. propose.py   請 AI 提出候選測資（這一輪已有候選檔就沿用，不重抽）
  2. auto_review  依評測數字自動審核，寫出 rN_review.json、rN_tests.json
停止條件（每輪開始前檢查，依序）：
  * converged：TPR = 1、訓練池每個 S- 至少被抓一次、TNR 達成率 ≥ --target
  * stalled：上一輪沒有保留任何新測資（再跑也只是同樣的貪婪規則）
  * max_rounds：已到 --max-rounds
結束後：
  * 驗收池只跑一次，存成 rounds/heldout_final.json；檔案已存在就只讀出來，不重跑
  * 每輪數據彙整成 rounds/pipeline_summary.json，並印出可貼進報告的表格

前置：第 0 輪要先用 rounds.py init 建立。

執行：
    cd backend
    python -m testgen.pipeline --problem longest-substring --plan    # 只看目前狀態與會做什麼，不呼叫 API、不寫檔
    python -m testgen.pipeline --problem longest-substring
"""
from __future__ import annotations
import argparse
import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from problem import PROBLEMS                         # noqa: E402
from testgen import registry, rounds, run_eval      # noqa: E402
from testgen.auto_review import review_round        # noqa: E402
from testgen.propose import DEFAULT_MODEL           # noqa: E402


def last_round(pid: str) -> int:
    n = -1
    while rounds.round_path(pid, n + 1, "tests").exists():
        n += 1
    if n < 0:
        raise SystemExit(f"{pid} 還沒有第 0 輪；先執行 python -m testgen.rounds init --problem {pid}")
    return n


def load(pid: str, n: int, kind: str) -> dict | None:
    path = rounds.round_path(pid, n, kind)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def is_converged(ev: dict, target: float) -> bool:
    return ev["TPR"] >= 0.9999 and not ev["uncaught"] and ev["achievement"] >= target


def stop_reason(pid: str, n_last: int, max_rounds: int, target: float) -> str | None:
    ev = load(pid, n_last, "tests")["evaluation"]
    if is_converged(ev, target):
        return "converged"
    if n_last >= 1:
        review = load(pid, n_last, "review")
        if review is not None and not any(i["decision"] == "keep" for i in review["items"]):
            return "stalled"
    if n_last >= max_rounds:
        return "max_rounds"
    return None


def propose(pid: str, n: int, args) -> None:
    cmd = [sys.executable, "-m", "testgen.propose", "--problem", pid, "--round", str(n),
           "--n", str(args.n), "--model", args.model, "--temperature", str(args.temperature),
           "--prompt-version", args.prompt_version, "--max-tokens", str(args.max_tokens)]
    if args.reasoning_effort != "none":
        cmd += ["--reasoning-effort", args.reasoning_effort]
    print(f"\n[pipeline] 第 {n} 輪：AI 提案（{args.model}）")
    r = subprocess.run(cmd, cwd=BACKEND, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise SystemExit(f"第 {n} 輪提案失敗（exit {r.returncode}）；修正後重跑 pipeline 會從這一輪接續")


async def heldout_final(pid: str, n_last: int) -> dict:
    """驗收池只跑一次：已有紀錄就直接讀，不重跑。"""
    path = rounds.rounds_dir(pid) / "heldout_final.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        print(f"\n[pipeline] 驗收池已跑過（{data['created_at']}，對應第 {data['round']} 輪），只讀出結果，不重跑")
        return data
    cases = load(pid, n_last, "tests")["cases"]
    cases = [dict(c, args=tuple(c["args"])) if "args" in c else c for c in cases]
    method = PROBLEMS[pid]["method"]
    run_eval.TEST_CASES = cases
    s_plus = await run_eval.evaluate_pool(registry.pool_dir(pid, "correct"), method)
    s_held = await run_eval.evaluate_pool(registry.pool_dir(pid, "heldout"), method)
    summary = run_eval.summarise(s_plus, s_held)
    data = {
        "problem": pid, "round": n_last, "n_cases": len(cases),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "note": "驗收池（solutions_heldout）只在最後一輪結束後跑一次；不得依結果回頭修改測資",
        "TPR": summary["metrics"]["TPR"], "heldout_TNR": summary["metrics"]["TNR"],
        "heldout_pass_rates": {Path(k).stem: v for k, v in summary["S_minus_pass_rates"].items()},
        "heldout_uncaught": [Path(k).stem for k in summary["false_positives"]],
    }
    rounds.write_json(path, data)
    print(f"\n[pipeline] 驗收池（第 {n_last} 輪測資）：TNR {data['heldout_TNR']}，"
          f"漏網 {data['heldout_uncaught'] or '無'}；已存成 {path.relative_to(BACKEND)}")
    return data


def round_rows(pid: str, n_last: int) -> list[dict]:
    rows = []
    for n in range(0, n_last + 1):
        tests = load(pid, n, "tests")
        ev = tests["evaluation"]
        row = {"round": n, "n_cases": len(tests["cases"]), "TPR": ev["TPR"], "TNR": ev["TNR"],
               "achievement": ev["achievement"], "uncaught": ev["uncaught"]}
        cand, review = load(pid, n, "candidates"), load(pid, n, "review")
        if cand:
            st, meta = cand.get("stats", {}), cand.get("meta", {})
            row.update({"proposed": st.get("n_returned"), "invalid_or_dup": st.get("n_rejected"),
                        "model": meta.get("model"), "prompt_version": meta.get("prompt_version", "v1"),
                        "reasoning_effort": meta.get("reasoning_effort"),
                        "api_sec": meta.get("elapsed_sec"), "tokens": (meta.get("usage") or {}).get("total_tokens")})
        if review:
            items = review["items"]
            row.update({"kept": sum(i["decision"] == "keep" for i in items),
                        "target_hit_rate": round(sum(bool(i.get("target_hit")) for i in items) / len(items), 4) if items else None})
        rows.append(row)
    return rows


def print_table(pid: str, rows: list[dict], reason: str, held: dict | None) -> None:
    print(f"\n=== {pid}：{PROBLEMS[pid]['title']} ===")
    print("| 輪 | 測資數 | 提案 | 不合法/重複 | 保留 | target_hit | TNR | 達成率 | 訓練池漏網 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        dash = lambda k: "—" if r.get(k) is None else r[k]
        print(f"| r{r['round']} | {r['n_cases']} | {dash('proposed')} | {dash('invalid_or_dup')} | {dash('kept')} | "
              f"{dash('target_hit_rate')} | {r['TNR']:.4f} | {r['achievement']:.4f} | {', '.join(r['uncaught']) or '無'} |")
    label = {"converged": "收斂", "stalled": "停滯（上一輪沒有保留新測資）", "max_rounds": "達到輪數上限"}[reason]
    print(f"停止原因：{label}")
    if held:
        print(f"驗收池：TNR {held['heldout_TNR']}，漏網 {', '.join(held['heldout_uncaught']) or '無'}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--problem", required=True, choices=list(registry.TESTGEN_PROBLEMS))
    p.add_argument("--max-rounds", type=int, default=4, help="最多跑到第幾輪（預設 4，對照 LC3 人工迭代的 4 輪）")
    p.add_argument("--target", type=float, default=0.85, help="TNR 達成率門檻（預設 0.85）")
    p.add_argument("--n", type=int, default=12, help="每輪要求 AI 提出幾筆候選")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--prompt-version", default="v2")
    p.add_argument("--reasoning-effort", default="low", choices=["low", "medium", "high", "none"],
                   help="預設 low：與 LC121 全部輪次、LC32 第 3–5 輪相同；none = 用模型預設")
    p.add_argument("--max-tokens", type=int, default=4000,
                   help="每次回覆的 token 上限；Groq 免費方案每分鐘 8000（含 prompt），預設 4000")
    p.add_argument("--plan", action="store_true", help="只顯示目前狀態與接下來會做什麼，不呼叫 API、不寫檔")
    args = p.parse_args()
    pid = args.problem

    n_last = last_round(pid)
    reason = stop_reason(pid, n_last, args.max_rounds, args.target)
    if args.plan:
        print(f"[pipeline] {pid}：已完成到第 {n_last} 輪")
        if reason:
            print(f"  不會再提案（{reason}）；接下來只做驗收池與彙整")
        else:
            print(f"  接下來從第 {n_last + 1} 輪開始，最多到第 {args.max_rounds} 輪，每輪呼叫一次 {args.model}")
        held_path = rounds.rounds_dir(pid) / "heldout_final.json"
        print(f"  驗收池：{'已有紀錄，只會讀出' if held_path.exists() else '還沒跑，結束時會跑一次並存檔'}")
        print_table(pid, round_rows(pid, n_last), reason or "max_rounds", None)
        return

    while reason is None:
        n = n_last + 1
        if not rounds.round_path(pid, n, "candidates").exists():
            propose(pid, n, args)
        else:
            print(f"\n[pipeline] 第 {n} 輪已有候選檔，沿用（不重抽）")
        print(f"[pipeline] 第 {n} 輪：自動審核")
        asyncio.run(review_round(pid, n, verbose=False))
        n_last = n
        ev = load(pid, n, "tests")["evaluation"]
        print(f"[pipeline] 第 {n} 輪結束：TNR {ev['TNR']}，達成率 {ev['achievement']}，訓練池漏網 {ev['uncaught'] or '無'}")
        reason = stop_reason(pid, n_last, args.max_rounds, args.target)

    held = asyncio.run(heldout_final(pid, n_last))
    rows = round_rows(pid, n_last)
    rounds.write_json(rounds.rounds_dir(pid) / "pipeline_summary.json", {
        "problem": pid, "created_at": datetime.now().isoformat(timespec="seconds"),
        "settings": {"max_rounds": args.max_rounds, "target": args.target, "n": args.n, "model": args.model,
                     "temperature": args.temperature, "prompt_version": args.prompt_version,
                     "reasoning_effort": args.reasoning_effort, "max_tokens": args.max_tokens},
        "final_round": n_last, "stop_reason": reason,
        "converged": is_converged(load(pid, n_last, "tests")["evaluation"], args.target),
        "rounds": rows, "heldout": held,
    })
    print_table(pid, rows, reason, held)


if __name__ == "__main__":
    main()
