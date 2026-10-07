#!/usr/bin/env python3
"""assess_problem.py — 題目適用性判斷的第二、三關（實驗計畫第四節），輸出評分卡。

第二關 建池驗證
  2a S+ 一致性：所有 S+ 在隨機合法輸入上答案一致
  2b S- 非等價：每個 S- 至少在一組輸入上答錯
  2c S- 不重複：沒有兩個 S- 被抓到的輸入集合完全相同（另列包含關係）
  2d 有效 S- 數：扣掉等價與重複後 ≥ 4
  2e validator：現有測資都通過 spec.validate，且 expected 與 S* 一致
第三關 量化
  3a TNR 上限：窮舉小輸入 + 隨機輸入，找「單筆最多抓到幾個 S-」÷ S- 總數
  3b 起點：現有測資的 TNR 與達成率（TNR ÷ 上限）

驗收池只檢查有效性（非等價、不與訓練池重複），**不計算它對現有測資的表現**——
迭代期間看到驗收分數，驗收池就失去意義。

為了跑數萬組輸入，這裡在同一個程序內直接呼叫解法（不經 executor 的子程序），
所以只適用於已知會正常結束的 S+/S- 池。正式的 TPR/TNR 仍以 run_eval.py 為準。

執行：
    cd backend
    python -m testgen.assess_problem --problem longest-valid-parentheses
"""
from __future__ import annotations
import argparse
import itertools
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from problem import PROBLEMS          # noqa: E402
from judge import get_args            # noqa: E402
from testgen import registry          # noqa: E402

MIN_EFFECTIVE_S_MINUS = 4
_ERR = object()   # 解法丟出例外時的哨兵值，跟任何答案都不相等


def load_pool(pool_dir: Path, method: str) -> dict[str, dict]:
    """{檔名: {"call": 可呼叫的方法, "desc": 檔頭第一行註解}}"""
    pool = {}
    for path in sorted(pool_dir.glob("*.py")):
        code = path.read_text(encoding="utf-8")
        ns: dict = {}
        exec(code, ns)
        first = code.splitlines()[0] if code else ""
        pool[path.stem] = {
            "call": getattr(ns["Solution"](), method),
            "desc": first.lstrip("# ").strip() if first.startswith("#") else "",
        }
    return pool


def run(call, args: tuple):
    try:
        # 複製 list 參數，避免解法改到輸入影響下一個解法
        return call(*[list(a) if isinstance(a, list) else a for a in args])
    except Exception:
        return _ERR


def same(a, b) -> bool:
    if a is _ERR or b is _ERR:
        return False
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) < 1e-6
        except (TypeError, ValueError):
            return False
    return a == b


def kill_sets(pool: dict, inputs: list[tuple], expected: list) -> dict[str, frozenset]:
    """每個解法答錯的輸入索引集合。"""
    return {
        name: frozenset(i for i, args in enumerate(inputs) if not same(run(s["call"], args), expected[i]))
        for name, s in pool.items()
    }


