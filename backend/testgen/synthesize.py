#!/usr/bin/env python3
"""synthesize.py — 讀 commands_<version>.txt，跑 gen.py，用 reference 算 expected，
寫出可被 run_eval.py 載入的 tests_<version>.py 模組。

對應論文流程裡的「用 reference solution S* 為每筆生成測資補上 ground-truth」。

執行：
    cd backend
    python -m testgen.synthesize --commands testgen/commands_v1.txt --out testgen/tests_v1.py
    python -m testgen.synthesize --problem <id> --gen <生成器模組> --commands ... --out ...

生成器的 mode 若回傳 tuple，視為多參數題目，測資寫成 'args'；否則寫成單參數的 'input'。
"""
from __future__ import annotations
import argparse
import importlib
import inspect
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from testgen import registry  # noqa: E402


def _exec_solution(code: str):
    """exec 解法字串，回傳 Solution class。"""
    ns = {}
    exec(code, ns)
    return ns["Solution"]


def parse_command(line: str) -> tuple[str, dict]:
    """把 'doubled_distinct --n 6 --seed 11' 拆成 ('doubled_distinct', {n:6, seed:11})"""
    parts = shlex.split(line)
    mode = parts[0]
    kwargs = {}
    i = 1
    while i < len(parts):
        key = parts[i].lstrip("-")
        val = parts[i + 1]
        # 自動轉型
        try:                    kwargs[key] = int(val)
        except ValueError:
            try:                kwargs[key] = float(val)
            except ValueError:  kwargs[key] = val
        i += 2
    return mode, kwargs


def gen_one(gen_module, mode: str, kwargs: dict):
    """依 mode 名稱呼叫對應的生成器函式。"""
    func = gen_module.MODES[mode]
    # 過濾掉函式不接受的 kwargs（譬如把 --alphabet 傳給不吃 alphabet 的 mode）
    sig = inspect.signature(func)
    safe_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
    # 缺 seed 補 0
    if "seed" in sig.parameters and "seed" not in safe_kwargs:
        safe_kwargs["seed"] = 0
    return func(**safe_kwargs)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--problem", default="longest-substring",
                   help="題目 id（見 testgen/registry.py），決定 reference 與 method")
    p.add_argument("--gen", default="testgen.gen", help="生成器模組（需有 MODES 字典）")
    p.add_argument("--commands", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    from problem import PROBLEMS
    method = PROBLEMS[args.problem]["method"]
    gen_module = importlib.import_module(args.gen)
    Reference = _exec_solution(registry.reference_path(args.problem).read_text(encoding="utf-8"))
    ref_call = getattr(Reference(), method)

    cases = []
    with open(args.commands, encoding="utf-8") as f:
        idx = 0
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            idx += 1
            mode, kwargs = parse_command(line)
            try:
                generated = gen_one(gen_module, mode, kwargs)
            except Exception as e:
                print(f"  [WARN] 命令 #{idx} 失敗: {line}  ({e})")
                continue
            call_args = generated if isinstance(generated, tuple) else (generated,)
            expected = ref_call(*call_args)
            size = len(generated) if isinstance(generated, str) else len(repr(generated))
            is_stress = (mode.startswith("stress") or size >= 10000)
            arg_key = "args" if isinstance(generated, tuple) else "input"
            cases.append({
                "index": idx,
                arg_key: generated,
                "expected": expected,
                "is_stress": is_stress,
                "_source_command": line,
            })

    # 把 TEST_CASES 寫成 Python 模組（跟 problem.py 同 shape）
    out_path = Path(args.out)
    lines = [
        "# 自動產生 — 請勿手改。",
        f"# 來源命令：{Path(args.commands).name}",
        f"# 共 {len(cases)} 筆測資",
        "",
        "TEST_CASES = [",
    ]
    for c in cases:
        # 用 repr 保留 escape，is_stress 直接 True/False
        lines.append(
            f"    {{'index': {c['index']:>3}, "
            f"{'args' if 'args' in c else 'input'!r}: {c.get('args', c.get('input'))!r}, "
            f"'expected': {c['expected']!r}, "
            f"'is_stress': {c['is_stress']}, "
            f"'_source': {c['_source_command']!r}}},"
        )
    lines.append("]")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[synthesize] 寫入 {out_path} — {len(cases)} 筆測資")
    for c in cases:
        shown = repr(c.get("args", c.get("input")))
        prev = (shown[:30] + "...") if len(shown) > 30 else shown
        print(f"  #{c['index']:>2}  expected={c['expected']!r:>5}  input={prev}")


if __name__ == "__main__":
    main()
