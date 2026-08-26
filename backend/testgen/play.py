#!/usr/bin/env python3
"""play.py — 離線 CLI 模擬使用者寫程式 + 自動記錄完整 trace。

不需 uvicorn、不需前端，直接在 terminal 貼程式碼 → 即時看 trace + 寫進 session log。
適合：邊改邊看 backend 在做什麼、做專題 demo、產生報告素材。

執行：
    python -m testgen.play                              # 互動模式（貼程式碼後 Ctrl-D）
    python -m testgen.play --file my_solution.py        # 跑現成檔案
    python -m testgen.play --file foo.py --no-log       # 不寫 session log
"""
from __future__ import annotations
import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

# 強制開啟 logger（除非 --no-log）
os.environ.setdefault("TESTGEN_SESSION_LOG", "1")

CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def read_code_from_stdin() -> str:
    print(f"{CYAN}貼上你的程式碼，貼完按 Ctrl-D（Windows: Ctrl-Z 然後 Enter）：{RESET}")
    return sys.stdin.read()


async def play(code: str, write_log: bool = True, problem_id: str = "longest-substring"):
    # 延遲 import 避免在 sandbox 沒裝 openai 時整支腳本爆炸
    from judge import judge
    from ai import get_hint, build_prompt
    from problem import PROBLEMS
    from testgen import session_logger

    if not write_log:
        session_logger.LOG_ENABLED = False

    problem_title = PROBLEMS[problem_id]["title"]
    problem_context = PROBLEMS[problem_id]["ai_context"]

    print(f"\n{BOLD}━━━ 跑 judge（{problem_title}）━━━{RESET}")
    t0 = time.perf_counter()
    results = await judge(code, problem_id)
    judge_ms = (time.perf_counter() - t0) * 1000

    n_pass = sum(1 for r in results if r["passed"])
    n_total = len(results)
    fails = [r for r in results if not r["passed"]]

    if n_pass == n_total:
        print(f"  {GREEN}AC：{n_pass}/{n_total} 全過（耗時 {judge_ms:.0f} ms）{RESET}")
    else:
        print(f"  {RED}WA / RE：{n_pass}/{n_total}（耗時 {judge_ms:.0f} ms）{RESET}")
        ff = fails[0]
        print(f"\n  {RED}第一個失敗 → 前端會給學生看的：{RESET}")
        print(f"    #{ff['index']}  input = {ff['input']!r}")
        print(f"    expected = {ff['expected']}    actual = {ff['actual']}    "
              f"error_type = {ff['error_type'] or 'wrong_answer'}")

    if fails:
        print(f"\n  {DIM}全部失敗的測資：{RESET}")
        for r in fails:
            inp = str(r.get("input", ""))[:30]
            print(f"    {DIM}#{r['index']:>2}  input={inp!r:<32s}  got={r['actual']!r:<10s}  "
                  f"{r.get('error_type') or ''}{RESET}")

    # AI prompt
    print(f"\n{BOLD}━━━ 組裝 AI prompt ━━━{RESET}")
    prompt = build_prompt(results, problem_title, problem_context)
    if prompt is None:
        print(f"  {GREEN}全過 → 不需要 AI 提示{RESET}")
    else:
        print(f"  Prompt 長度：{len(prompt)} 字元")
        print(f"  {DIM}（前 200 字預覽）{RESET}")
        print(f"    {DIM}{prompt[:200]!r}...{RESET}")

    # AI hint
    print(f"\n{BOLD}━━━ 呼叫 Groq Llama ━━━{RESET}")
    t1 = time.perf_counter()
    hint = await get_hint(results, problem_title, problem_context)
    ai_ms = (time.perf_counter() - t1) * 1000
    if hint:
        print(f"  耗時：{ai_ms:.0f} ms")
        print(f"\n  {YELLOW}AI 提示：{RESET}")
        for line in hint.split("\n"):
            print(f"    {line}")
    elif prompt is None:
        print(f"  {GREEN}（沒提示）{RESET}")
    else:
        print(f"  {RED}AI 呼叫失敗（GROQ_API_KEY 可能沒設、或 quota 用完）{RESET}")

    total_ms = (time.perf_counter() - t0) * 1000
    print(f"\n{BOLD}━━━ 紀錄 ━━━{RESET}")
    if write_log and session_logger.LOG_ENABLED:
        await session_logger.log_submission(
            code=code, results=results, hint=hint,
            ai_prompt=prompt, elapsed_ms=total_ms,
        )
        print(f"  {GREEN}已寫入 {session_logger.LOG_PATH}{RESET}")
        print(f"  {DIM}用 `python -m testgen.view_session` 查看{RESET}")
    else:
        print(f"  {DIM}（--no-log，沒寫入）{RESET}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", type=str, default=None,
                   help="讀檔案內容當程式碼（不指定 = 從 stdin 貼上）")
    p.add_argument("--no-log", action="store_true",
                   help="不寫 session log")
    p.add_argument("--problem", type=str, default="longest-substring",
                   help="題目 id（longest-substring / valid-parentheses / median-two-sorted-arrays）")
    args = p.parse_args()

    if args.file:
        code = Path(args.file).read_text(encoding="utf-8")
    else:
        code = read_code_from_stdin()

    if not code.strip():
        print(f"{RED}沒有程式碼，結束{RESET}")
        sys.exit(1)

    asyncio.run(play(code, write_log=not args.no_log, problem_id=args.problem))


if __name__ == "__main__":
    main()