def assess(problem_id: str, n_random: int, seed: int) -> dict:
    prob = PROBLEMS[problem_id]
    method = prob["method"]
    spec = registry.load_spec(problem_id)
    s_plus = load_pool(registry.pool_dir(problem_id, "correct"), method)
    s_minus = load_pool(registry.pool_dir(problem_id, "wrong"), method)
    heldout_dir = registry.pool_dir(problem_id, "heldout")
    held = load_pool(heldout_dir, method) if heldout_dir.exists() else {}
    ref_name = Path(registry.TESTGEN_PROBLEMS[problem_id]["reference"]).stem
    ref = s_plus[ref_name]["call"]

    rng = random.Random(seed)
    random_inputs = [spec.random_args(rng) for _ in range(n_random)]
    small_inputs = list(spec.small_args())
    bad_gen = [a for a in itertools.chain(random_inputs, small_inputs) if spec.validate(a)]
    if bad_gen:
        raise SystemExit(f"spec 產生了不合法的輸入（spec 本身有問題）：{bad_gen[0]!r} → {spec.validate(bad_gen[0])}")
    inputs = random_inputs + small_inputs
    expected = [run(ref, a) for a in inputs]

    # 2a S+ 一致性
    plus_kills = kill_sets(s_plus, inputs, expected)
    mismatch_idx = sorted(set().union(*plus_kills.values()))
    gate_2a = {
        "pass": not mismatch_idx,
        "n_inputs": len(inputs),
        "mismatches": len(mismatch_idx),
        "example": repr(inputs[mismatch_idx[0]]) if mismatch_idx else None,
    }

    # 2b–2d S- 訓練池
    minus_kills = kill_sets(s_minus, inputs, expected)
    equivalent = [n for n, k in minus_kills.items() if not k]
    duplicates = [[a, b] for a, b in itertools.combinations(minus_kills, 2)
                  if minus_kills[a] and minus_kills[a] == minus_kills[b]]
    subsumed = [[a, b] for a, b in itertools.permutations(minus_kills, 2)
                if minus_kills[a] and minus_kills[a] < minus_kills[b]]
    effective = len({k for k in minus_kills.values() if k})
    gate_2bcd = {
        "pass": not equivalent and not duplicates and effective >= MIN_EFFECTIVE_S_MINUS,
        "n_s_minus": len(s_minus),
        "effective": effective,
        "equivalent": equivalent,
        "duplicates": duplicates,
        "subsumed": subsumed,   # [a, b]：抓到 a 的輸入一定也抓到 b（不算失敗，只記錄）
    }

    # 驗收池：只檢查有效性
    held_kills = kill_sets(held, inputs, expected)
    gate_heldout = {
        "pass": all(held_kills.values()) and not any(
            held_kills[h] == minus_kills[m] for h in held for m in s_minus),
        "n_heldout": len(held),
        "equivalent": [h for h, k in held_kills.items() if not k],
        "same_as_training": [[h, m] for h in held for m in s_minus
                             if held_kills[h] and held_kills[h] == minus_kills[m]],
    }

    # 2e 現有測資：合法、expected 與 S* 一致
    cases = prob["test_cases"]
    case_args = [get_args(tc) for tc in cases]
    invalid = [{"index": tc["index"], "reason": spec.validate(a)}
               for tc, a in zip(cases, case_args) if spec.validate(a)]
    wrong_expected = [tc["index"] for tc, a in zip(cases, case_args)
                      if not same(run(ref, a), tc["expected"])]
    gate_2e = {"pass": not invalid and not wrong_expected,
               "invalid_cases": invalid, "expected_mismatch": wrong_expected}

    # 3a TNR 上限
    n_minus = len(s_minus)
    per_input = [sum(1 for k in minus_kills.values() if i in k) for i in range(len(inputs))]
    best_i = max(range(len(inputs)), key=per_input.__getitem__)
    ceiling = per_input[best_i] / n_minus
    gate_3a = {
        "ceiling": round(ceiling, 4),
        "max_caught": per_input[best_i],
        "example": repr(inputs[best_i]),
        "example_caught": sorted(n for n, k in minus_kills.items() if best_i in k),
        "searched": {"random": len(random_inputs), "exhaustive_small": len(small_inputs)},
    }

    # 3b 起點：現有測資在訓練池上的 TNR
    case_expected = [tc["expected"] for tc in cases]
    case_kills = kill_sets(s_minus, case_args, case_expected)
    tnr = sum(len(k) for k in case_kills.values()) / (len(cases) * n_minus)
    gate_3b = {
        "n_cases": len(cases),
        "tnr": round(tnr, 4),
        "achievement": round(tnr / ceiling, 4) if ceiling else None,
        "caught": sorted(n for n, k in case_kills.items() if k),
        "missed": sorted(n for n, k in case_kills.items() if not k),
    }

    passed = all(g["pass"] for g in (gate_2a, gate_2bcd, gate_heldout, gate_2e))
    return {
        "problem": problem_id,
        "seed": seed,
        "verdict": ("A" if ceiling >= 0.9999 else "B") if passed else "FAIL",
        "gate_2a_s_plus_consistency": gate_2a,
        "gate_2bcd_s_minus": gate_2bcd,
        "heldout_validity": gate_heldout,
        "gate_2e_test_cases": gate_2e,
        "gate_3a_ceiling": gate_3a,
        "gate_3b_round0": gate_3b,
        "s_minus_descriptions": {n: s["desc"] for n, s in s_minus.items()},
    }


