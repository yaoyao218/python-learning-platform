# -*- coding: utf-8 -*-
"""讀取 teammate-guide.md 第 3 節的進度總表，彙整進度並檢查是否有不合規的列。給負責人追蹤用，唯讀。

執行（在 repo 根目錄）：
    python docs/superpowers/specs/teammate-tests/progress_check.py
    python docs/superpowers/specs/teammate-tests/progress_check.py --run-tests   # 另外執行後端測試
    python docs/superpowers/specs/teammate-tests/progress_check.py --stale-days 7

檢查項目：
  1. 「完成」必須有證據；「卡住」必須有備註；
  2. 「待審」「完成」的產出檔案都必須存在；
  3. 「進行中」超過 --stale-days 天沒有更新會被標出；
  4. 狀態必須是 未開始／進行中／待審／完成／卡住；
  5. 沒有負責人卻已開始的列會被標出；
  6. 同時讀取第 5 節的問題紀錄：列出「需負責人決定」「待處理」的問題，並標出「影響方法＝是」但狀態不是「需負責人決定」的列。
結束碼：有問題為 1，沒有為 0（方便在日後接到 CI）。
"""
import argparse
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
GUIDE = HERE.parent / "teammate-guide.md"
STATUSES = ["未開始", "進行中", "待審", "完成", "卡住"]
COLS = ["ID", "內容", "負責", "狀態", "最後更新", "產出檔案", "證據", "備註"]
ISSUE_COLS = ["ID", "現象", "排除結果", "暫行處理", "影響方法", "狀態", "負責", "日期"]
ISSUE_STATUSES = ["已知", "待處理", "需負責人決定", "已排除"]


def parse_table(text, start, end, cols, name):
    m = re.search(rf"<!-- {start} -->(.*?)<!-- {end} -->", text, re.S)
    if not m:
        raise SystemExit(f"找不到{name}（{start}／{end} 標記）")
    rows = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- "):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0] == "ID":
            continue
        cells += [""] * (len(cols) - len(cells))
        rows.append(dict(zip(cols, cells[:len(cols)])))
    return rows


def parse_board(text):
    return parse_table(text, "BOARD:START", "BOARD:END", COLS, "進度總表")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-tests", action="store_true", help="另外執行後端測試")
    ap.add_argument("--stale-days", type=int, default=7)
    a = ap.parse_args()

    text = GUIDE.read_text(encoding="utf-8")
    rows = parse_board(text)
    issues = parse_table(text, "ISSUES:START", "ISSUES:END", ISSUE_COLS, "問題紀錄")
    problems = []
    by_status = Counter(r["狀態"] for r in rows)
    by_owner = defaultdict(Counter)

    for r in rows:
        rid, st = r["ID"], r["狀態"]
        by_owner[r["負責"] or "（未指派）"][st] += 1
        if st not in STATUSES:
            problems.append(f"{rid}: 狀態「{st}」不在 {STATUSES}")
            continue
        if st == "完成" and not r["證據"]:
            problems.append(f"{rid}: 標示「完成」但沒有證據")
        if st == "卡住" and not r["備註"]:
            problems.append(f"{rid}: 標示「卡住」但沒有備註")
        if st != "未開始" and not r["負責"]:
            problems.append(f"{rid}: 已開始（{st}）但沒有負責人")
        if st in ("待審", "完成"):
            files = [f.strip().strip("`") for f in r["產出檔案"].split(",") if f.strip()]
            if not files:
                problems.append(f"{rid}: {st} 但沒有列出產出檔案")
            for f in files:
                if not (REPO / f).exists():
                    problems.append(f"{rid}: 產出檔案不存在：{f}")
        if st == "進行中" and r["最後更新"]:
            try:
                age = (date.today() - datetime.strptime(r["最後更新"], "%Y-%m-%d").date()).days
                if age > a.stale_days:
                    problems.append(f"{rid}: 進行中但已 {age} 天沒更新")
            except ValueError:
                problems.append(f"{rid}: 最後更新格式應為 YYYY-MM-DD（目前「{r['最後更新']}」）")

    total = len(rows)
    done = by_status.get("完成", 0)
    print(f"進度：{done}/{total} 完成（{done / total:.0%}）" if total else "進度表是空的")
    print("狀態統計：", "　".join(f"{s} {by_status.get(s, 0)}" for s in STATUSES))
    print("\n各負責人：")
    for owner, c in sorted(by_owner.items()):
        print(f"  {owner}: " + "　".join(f"{s} {c.get(s, 0)}" for s in STATUSES if c.get(s, 0)))
    blocked = [r for r in rows if r["狀態"] == "卡住"]
    if blocked:
        print("\n卡住的項目：")
        for r in blocked:
            print(f"  {r['ID']} {r['內容']} — {r['備註']}")
    waiting = [r for r in rows if r["狀態"] == "待審"]
    if waiting:
        print("\n待你審的項目：", ", ".join(r["ID"] for r in waiting))

    ic = Counter(i["狀態"] for i in issues)
    print(f"\n問題紀錄：共 {len(issues)} 筆　" + "　".join(f"{st} {ic.get(st, 0)}" for st in ISSUE_STATUSES))
    for i in issues:
        if i["狀態"] not in ISSUE_STATUSES:
            problems.append(f"問題 {i['ID']}: 狀態「{i['狀態']}」不在 {ISSUE_STATUSES}")
        if i["影響方法"] == "是" and i["狀態"] not in ("需負責人決定", "已排除"):
            problems.append(f"問題 {i['ID']}: 影響方法＝是，但狀態不是「需負責人決定」")
        if i["狀態"] in ("待處理", "已知") and not i["暫行處理"]:
            problems.append(f"問題 {i['ID']}: 沒有暫行處理")
    need = [i for i in issues if i["狀態"] == "需負責人決定"]
    if need:
        print("\n需要你決定的問題（影響方法）：")
        for i in need:
            print(f"  {i['ID']} {i['現象']} — 暫行處理：{i['暫行處理'] or '（無）'}")
    todo = [i for i in issues if i["狀態"] == "待處理"]
    if todo:
        print("\n新發現、尚待處理的問題：", ", ".join(i["ID"] for i in todo))

    if problems:
        print("\n需要處理的問題：")
        for p in problems:
            print("  -", p)
    else:
        print("\n進度表沒有發現不合規的列。")

    if a.run_tests:
        print("\n執行後端測試…")
        r = subprocess.run([sys.executable, "-m", "pytest", "-s", "-q"], cwd=REPO / "backend")
        if r.returncode != 0:
            problems.append("後端測試未全部通過")

    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
