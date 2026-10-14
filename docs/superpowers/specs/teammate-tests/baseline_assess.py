# -*- coding: utf-8 -*-
"""量測現有 in-process 評估（assess_problem）的耗時，並輸出每個解法的「答錯輸入集合」指紋。
用途：給 I1（安全批次執行器）當效能與一致性基準。對照檔：../baseline_assess.json

執行：
    cd backend
    python ../docs/superpowers/specs/teammate-tests/baseline_assess.py [--repeats 3] [--out 路徑.json]

特性：唯讀。呼叫 assess_problem.assess()（不是 main()），因此**不會**覆寫各題的 assessment.json。
預設輸出檔放在本腳本旁邊（含時間），不會覆蓋已提交的 baseline_assess.json。
"""
import argparse
import hashlib
import json
import os
import platform
import random
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[3] / "backend"
sys.path.insert(0, str(BACKEND))
from testgen import registry, assess_problem as ap   # noqa: E402
from problem import PROBLEMS                          # noqa: E402

N_RANDOM, SEED = 20000, 0


def fingerprints(pid):
    method = PROBLEMS[pid]["method"]
    spec = registry.load_spec(pid)
    s_plus = ap.load_pool(registry.pool_dir(pid, "correct"), method)
    s_minus = ap.load_pool(registry.pool_dir(pid, "wrong"), method)
    hd = registry.pool_dir(pid, "heldout")
    held = ap.load_pool(hd, method) if hd.exists() else {}
    ref_name = Path(registry.TESTGEN_PROBLEMS[pid]["reference"]).stem
    ref = s_plus[ref_name]["call"]
    rng = random.Random(SEED)
    inputs = [spec.random_args(rng) for _ in range(N_RANDOM)] + list(spec.small_args())
    expected = [ap.run(ref, a) for a in inputs]
    res = {"n_inputs": len(inputs), "pools": {}}
    for label, pool in (("S+", s_plus), ("S-", s_minus), ("heldout", held)):
        ks = ap.kill_sets(pool, inputs, expected)
        res["pools"][label] = {name: {"n_killed": len(k), "sha256_16": hashlib.sha256(json.dumps(sorted(k)).encode()).hexdigest()[:16]}
                               for name, k in ks.items()}
    return res


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--out", default=None)
    a = p.parse_args()
    report = {"date": datetime.now().isoformat(timespec="seconds"), "python": platform.python_version(),
              "platform": platform.platform(), "cpu_count": os.cpu_count(), "n_random": N_RANDOM, "seed": SEED,
              "repeats": a.repeats, "problems": {}}
    for pid in registry.TESTGEN_PROBLEMS:
        if not registry.pool_dir(pid, "wrong").exists():
            continue                            # 只登記到能產生虛擬碼的題目，沒有 S- 池
        times = []
        for _ in range(a.repeats):
            t0 = time.perf_counter()
            ap.assess(pid, N_RANDOM, SEED)
            times.append(time.perf_counter() - t0)
        fp = fingerprints(pid)
        report["problems"][pid] = {"assess_seconds": [round(t, 2) for t in times], "assess_median": round(statistics.median(times), 2),
                                   "n_inputs": fp["n_inputs"], "n_solutions": sum(len(v) for v in fp["pools"].values()),
                                   "fingerprints": fp["pools"]}
        print(pid, "times", [round(t, 2) for t in times], "inputs", fp["n_inputs"], flush=True)
    out = Path(a.out) if a.out else HERE / f"baseline_assess_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
