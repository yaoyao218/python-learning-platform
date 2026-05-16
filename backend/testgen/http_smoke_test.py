#!/usr/bin/env python3
"""http_smoke_test.py — 用 FastAPI TestClient 從 HTTP 層測 /submit，
模擬前端真正打 API 的行為，不需要啟動 uvicorn。

跟 smoke_test.py 差異：smoke_test 直接呼叫 judge()，這支跑完整 ASGI 棧
（含 CORS middleware、Pydantic 驗證、main.py 的 endpoint handler）。

執行：
    cd backend
    python -m testgen.http_smoke_test
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
INFO = "\033[33m●\033[0m"


# 學生提交劇本：(描述, 程式碼, 預期第一個失敗的 index)
SCENARIOS = [
    (
        "正解 sliding window 應全過",
        """
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen = set(); left = best = 0
        for right in range(len(s)):
            while s[right] in seen:
                seen.remove(s[left]); left += 1
            seen.add(s[right])
            best = max(best, right - left + 1)
        return best
""",
        None,  # 全過
    ),
    (
        "return len(s) 應在 #1 abcabcbb 上 fail",
        "class Solution:\n    def lengthOfLongestSubstring(self, s):\n        return len(s)",
        1,
    ),
    (
        "return len(set(s)) 應在 #3 pwwkew 上 fail",
        "class Solution:\n    def lengthOfLongestSubstring(self, s):\n        return len(set(s))",
        3,
    ),
    (
        "syntax error 應觸發 syntax_error error_type",
        "class Solution:\n    def lengthOfLongestSubstring(self, s)\n        return 0",
        1,  # 第一筆就會 fail（語法錯誤所有 case 都 fail）
    ),
]


async def main():
    try:
        from httpx import AsyncClient, ASGITransport
        from main import app
    except ImportError as e:
        print(f"{FAIL} 缺少依賴：{e}")
        print(f"{INFO} pip install -r requirements.txt 後重跑")
        sys.exit(1)

    failures = []

    # 用 mock 把 ai.get_hint 換掉，避免實際打 Groq（要 GROQ_API_KEY）
    async def fake_hint(code, results):
        all_passed = all(r["passed"] for r in results)
        return None if all_passed else "（mocked）AI 提示在此"

    print(f"\n=== HTTP 層測試（模擬前端 POST /submit）===\n")
    with patch("main.get_hint", side_effect=fake_hint):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            for label, code, expected_first_fail in SCENARIOS:
                resp = await client.post("/submit", json={"code": code})
                ok_status = resp.status_code == 200
                if not ok_status:
                    print(f"  {FAIL}  {label}：HTTP {resp.status_code}")
                    failures.append(label); continue

                data = resp.json()
                results = data["results"]
                hint = data["hint"]
                fails = [r for r in results if not r["passed"]]

                if expected_first_fail is None:
                    ok = (not fails) and (hint is None)
                    if ok:
                        print(f"  {PASS}  {label}：全過 ({len(results)}/{len(results)})，無 AI 提示")
                    else:
                        print(f"  {FAIL}  {label}：失敗 {len(fails)} 筆，hint={hint!r}")
                        failures.append(label)
                else:
                    first = fails[0] if fails else None
                    ok = first and first["index"] == expected_first_fail and hint is not None
                    if ok:
                        print(f"  {PASS}  {label}")
                        print(f"      第一個失敗：#{first['index']} input={first['input']!r}")
                        print(f"      expected={first['expected']} actual={first['actual']} "
                              f"error_type={first['error_type']}")
                    else:
                        print(f"  {FAIL}  {label}")
                        print(f"      實際第一個失敗：{first}")
                        print(f"      hint={hint!r}")
                        failures.append(label)
                print()

    print("=== HTTP 預檢結果 ===")
    if failures:
        print(f"  {FAIL} 失敗劇本：{failures}")
        sys.exit(1)
    else:
        print(f"  {PASS} HTTP 層全綠！前端真的打 /submit 行為一致。")


if __name__ == "__main__":
    asyncio.run(main())
