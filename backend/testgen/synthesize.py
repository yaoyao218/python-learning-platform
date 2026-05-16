#!/usr/bin/env python3
"""synthesize.py — 讀 commands_<version>.txt，跑 gen.py，用 reference 算 expected，
寫出可被 run_eval.py 載入的 tests_<version>.py 模組。

對應論文流程裡的「用 reference solution S* 為每筆生成測資補上 ground-truth」。

執行：
    cd backend
    python -m testgen.synthesize --commands testgen/commands_v1.txt --out testgen/tests_v1.py
"""
from __future__ import annotations
import argparse
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

# 直接 import 生成器模組與 reference solution
from testgen import gen as gen_module  # noqa: E402

# Reference solution（論文中的 S*）
REFERENCE_PATH = HERE / "solutions_correct" / "sliding_window.py"


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


def gen_one(mode: str, kwargs: dict) -> str:
    """依 mode 名稱呼叫對應的生成器函式。"""
    func = gen_module.MODES[mode]
    # 過濾掉函式不接受的 kwargs（譬如把 --alphabet 傳給不吃 alphabet 的 mode）
    import inspect
    sig = inspect.signature(func)
    safe_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
    # 缺 seed 補 0
    if "seed" in sig.parameters and "seed" not in safe_kwargs:
        safe_kwargs["seed"] = 0
    return func(**safe_kwargs)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--commands", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    Reference = _exec_solution(Path(REFERENCE_PATH).read_text(encoding="utf-8"))
    ref = Reference()

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
                s = gen_one(mode, kwargs)
            except Exception as e:
                print(f"  [WARN] 命令 #{idx} 失敗: {line}  ({e})")
                continue
            expected = ref.lengthOfLongestSubstring(s)
            is_stress = (mode.startswith("stress") or len(s) >= 10000)
            cases.append({
                "index": idx,
                "input": s,
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
            f"'input': {c['input']!r}, "
            f"'expected': {c['expected']}, "
            f"'is_stress': {c['is_stress']}, "
            f"'_source': {c['_source_command']!r}}},"
        )
    lines.append("]")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[synthesize] 寫入 {out_path} — {len(cases)} 筆測資")
    for c in cases:
        prev = (c["input"][:30] + "...") if len(c["input"]) > 30 else c["input"]
        print(f"  #{c['index']:>2}  expected={c['expected']:>3}  input={prev!r}")


if __name__ == "__main__":
    main()