def print_card(r: dict):
    ok = lambda b: "✓" if b else "✗"
    g2a, g2, gh, g2e = (r["gate_2a_s_plus_consistency"], r["gate_2bcd_s_minus"],
                        r["heldout_validity"], r["gate_2e_test_cases"])
    g3a, g3b = r["gate_3a_ceiling"], r["gate_3b_round0"]
    print(f"\n=== 評分卡：{r['problem']} ===")
    print(f"2a  S+ 一致性      {ok(g2a['pass'])}  {g2a['n_inputs']} 組輸入，不一致 {g2a['mismatches']} 次"
          + (f"（例：{g2a['example']}）" if g2a["example"] else ""))
    print(f"2b  S- 非等價      {ok(not g2['equivalent'])}  " + (f"等價（從未答錯）：{g2['equivalent']}" if g2["equivalent"] else "全部 S- 都會答錯"))
    print(f"2c  S- 不重複      {ok(not g2['duplicates'])}  " + (f"行為完全相同：{g2['duplicates']}" if g2["duplicates"] else "沒有重複"))
    print(f"2d  有效 S- 數     {ok(g2['effective'] >= MIN_EFFECTIVE_S_MINUS)}  {g2['effective']}/{g2['n_s_minus']}（下限 {MIN_EFFECTIVE_S_MINUS}）")
    print(f"    包含關係       {len(g2['subsumed'])} 組" + (f"：{g2['subsumed']}" if g2["subsumed"] else ""))
    print(f"2e  現有測資       {ok(g2e['pass'])}  "
          + ("全部合法且 expected 與 S* 一致" if g2e["pass"]
             else f"不合法 {g2e['invalid_cases']}；expected 與 S* 不符 {g2e['expected_mismatch']}"))
    print(f"    驗收池有效性   {ok(gh['pass'])}  {gh['n_heldout']} 個"
          + (f"；等價 {gh['equivalent']}" if gh["equivalent"] else "")
          + (f"；與訓練池重複 {gh['same_as_training']}" if gh["same_as_training"] else ""))
    print(f"3a  TNR 上限       {g3a['ceiling']:.3f}  單筆最多抓到 {g3a['max_caught']} 個，例：{g3a['example']}")
    print(f"    搜尋範圍       隨機 {g3a['searched']['random']} 組 + 窮舉小輸入 {g3a['searched']['exhaustive_small']} 組（上限是「找到的最大值」，真實上限只可能更高）")
    ach = f"{g3b['achievement']:.3f}" if g3b["achievement"] is not None else "—"
    print(f"3b  起點           {g3b['n_cases']} 筆測資：TNR {g3b['tnr']:.3f}，達成率 {ach}；"
          f"抓到 {len(g3b['caught'])}/{len(g3b['caught']) + len(g3b['missed'])} 種"
          + (f"，漏掉 {g3b['missed']}" if g3b["missed"] else ""))
    verdict = {"A": "✅ A 級（上限 = 1）", "B": "✅ B 級（上限 < 1，必須用達成率）", "FAIL": "❌ 未通過第二關"}[r["verdict"]]
    print(f"判定               {verdict}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--problem", required=True, help=f"題目 id：{list(registry.TESTGEN_PROBLEMS)}")
    p.add_argument("--random", type=int, default=20000, help="隨機輸入組數（預設 20000）")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    report = assess(args.problem, args.random, args.seed)
    print_card(report)
    out = registry.problem_dir(args.problem) / "assessment.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n完整結果已寫入 {out.relative_to(BACKEND)}")
    current = registry.TESTGEN_PROBLEMS[args.problem]["ceiling"]
    if current != report["gate_3a_ceiling"]["ceiling"]:
        print(f"⚠ registry.py 登記的上限是 {current}，這次估算是 {report['gate_3a_ceiling']['ceiling']}，請更新")


if __name__ == "__main__":
    main()
