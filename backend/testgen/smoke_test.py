#!/usr/bin/env python3
"""smoke_test.py — 一鍵預檢，跑通就可以放心開 uvicorn。

不需 pytest，不啟動 server，純 in-process 把 5 個風險點掃一遍：

  1. 核心模組能 import（problem / judge / executor）
  2. problem.py 載入正確 schema
  3. reference 正解全過 TEST_CASES（TPR 在線上判 = 1.0）
  4. 6 個常見 bug 解都會至少 fail 一筆（學生踩雷會被攔下）
  5. ai.build_prompt 對失敗結果能正確選擇分支（不打 Groq API）

執行：
    cd backend
    python -m testgen.smoke_test
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
INFO = "\033[33m●\033[0m"


def check(name, ok, detail=""):
    sym = PASS if ok else FAIL
    print(f"  {sym}  {name}" + (f"  ({detail})" if detail else ""))
    return ok


async def main():
    failures = []

    print("\n=== 預檢 1：核心模組 import ===")
    try:
        import problem, judge, executor
        check("import problem / judge / executor", True,
              f"problem.TEST_CASES = {len(problem.TEST_CASES)} 筆")
    except Exception as e:
        check("import 核心模組", False, str(e))
        print(f"\n  → 通常是 backend/ 不在 PYTHONPATH，或 requirements 沒裝。")
        sys.exit(1)

    has_ai = True
    try:
        import ai  # noqa: F401
        check("import ai（依賴 openai）", True)
    except ImportError as e:
        has_ai = False
        check("import ai", False, f"{e}（先 pip install -r requirements.txt）")
        print(f"  {INFO} 預檢 5 會跳過 prompt 檢查，其他繼續。")

    print("\n=== 預檢 2：problem.py 格式檢查 ===")
    required = {"index", "input", "expected", "is_stress"}
    schema_ok = all(required.issubset(tc.keys()) for tc in problem.TEST_CASES)
    if not check("每筆 schema 齊全（index/input/expected/is_stress）", schema_ok):
        failures.append("schema")
    indices_unique = len({tc["index"] for tc in problem.TEST_CASES}) == len(problem.TEST_CASES)
    if not check("測資 index 不重複", indices_unique):
        failures.append("dup_index")

    print("\n=== 預檢 3：reference 正解全過 ===")
    REF = HERE / "solutions_correct" / "sliding_window.py"
    ref_code = REF.read_text(encoding="utf-8")
    results = await judge.judge(ref_code)
    all_pass = all(r["passed"] for r in results)
    n_pass = sum(1 for r in results if r["passed"])
    if not check("reference 全過 problem.TEST_CASES", all_pass,
                 f"{n_pass}/{len(results)} 通過"):
        failures.append("ref_solution")
        for r in results:
            if not r["passed"]:
                print(f"      ↳ #{r['index']} input={r['input']!r} "
                      f"expected={r['expected']} actual={r['actual']}")

    print("\n=== 預檢 4：6 個錯誤解都會被攔下（至少 1 筆 fail）===")
    s_minus_dir = HERE / "solutions_wrong"
    survivors = []
    for sol_file in sorted(s_minus_dir.glob("*.py")):
        code = sol_file.read_text(encoding="utf-8")
        rs = await judge.judge(code)
        fails = [r for r in rs if not r["passed"]]
        sname = sol_file.name
        if not fails:
            survivors.append(sname)
            check(f"{sname:<22s}", False, "全過（漏網的 bug）")
        else:
            ff = fails[0]
            check(f"{sname:<22s}", True,
                  f"被擋下：#{ff['index']} input={str(ff['input'])[:20]!r}")
    if survivors:
        failures.append(f"survivors={survivors}")

    print("\n=== 預檢 5：ai.build_prompt 對各失敗類型能組 prompt ===")
    if not has_ai:
        print(f"  {INFO} 跳過（裝 requirements 後重跑即驗證）")
    else:
        scenarios = [
            ("syntax_error", "def f(\n  pass"),
            ("runtime_error",
             "class Solution:\n    def lengthOfLongestSubstring(self, s):\n        return 1/0"),
            ("no_return",
             "class Solution:\n    def lengthOfLongestSubstring(self, s):\n        pass"),
            ("wrong_answer",
             "class Solution:\n    def lengthOfLongestSubstring(self, s):\n        return len(s)"),
        ]
        for label, code in scenarios:
            try:
                rs = await judge.judge(code)
                prompt = ai.build_prompt(code, rs)
                ok = prompt is not None and isinstance(prompt, str) and len(prompt) > 100
                if not check(f"build_prompt for {label}", ok,
                             f"prompt 長度 = {len(prompt) if prompt else 0}"):
                    failures.append(f"prompt_{label}")
            except Exception as e:
                check(f"build_prompt for {label}", False, str(e))
                failures.append(f"prompt_{label}")

    print("\n=== 預檢結果 ===")
    if failures:
        print(f"  {FAIL} 失敗項目：{failures}")
        print(f"  {INFO} 不要 push！照上方紅項提示修，或回滾：")
        print(f"     cp problem_old.py problem.py")
        sys.exit(1)
    else:
        print(f"  {PASS} 所有預檢通過！可以放心啟動 uvicorn 跟前端做線上測試。")
        print()
        print(f"  下一步：")
        print(f"    1) uvicorn main:app --reload --port 8000")
        print(f"    2) （另開 terminal）cd ../frontend && npm run dev")
        print(f"    3) http://localhost:5173 跑 TESTING_GUIDE.md 的 6 種 bug 解")


if __name__ == "__main__":
    asyncio.run(main())
