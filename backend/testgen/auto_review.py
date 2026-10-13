#!/usr/bin/env python3
"""auto_review.py — 第 N 輪候選測資的自動審核（取代人工審核）。

規則（與 2026-10-13 起 LC121、LC32 各輪使用的規則相同，結果可重現）：
  * 只看評測數字，不看 AI 附的理由；只用 S- 訓練池，驗收池完全不碰
  * 上一輪正式測資全部保留
  * 候選以貪婪法加入：每次挑「加入後 TNR 最高」的一筆（同分取抓到較多種錯誤的），
    TNR 沒有提高就停止
  * expected 一律由參考解 S* 經平台 executor 計算

由舊的 docs/superpowers/specs/teammate-tests/ai_review_round.py 升級為正式元件；
該腳本現在只是呼叫這裡的薄包裝。

執行：
    cd backend
    python -m testgen.auto_review --problem best-time-stock --round 1 --dry-run   # 只印結果
    python -m testgen.auto_review --problem best-time-stock --round 1             # 寫入 rN_review / rN_tests
"""
from __future__ import annotations
import argparse
import ast
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from executor import run_code          # noqa: E402
from problem import PROBLEMS           # noqa: E402
from testgen import registry, rounds   # noqa: E402

REVIEWER = "AI（自動審核，非人工）"
RULE = "只看 TPR/TNR 數字，不看 AI 理由；上一輪正式測資全保留，候選以貪婪法依 TNR 加入"


def tnr_of(ids, caught, bugs):
    return sum(sum(b in caught[c] for c in ids) / len(ids) for b in bugs) / len(bugs) if ids else 0.0


async def review_round(pid: str, n: int, dry_run: bool = False, verbose: bool = True) -> dict:
    """審核第 n 輪候選；回傳 {kept, dropped, evaluation, trace}。dry_run 時不寫檔。"""
    method = PROBLEMS[pid]["method"]
    prev_data = rounds.load_round_tests(pid, n - 1)
    prev = prev_data["cases"]
    bugs = sorted(prev_data["evaluation"]["S_minus_pass_rates"])         # 訓練池 S- 的名稱
    ref = registry.reference_path(pid).read_text(encoding="utf-8")
    cand_path = rounds.round_path(pid, n, "candidates")
    if not cand_path.exists():
        raise SystemExit(f"找不到 {cand_path}；請先執行 python -m testgen.propose --problem {pid} --round {n}")
    cands = json.loads(cand_path.read_text(encoding="utf-8"))["candidates"]

    cc = []
    for c in cands:
        r = await run_code(ref, method, tuple(c["args"]) if "args" in c else (c["input"],))
        if r.get("error_type"):
            raise SystemExit(f"參考解在候選 {c.get('id')} 上出錯：{r}")
        cc.append({"args": tuple(c["args"]) if "args" in c else None, "input": c.get("input"),
                   "expected": ast.literal_eval(r["actual"]), "is_stress": False})

    # 與前一輪相同的格式：單參數題用 input，多參數題用 args
    def fix(case):
        return {k: v for k, v in case.items() if not (k in ("args", "input") and v is None)}
    cc = [fix(x) for x in cc]

    ids = [f"b{i}" for i in range(1, len(prev) + 1)] + [c["id"] for c in cands]
    allc = [dict(tc, index=k) for k, tc in enumerate(list(prev) + cc, 1)]
    ev = await rounds.evaluate(pid, allc)
    caught = {i: set() for i in ids}
    for bug, idxs in ev["S_minus_caught_by"].items():
        for k in idxs:
            caught[ids[k - 1]].add(bug)

    base = ids[:len(prev)]
    sel, rem = list(base), [c["id"] for c in cands]
    cur = tnr_of(sel, caught, bugs)
    trace = [("start", None, round(cur, 4))]
    while rem:
        best = max(rem, key=lambda c: (tnr_of(sel + [c], caught, bugs), len(caught[c])))
        new = tnr_of(sel + [best], caught, bugs)
        if new <= cur + 1e-9:
            break
        sel.append(best); rem.remove(best); trace.append(("add", best, round(new, 4))); cur = new
    final = tnr_of(sel, caught, bugs)

    items = []
    for c, x in zip(cands, cc):
        keep = c["id"] in sel
        k = sorted(caught[c["id"]])
        if keep:
            reason = f"抓到 {len(k)}/{len(bugs)}（{', '.join(k)}）；移除它 TNR {tnr_of([s for s in sel if s != c['id']], caught, bugs):.4f}→{final:.4f}，保留可提高密度"
        else:
            reason = f"抓到 {len(k)}/{len(bugs)}（{', '.join(k)}）；加入保留集 TNR {final:.4f}→{tnr_of(sel + [c['id']], caught, bugs):.4f}（下降）"
        items.append({"id": c["id"], "args": list(c["args"]) if "args" in c else [c["input"]], "expected": x["expected"],
                      "target_bug": c.get("target_bug"), "kills": k, "target_hit": c.get("target_bug") in k,
                      "decision": "keep" if keep else "drop", "reason": reason})
    kept = [dict(tc, index=k) for k, tc in enumerate(list(prev) + [x for c, x in zip(cands, cc) if c["id"] in sel], 1)]
    evf = await rounds.evaluate(pid, kept)

    if verbose:
        for it in items:
            print(f"{it['id']:6s} {it['decision']:4s} {it['reason']}")
        print(f"\nr{n-1}: n={len(prev)} TNR={tnr_of(base, caught, bugs):.4f}  ->  r{n}: n={len(kept)} "
              f"TPR={evf['TPR']} TNR={evf['TNR']} achievement={evf['achievement']}")
        print("pass rates:", evf["S_minus_pass_rates"])
        print("uncaught:", evf["uncaught"], "| S+ fail:", evf["S_plus_failures"])

    result = {"n_prev": len(prev), "n_kept_new": len(kept) - len(prev), "n_candidates": len(cands),
              "evaluation": evf, "trace": trace,
              "target_hit_rate": round(sum(it["target_hit"] for it in items) / len(items), 4) if items else None}
    if dry_run:
        if verbose:
            print("\n（--dry-run：沒有寫入任何檔案）")
        return result
    meta = {"reviewer": REVIEWER, "rule": RULE, "created_at": datetime.now().isoformat(timespec="seconds")}
    rounds.write_json(rounds.round_path(pid, n, "review"), {"problem": pid, "round": n, **meta, "trace": trace, "items": items})
    rounds.write_json(rounds.round_path(pid, n, "tests"), {"problem": pid, "round": n, **meta,
                      "source": f"自動審核：r{n-1} + 保留的 r{n} 候選", "evaluation": evf,
                      "cases": [rounds._to_json_case(c) for c in kept]})
    if verbose:
        print(f"\n已寫入 rounds/r{n}_review.json 與 rounds/r{n}_tests.json")
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", required=True, choices=list(registry.TESTGEN_PROBLEMS))
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    asyncio.run(review_round(a.problem, a.round, a.dry_run))


if __name__ == "__main__":
    main()
