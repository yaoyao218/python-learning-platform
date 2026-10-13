#!/usr/bin/env python3
"""export_round_to_problem.py — 把某題「最後一輪」的測資（rounds/rN_tests.json）寫回 backend/problem.py。

只改 problem.py 裡該題的 `_XXX_CASES = [ ... ]` 清單（例如 `_BEST_TIME_STOCK_CASES`），不動其他部分。

排序規則（讓學生看到的「第一個失敗」有教學意義）：
  1. 前 K 道官方範例照原順序（K 由 --official 指定；必須與 problem.py 目前最前面的 K 道相同，否則報錯）；
  2. 其餘非壓力測資依輸入長度由短到長（長度相同維持原順序）；
  3. 壓力測資（is_stress）放最後；
  4. index 從 1 重新編號。
格式：沿用該題 problem.py 現有清單的寫法——單一字串參數用 "input"，多參數（或陣列）用 "args"。

安全檢查：這一輪的測資必須「包含」problem.py 目前的所有案例，否則中止並列出會被丟掉的案例
（例如拿到的是舊基準輪次，會把現有測資蓋掉）。確定要丟掉才加 --allow-drop。

預設只印出差異（不寫檔）；加 --write 才寫入。連續執行兩次結果相同（冪等）。

執行：
    cd backend
    python -m testgen.export_round_to_problem --problem best-time-stock --round 1 --official 2
    python -m testgen.export_round_to_problem --problem best-time-stock --round 1 --official 2 --write

官方範例筆數：longest-substring 3、best-time-stock 2、longest-valid-parentheses 3。
"""
from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

HEADER_PREFIXES = ("# 由 testgen/export_round_to_problem.py", "# 第 0 輪")


def list_name(problem_id: str) -> str:
    return "_" + problem_id.upper().replace("-", "_") + "_CASES"


def find_block(lines: list[str], name: str) -> tuple[int, int]:
    """回傳 (起始行, 結束行) —— `NAME = [` 到單獨一行 `]`（含）。行號從 0 起算。"""
    start = next((i for i, ln in enumerate(lines) if re.match(rf"^{re.escape(name)}\s*=\s*\[\s*$", ln)), None)
    if start is None:
        raise SystemExit(f"在 problem.py 找不到 `{name} = [`")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].rstrip() == "]"), None)
    if end is None:
        raise SystemExit(f"找不到 `{name}` 清單的結尾 `]`")
    return start, end


def parse_block(lines: list[str]) -> tuple[list[dict], dict[str, str]]:
    """解析清單內的案例，並記下每個案例前面的註解（供保留）。"""
    cases, comments, pending = [], {}, None
    for ln in lines:
        s = ln.strip()
        if s.startswith("#"):
            pending = s
        elif s.startswith("{"):
            case = ast.literal_eval(s.rstrip(","))
            cases.append(case)
            if pending:
                comments[case_key(case)] = pending
            pending = None
    return cases, comments


def call_args(case: dict) -> tuple:
    return tuple(case["args"]) if "args" in case else (case["input"],)


def case_key(case: dict) -> str:
    return repr(call_args(case))


def size(case: dict) -> int:
    n = 0
    for a in call_args(case):
        n += len(a) if hasattr(a, "__len__") else 1
    return n


def normalize(case: dict, style: str) -> dict:
    """依現有清單的寫法輸出：input（單一字串參數）或 args（多參數／陣列）。"""
    args = call_args(case)
    out = {"expected": case["expected"], "is_stress": bool(case.get("is_stress", False))}
    if style == "input":
        if len(args) != 1:
            raise SystemExit(f"這一題現有寫法是單一參數（input），但案例有 {len(args)} 個參數：{args!r}")
        out["input"] = args[0]
    else:
        out["args"] = args
    return out


def order_cases(new_cases: list[dict], current: list[dict], official: int, style: str, allow_drop: bool = False) -> list[dict]:
    new_keys = {case_key(normalize(c, style)) for c in new_cases}
    missing = [case_key(c) for c in current if case_key(c) not in new_keys]
    if missing and not allow_drop:
        raise SystemExit(f"這一輪的測資沒有包含 problem.py 目前的 {len(missing)} 道案例，匯出會把它們丟掉：{missing[:5]}\n"
                         "請確認選對了輪次（例如不是舊基準輪次）。確定要丟掉才加 --allow-drop。")
    if official > len(new_cases):
        raise SystemExit(f"--official {official} 大於這一輪的測資數 {len(new_cases)}")
    head = [normalize(c, style) for c in new_cases[:official]]
    want = [normalize(c, style) for c in current[:official]]
    if [case_key(c) for c in head] != [case_key(c) for c in want] or [c["expected"] for c in head] != [c["expected"] for c in want]:
        raise SystemExit("這一輪最前面的 K 道與 problem.py 目前最前面的 K 道不同——請確認 --official 是否正確，"
                         "或這一輪是否不是由 problem.py 的現有測資延伸而來。\n"
                         f"  problem.py：{[case_key(c) for c in want]}\n  這一輪    ：{[case_key(c) for c in head]}")
    rest = [normalize(c, style) for c in new_cases[official:]]
    seen, dup = set(), []
    for c in head + rest:
        k = case_key(c)
        if k in seen:
            dup.append(k)
        seen.add(k)
    if dup:
        raise SystemExit(f"測資中有重複的輸入：{dup[:3]}")
    normal = sorted([c for c in rest if not c["is_stress"]], key=size)       # sorted 是穩定排序
    stress = [c for c in rest if c["is_stress"]]
    return head + normal + stress


