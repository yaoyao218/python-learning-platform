#!/usr/bin/env python3
"""mask_demo.py — 示範遮罩（masking.py）：故意讓提示夾帶完整正解，印出遮罩前後的對照。

平常 AI 很少在提示裡放程式碼，網站上幾乎看不到遮罩出手；這個工具直接造出「洩漏答案」的提示，
走一次和網站相同的 sanitize_hint 流程（跑測資 → 請 AI 遮蔽 → 再跑測資驗證）。

前置：backend/.env 要有 GROQ_API_KEY（遮蔽那一步會呼叫 AI）。

執行：
    cd backend
    python -m testgen.mask_demo                          # 預設 best-time-stock
    python -m testgen.mask_demo --problem valid-parentheses
"""
from __future__ import annotations
import argparse
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv                       # noqa: E402

load_dotenv(BACKEND / ".env")

from ai import _MODEL, client                         # noqa: E402
from masking import extract_code_blocks, is_full_solution, sanitize_hint  # noqa: E402
from problem import PROBLEMS                          # noqa: E402
from testgen import registry                          # noqa: E402


async def run(problem_id: str) -> None:
    problem = PROBLEMS[problem_id]
    solution = registry.reference_path(problem_id).read_text(encoding="utf-8").strip()
    leaked = (
        "你可以參考下面這段寫法，照著改就能過了：\n\n"
        f"```python\n{solution}\n```\n\n"
        "你覺得每一步在做什麼？"
    )
    print(f"題目：{problem['title']}（{problem_id}）｜模型：{_MODEL}\n")
    print("=" * 30, "遮罩前（AI 原本的提示）", "=" * 30)
    print(leaked)
    print(f"\n→ 這段程式碼能通過測資嗎？{'能，算洩漏答案' if await is_full_solution(solution, problem_id) else '不能'}\n")

    result = await sanitize_hint(leaked, problem_id, problem["title"], client, _MODEL)

    print("=" * 30, "遮罩後（學生實際看到的）", "=" * 30)
    print(result)
    blocks = extract_code_blocks(result)
    if blocks:
        still = [await is_full_solution(code, problem_id) for _, code in blocks]
        print(f"\n→ 遮罩後的程式碼還能通過測資嗎？{'能（遮罩失敗）' if any(still) else '不能，已安全'}")
    else:
        print("\n→ 遮罩後沒有程式碼：整段被換成提示文字（AI 遮不乾淨或遮蔽失敗時的處理）")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--problem", default="best-time-stock", choices=list(registry.TESTGEN_PROBLEMS))
    asyncio.run(run(p.parse_args().problem))


if __name__ == "__main__":
    main()
