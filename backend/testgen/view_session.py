#!/usr/bin/env python3
"""view_session.py — 把 session JSONL 漂亮印出來。

執行：
    python -m testgen.view_session                  # 看當天最新 log
    python -m testgen.view_session --file PATH      # 指定檔
    python -m testgen.view_session --last 5         # 只看最後 5 筆
    python -m testgen.view_session --summary        # 統計摘要
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SESSIONS_DIR = HERE / "sessions"

# ANSI 顏色
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def latest_log():
    files = sorted(SESSIONS_DIR.glob("*.jsonl"))
    return files[-1] if files else None


def read_records(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def fmt_code(code: str, max_lines: int = 12) -> str:
    lines = code.strip().split("\n")
    if len(lines) <= max_lines:
        return "\n".join(f"    {DIM}│{RESET} {l}" for l in lines)
    return ("\n".join(f"    {DIM}│{RESET} {l}" for l in lines[:max_lines])
            + f"\n    {DIM}│ ... (+{len(lines) - max_lines} 行){RESET}")


def print_record(i: int, r: dict):
    ts = r.get("ts", "?")
    elapsed = r.get("elapsed_ms")
    elapsed_str = f"{elapsed:.0f}ms" if elapsed else "?"
    n_pass = r.get("n_pass", 0)
    n_total = r.get("n_test_cases", 0)
    n_fail = r.get("n_fail", 0)

    status = (f"{GREEN}AC{RESET}" if n_fail == 0
              else f"{RED}WA × {n_fail}{RESET}")

    print(f"\n{BOLD}━━━ 提交 #{i + 1} ━━━{RESET}")
    print(f"  {DIM}時間：{ts}    耗時：{elapsed_str}    "
          f"通過：{n_pass}/{n_total}    結果：{status}{RESET}")

    # 學生程式碼
    print(f"\n  {CYAN}學生提交的程式碼：{RESET}")
    print(fmt_code(r.get("code", "")))

    # 第一個失敗
    if n_fail > 0:
        idx = r.get("first_fail_index")
        inp = r.get("first_fail_input")
        exp = r.get("first_fail_expected")
        act = r.get("first_fail_actual")
        et = r.get("first_fail_error_type")
        print(f"\n  {RED}第一個失敗（前端會給學生看的）：{RESET}")
        print(f"    測資 #{idx}  input = {inp!r}")
        print(f"    expected = {exp}    actual = {act}    error_type = {et or 'wrong_answer'}")

    # AI 部分
    if r.get("ai_hint"):
        print(f"\n  {YELLOW}AI 提示：{RESET}")
        hint = r["ai_hint"]
        for line in hint.split("\n"):
            print(f"    {line}")
        prompt = r.get("ai_prompt")
        if prompt:
            print(f"\n  {DIM}（送給 Groq 的 prompt 長度 = {len(prompt)} 字元）{RESET}")
    elif n_fail == 0:
        print(f"\n  {GREEN}全部通過，沒有觸發 AI 提示。{RESET}")

    # 所有失敗 case 簡表
    if n_fail > 1:
        print(f"\n  {DIM}全部失敗的測資（學生其實只會看到第一筆）：{RESET}")
        for case_r in r.get("results", []):
            if not case_r.get("passed"):
                idx = case_r["index"]
                inp = str(case_r.get("input", ""))[:30]
                act = case_r.get("actual")
                et = case_r.get("error_type") or ""
                print(f"    {DIM}#{idx:>2}  {inp!r:<32s}  →  got {act!r:<10s}  {et}{RESET}")


def print_summary(records: list[dict]):
    if not records:
        print("（無紀錄）")
        return
    n = len(records)
    n_ac = sum(1 for r in records if r.get("n_fail", 0) == 0)
    avg_ms = sum(r.get("elapsed_ms", 0) or 0 for r in records) / n
    print(f"\n{BOLD}=== Session 摘要 ==={RESET}")
    print(f"  總提交次數：{n}")
    print(f"  AC（全過）：{n_ac}  ({100 * n_ac / n:.1f}%)")
    print(f"  WA / RE：{n - n_ac}")
    print(f"  平均耗時：{avg_ms:.0f} ms")
    # 最常失敗的測資
    fail_counts = {}
    for r in records:
        idx = r.get("first_fail_index")
        if idx is not None:
            fail_counts[idx] = fail_counts.get(idx, 0) + 1
    if fail_counts:
        print(f"\n  學生最常踩雷的測資 (top 5)：")
        for idx, c in sorted(fail_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"    #{idx:>2}  被踩到 {c} 次")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", type=str, default=None)
    p.add_argument("--last", type=int, default=None)
    p.add_argument("--summary", action="store_true")
    args = p.parse_args()

    path = Path(args.file) if args.file else latest_log()
    if not path or not path.exists():
        print(f"找不到 log 檔（看了 {SESSIONS_DIR}）")
        print(f"先啟用 logger：TESTGEN_SESSION_LOG=1 uvicorn main:app --reload")
        sys.exit(1)
    print(f"{DIM}讀取 {path}{RESET}")
    records = read_records(path)
    if not records:
        print("（log 是空的——還沒有提交過任何程式碼）")
        return
    if args.last:
        records = records[-args.last:]

    if args.summary:
        print_summary(records)
    else:
        for i, r in enumerate(records):
            print_record(i, r)
        print_summary(records)


if __name__ == "__main__":
    main()