def render(cases: list[dict], comments: dict[str, str], official: int, round_no: int, style: str) -> list[str]:
    out = []
    for i, c in enumerate(cases, 1):
        key = case_key(c)
        if i <= official:
            out.append(f"    # LC 官方範例 {i}")
        elif key in comments:
            out.append(f"    {comments[key]}")
        else:
            out.append(f"    # r{round_no}")
        body = repr(c["input"]) if style == "input" else repr(tuple(c["args"]))
        key_name = "input" if style == "input" else "args"
        out.append(f'    {{"index": {i}, "{key_name}": {body}, "expected": {c["expected"]!r}, "is_stress": {c["is_stress"]}}},')
    return out


def build_new_source(source: str, problem_id: str, new_cases: list[dict], official: int, round_no: int,
                     allow_drop: bool = False) -> tuple[str, dict]:
    lines = source.splitlines()
    name = list_name(problem_id)
    start, end = find_block(lines, name)
    current, comments = parse_block(lines[start + 1:end])
    if not current:
        raise SystemExit(f"{name} 目前是空的，無法判斷寫法（input 或 args）")
    style = "input" if "input" in current[0] else "args"
    ordered = order_cases(new_cases, current, official, style, allow_drop)
    body = render(ordered, comments, official, round_no, style)

    # 清單上方：移除舊的產生器註解與過時的「第 0 輪」註解，再加上新的
    top = start
    while top > 0 and lines[top - 1].startswith(HEADER_PREFIXES):
        top -= 1
    header = [f"# 由 testgen/export_round_to_problem.py 從 r{round_no}_tests.json 產生：共 {len(ordered)} 道，"
              f"前 {official} 道為 LC 官方範例，其餘依輸入長度由短到長，壓力測資在最後。"]
    new_lines = lines[:top] + header + [lines[start]] + body + [lines[end]] + lines[end + 1:]
    text = "\n".join(new_lines) + ("\n" if source.endswith("\n") else "")
    info = {"total": len(ordered), "official": official, "stress": sum(c["is_stress"] for c in ordered), "style": style,
            "previous_total": len(current)}
    return text, info


def load_cases(problem_id: str, round_no: int, tests_json: str | None) -> list[dict]:
    if tests_json:
        data = json.loads(Path(tests_json).read_text(encoding="utf-8"))
        cases = data["cases"]
        for c in cases:
            if "args" in c:
                c["args"] = tuple(c["args"])
        return cases
    from testgen import rounds
    return rounds.load_round_tests(problem_id, round_no)["cases"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--problem", required=True)
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--official", type=int, required=True, help="最前面官方範例的筆數")
    ap.add_argument("--write", action="store_true", help="真的寫入 problem.py（預設只印差異）")
    ap.add_argument("--allow-drop", action="store_true", help="允許丟掉 problem.py 目前有、但這一輪沒有的案例")
    ap.add_argument("--problem-file", default=str(BACKEND / "problem.py"), help="要改的檔案（測試用）")
    ap.add_argument("--tests-json", default=None, help="直接指定測資 JSON（測試用）")
    a = ap.parse_args()

    path = Path(a.problem_file)
    source = path.read_text(encoding="utf-8")
    cases = load_cases(a.problem, a.round, a.tests_json)
    new_source, info = build_new_source(source, a.problem, cases, a.official, a.round, a.allow_drop)

    diff = list(difflib.unified_diff(source.splitlines(), new_source.splitlines(), "problem.py（目前）", "problem.py（匯出後）", lineterm="", n=1))
    print(f"題目 {a.problem}｜第 {a.round} 輪｜寫法：{info['style']}｜{info['previous_total']} 道 → {info['total']} 道"
          f"（官方範例 {info['official']}、壓力測資 {info['stress']}）")
    if not diff:
        print("沒有差異（已經是最新）。")
        return
    print("\n".join(diff))
    if a.write:
        path.write_text(new_source, encoding="utf-8")
        print(f"\n已寫入 {path}")
    else:
        print("\n（預設只印出差異，沒有寫檔；確認後加 --write）")


if __name__ == "__main__":
    main()
