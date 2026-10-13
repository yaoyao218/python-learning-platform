# -*- coding: utf-8 -*-
"""第 N 輪候選測資的 AI 代審（測試階段，非人工）。規則：只看 TPR/TNR 數字，不看 AI 附的理由；
上一輪正式測資全部保留，候選以貪婪法依「抓錯密度」加入。對應設計文件 B 的第 ⑧ 步。

前置：已用 `python -m testgen.propose --problem X --round N` 產生 rounds/rN_candidates.json。
執行（在 backend 資料夾）：
    python ../docs/superpowers/specs/teammate-tests/ai_review_round.py --problem best-time-stock --round 1 --dry-run
    python ../docs/superpowers/specs/teammate-tests/ai_review_round.py --problem best-time-stock --round 1

--dry-run：只印出結果，不寫任何檔案。沒有 --dry-run 時會寫入 rounds/rN_review.json 與 rounds/rN_tests.json，
並標註 test_phase（AI 代審、非人工）。只使用「訓練池」的 S-；驗收池（solutions_heldout）完全不碰。
"""
import argparse
import ast
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[4] / "backend"
sys.path.insert(0, str(BACKEND))
from executor import run_code          # noqa: E402
from problem import PROBLEMS           # noqa: E402
from testgen import registry, rounds   # noqa: E402

NOTE = "測試階段：審核由 AI 代審（非人工），規則為只看 TPR/TNR 數字；不計入正式實驗結果。"


def tnr_of(ids, caught, bugs):
    return sum(sum(b in caught[c] for c in ids) / len(ids) for b in bugs) / len(bugs) if ids else 0.0


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", required=True, choices=list(registry.TESTGEN_PROBLEMS))
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    pid, n = a.problem, a.round
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

    for it in items:
        print(f"{it['id']:6s} {it['decision']:4s} {it['reason']}")
    print(f"\nr{n-1}: n={len(prev)} TNR={tnr_of(base, caught, bugs):.4f}  ->  r{n}: n={len(kept)} TPR={evf['TPR']} TNR={evf['TNR']} achievement={evf['achievement']}")
    print("pass rates:", evf["S_minus_pass_rates"])
    print("uncaught:", evf["uncaught"], "| S+ fail:", evf["S_plus_failures"])

    if a.dry_run:
        print("\n（--dry-run：沒有寫入任何檔案）")
        return
    meta = {"test_phase": True, "note": NOTE, "reviewer": "AI（測試階段代審，非人工）",
            "rule": "只看 TPR/TNR 數字，不看 AI 理由；上一輪正式測資全保留，候選以貪婪法依 TNR 加入",
            "created_at": datetime.now().isoformat(timespec="seconds")}
    rounds.write_json(rounds.round_path(pid, n, "review"), {"problem": pid, "round": n, **meta, "trace": trace, "items": items})
    rounds.write_json(rounds.round_path(pid, n, "tests"), {"problem": pid, "round": n, **meta,
                      "source": f"AI 代審（測試階段）：r{n-1} + 保留的 r{n} 候選", "evaluation": evf,
                      "cases": [rounds._to_json_case(c) for c in kept]})
    print(f"\n已寫入 rounds/r{n}_review.json 與 rounds/r{n}_tests.json")


asyncio.run(main())
