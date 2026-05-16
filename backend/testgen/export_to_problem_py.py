#!/usr/bin/env python3
"""export_to_problem_py.py — 把 tests_v{N}.py 的測資集合併 LeetCode 官方範例，
產出可直接 swap 進 backend/problem.py 的格式。

設計取捨：
  * **保留 LeetCode 官方範例（baseline #1-3）** 作為教學起點
    abcabcbb / bbbbb / pwwkew 來自 LC 3 的題目敘述本身，學生看到題目時就熟悉。
    這三筆放在最前面，讓學生有 "AC 第一筆" 的成就感。
  * **再排入 v4 高鑑別度案例**（caught >=5/6 的）為主力，按 input 長度排序
    讓學生看到的「第一個失敗」是有教學意義的，不是 50000 字元的 stress test。
  * **最後放壓力測試**（is_stress=True），用 10 秒 timeout。

執行：
    cd backend
    python -m testgen.export_to_problem_py --tests testgen.tests_v4 --out problem_v4.py
"""
from __future__ import annotations
import argparse
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))


# LeetCode 官方範例（直接從 LC 3 題目敘述抓的三筆）
LEETCODE_EXAMPLES = [
    {"input": "abcabcbb", "expected": 3, "_note": "LC 官方範例 1"},
    {"input": "bbbbb",    "expected": 1, "_note": "LC 官方範例 2"},
    {"input": "pwwkew",   "expected": 3, "_note": "LC 官方範例 3"},
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tests", default="testgen.tests_v4",
                   help="從哪個 Python 模組讀 TEST_CASES")
    p.add_argument("--out", default="problem_v4.py",
                   help="輸出檔名（相對 backend/）")
    p.add_argument("--min-catch", type=int, default=5,
                   help="只匯出 caught>=min_catch 的案例（搭配 feedback JSON）")
    p.add_argument("--feedback", default="testgen/feedback_v4.json",
                   help="同名版本的 feedback JSON，用來判斷 catch 數")
    args = p.parse_args()

    # 載入測資模組
    mod = importlib.import_module(args.tests)
    src_cases = list(mod.TEST_CASES)

    # 載入反饋報告以挑出高鑑別度案例
    import json
    fb_path = BACKEND / args.feedback
    fb = json.loads(fb_path.read_text())
    catch_map = fb["command_value"]  # idx -> caught count

    # 篩選高鑑別度案例
    high_value = []
    others = []
    for tc in src_cases:
        idx = str(tc["index"])
        catch = catch_map.get(idx, catch_map.get(int(idx), 0))
        if catch >= args.min_catch:
            high_value.append((catch, tc))
        else:
            others.append((catch, tc))

    # 排序：高鑑別度按長度排（短→長），壓力測試最後
    high_value.sort(key=lambda x: (x[1]["is_stress"], len(x[1]["input"])))

    # 組裝最終列表：官方範例 → 高鑑別度 → 壓力 → 其他
    final = []
    next_idx = 1
    for ex in LEETCODE_EXAMPLES:
        final.append({
            "index": next_idx,
            "input": ex["input"],
            "expected": ex["expected"],
            "is_stress": False,
            "_note": ex["_note"],
        })
        next_idx += 1
    for catch, tc in high_value:
        final.append({
            "index": next_idx,
            "input": tc["input"],
            "expected": tc["expected"],
            "is_stress": tc["is_stress"],
            "_note": f"v4: catch {catch}/6 from {tc.get('_source', '?')[:40]}",
        })
        next_idx += 1

    # 寫出 problem.py 格式
    lines = [
        "# 自動產出 — 由 testgen/export_to_problem_py.py 從 tests_v4 + LC 官方範例組成。",
        f"# {next_idx - 1} 筆測資；首 3 筆為 LeetCode 官方範例（學生熱身用），",
        "# 之後為論文方法收斂出的高鑑別度測資（catch>=5/6 的 S- bugs）。",
        "",
        "TEST_CASES = [",
    ]
    for c in final:
        note = c.pop("_note", "")
        # 把 input 用 repr 避免 escape 問題
        line = (
            f"    {{\"index\": {c['index']:>2}, "
            f"\"input\": {c['input']!r}, "
            f"\"expected\": {c['expected']}, "
            f"\"is_stress\": {c['is_stress']}}},"
        )
        # 加註解
        if note:
            line = f"    # {note}\n{line}"
        lines.append(line)
    lines.append("]")

    out_path = BACKEND / args.out
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[export] 寫入 {args.out} — {len(final)} 筆測資")
    print(f"  官方範例：3 筆")
    print(f"  v4 高鑑別度（catch>={args.min_catch}）：{len(high_value)} 筆")
    print(f"  丟棄低鑑別度：{len(others)} 筆")


if __name__ == "__main__":
    main()
