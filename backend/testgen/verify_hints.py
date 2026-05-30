"""
驗證 code-blind AI 提示系統能否正確診斷六種邏輯錯誤。

執行方式：
    cd backend
    python -m testgen.verify_hints
"""

import asyncio
import os
from pathlib import Path
from judge import judge
from ai import get_hint

SOLUTIONS_DIR = Path(__file__).parent / "solutions_wrong"

BUG_DESCRIPTIONS = {
    "always_len.py":       "直接回傳字串長度，完全沒找子字串",
    "count_unique.py":     "計算整個字串的不重複字元數，而非視窗長度",
    "inner_return.py":     "在內層迴圈提早 return，只處理第一個重複字元",
    "no_reset_left.py":    "遇到重複字元時，左邊界沒有正確往右移",
    "no_return.py":        "函式沒有 return 語句",
    "off_by_one_window.py":"視窗大小計算差 1",
}

SEP = "=" * 60


async def verify_one(filename: str) -> None:
    path = SOLUTIONS_DIR / filename
    code = path.read_text()

    results = await judge(code)
    passed = sum(1 for r in results if r["passed"])
    failed = [r for r in results if not r["passed"]]

    print(f"\n{SEP}")
    print(f"BUG：{filename}")
    print(f"預期行為：{BUG_DESCRIPTIONS[filename]}")
    print(f"測資結果：{passed}/17 通過")

    # 印出前 3 筆失敗的 actual 值，讓人快速確認 pattern
    print("失敗 pattern（前 3 筆）：")
    for r in failed[:3]:
        print(f"  input={r['input']!r:20s} expected={r['expected']}  actual={r['actual']}")

    # 印出 AI 會收到的 prompt 類型
    first_fail = failed[0] if failed else None
    error_type = first_fail["error_type"] if first_fail else None
    print(f"prompt 分支：{error_type or 'wrong_answer'}")

    # 呼叫 AI
    print("AI 提示：")
    hint = await get_hint(results)
    if hint:
        print(hint)
    else:
        print("（無提示：全部通過 或 API 未設定）")


async def main() -> None:
    print("=== code-blind AI 提示系統驗證 ===")
    print("確認每種 bug 的 AI 提示方向是否正確\n")

    if not os.environ.get("GROQ_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        print("⚠️  未偵測到 API key，AI 提示欄位會是空的。")
        print("   請先設定 GROQ_API_KEY 或 GEMINI_API_KEY。\n")

    for filename in BUG_DESCRIPTIONS:
        await verify_one(filename)

    print(f"\n{SEP}")
    print("驗證完成。請確認每個 AI 提示：")
    print("  ✓ 方向對應該 bug 的根本原因")
    print("  ✓ 結尾是問句（引導而非直接給答案）")
    print("  ✓ 沒有出現修正後的程式碼")


if __name__ == "__main__":
    asyncio.run(main())
