# -*- coding: utf-8 -*-
"""負責人一鍵驗收：對進度總表中狀態為「待審」「完成」的任務（或用 --task 指定的任務）做三件事：
  1. 範圍與壞味道檢查（scope_check）；
  2. 自動驗收測試（有的任務才有，見 ACCEPTANCE）；
  3. 既有後端測試不得退步（passed 不少於起點、沒有 failed、skipped 不增加）。
沒有自動驗收的任務會明確標示「需人工審」，並列出你該看的重點。

用法（在 repo 根目錄）：
    python docs/superpowers/specs/teammate-tests/verify/verify_all.py
    python docs/superpowers/specs/teammate-tests/verify/verify_all.py --task A1 --base origin/main
    python docs/superpowers/specs/teammate-tests/verify/verify_all.py --seed 12345   # 固定驗收用的隨機種子

提示：不加 --seed 時，每次的隨機輸入都不同；失敗時會印出種子，可用同一個種子重現。
重要：驗收時請用你自己的環境與你自己的 checkout；不要用組員提供的結果檔或截圖當作依據。
"""
import argparse
import os
import random
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import progress_check as pc            # noqa: E402
import scope_check as sc               # noqa: E402

BASE_PASSED, BASE_SKIPPED = 43, 8       # 2026-10-10 起點：43 passed, 8 skipped
ACCEPTANCE = {
    "A1": "test_acceptance_a1_safe_batch.py",
    "A2": "test_acceptance_a2_strict_check.py",
}
MANUAL_HINTS = {
    "A3": "確認 assess_problem 的 --isolated 對人工池的結果與一般模式相同；AI 池不會走 exec；pool_meta.json 欄位齊全。",
    "A4": "確認天花板由檢查關算出並寫入；沒有手動填寫的收斂旗標；不改變既有題目的登記值。",
    "B1": "用模擬的壞格式、429、空回應各跑一次，確認不崩潰且有分類記錄；確認一次只請 AI 寫一份程式、沒有使用 JSON 模式。",
    "B2": "重跑 T1（5 次），確認虛擬碼與實作沒有看到 S+；格式警告只記錄不退回。",
    "B3": "確認淘汰只用與測資無關的指標；驗收批不出現在任何提案或審核提示；參數可設定且預設值等於設計文件。",
    "B4": "確認審核紀錄含審核者、依據、是否測試階段。",
    "B5": "確認驗收批用模型 B 產生，且迭代期間沒有被讀取。",
    "B6": "確認輸入規格的 validate／random_args／small_args 通過一致性檢查。",
    "C1": "確認 build_prompt 仍沒有學生程式碼參數；hint_guard 對虛擬碼與整段複述的行為；既有 test_ai 全過。",
    "C2": "沒有虛擬碼的題目外觀不變；API 兩種情況都有測試；測資內容沒有送到前端。",
    "C3": "照 user-facing-draft.md 的檢查清單逐項確認，並找一位沒參與開發的人走一遍。",
    "C4": "確認預設不記錄程式碼；開啟前需有同意；只做離線比對，沒有自動提示。",
    "D1": "確認只改文字、沒有改數據；每個新說法都有出處。",
    "T": "核對結果 JSON 的日期與參數；自己抽跑一次。",
}


def run_pytest(args, env_extra=None, cwd=None):
    env = dict(os.environ, PYTHONUTF8="1", **(env_extra or {}))
    r = subprocess.run([sys.executable, "-m", "pytest", *args], cwd=cwd or REPO, capture_output=True, text=True,
                       encoding="utf-8", env=env)
    return r.returncode, r.stdout + r.stderr


def parse_counts(out):
    def n(word):
        m = re.search(rf"(\d+) {word}", out)
        return int(m.group(1)) if m else 0
    return n("passed"), n("failed"), n("skipped"), n("error")


def acceptance_tampered(filename, base):
    """驗收測試檔（或共用工具）與 base 不同，代表可能被改過；此時自動驗收的結果不可信。"""
    rels = [f"docs/superpowers/specs/teammate-tests/verify/{filename}", "docs/superpowers/specs/teammate-tests/verify/_support.py"]
    for rel in rels:
        r = subprocess.run(["git", "diff", "--quiet", base, "--", rel], cwd=REPO)
        if r.returncode != 0:
            return True
        u = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "--", rel], cwd=REPO, capture_output=True, text=True)
        if u.stdout.strip():
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", action="append", help="指定任務（可重複）；預設為進度表中「待審」「完成」的任務")
    ap.add_argument("--base", default="main")
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()
    seed = a.seed if a.seed is not None else random.randint(1, 999_999)

    board = pc.parse_board(pc.GUIDE.read_text(encoding="utf-8"))
    tasks = a.task or [r["ID"] for r in board if r["狀態"] in ("待審", "完成")]
    print(f"驗收種子：{seed}（固定種子可重現）")
    print(f"驗收任務：{tasks or '（沒有待審或完成的任務）'}\n")
    rows, any_fail = [], False

    # 1. 既有測試不得退步
    code, out = run_pytest(["-s", "-q"], cwd=REPO / "backend")
    p, f, s, e = parse_counts(out)
    base_ok = f == 0 and e == 0 and p >= BASE_PASSED and s <= BASE_SKIPPED
    print(f"既有後端測試：{p} passed, {f} failed, {s} skipped, {e} error（起點 {BASE_PASSED} passed／{BASE_SKIPPED} skipped）→ {'通過' if base_ok else '不通過'}")
    any_fail |= not base_ok

    # 2. 逐任務
    for t in tasks:
        row = next((r for r in board if r["ID"] == t), None)
        if row is None:
            rows.append((t, "?", "找不到任務", "-", "-"))
            any_fail = True
            continue
        try:
            findings, files, allowed = sc.run(t, a.base)
            scope = "通過" if not (findings["violations"] or findings["high"]) else "不通過"
            detail = findings["violations"][:3] + findings["high"][:3]
        except SystemExit as ex:
            scope, detail = f"無法檢查（{ex}）", []
        if t in ACCEPTANCE and acceptance_tampered(ACCEPTANCE[t], a.base):
            acc, acc_ok, out = "驗收檔被改動（結果不可信）", False, ""
        elif t in ACCEPTANCE:
            code, out = run_pytest([str(HERE / ACCEPTANCE[t]), "-s", "-q", "-p", "no:cacheprovider"],
                                   env_extra={"VERIFY_SEED": str(seed)})
            p2, f2, s2, e2 = parse_counts(out)
            acc = f"{p2} passed／{f2 + e2} 未過" + ("" if code == 0 else "（不通過）")
            acc_ok = code == 0
        else:
            acc, acc_ok = "需人工審", True
        evidence = "有" if row["證據"] else "缺"
        ok = scope == "通過" and acc_ok and (row["狀態"] != "完成" or row["證據"])
        any_fail |= not ok
        rows.append((t, row["狀態"], scope, acc, evidence))
        if detail:
            print(f"\n[{t}] 範圍檢查的問題：")
            for d in detail:
                print("  -", d)
        if t in MANUAL_HINTS and t not in ACCEPTANCE:
            print(f"\n[{t}] 你需要人工看的重點：{MANUAL_HINTS[t]}")
        if t in ACCEPTANCE and not acc_ok:
            tail = "\n".join(out.splitlines()[-12:])
            print(f"\n[{t}] 自動驗收輸出（末段）：\n{tail}")

    print("\n任務 | 狀態 | 範圍檢查 | 自動驗收 | 證據欄")
    for r in rows:
        print(" | ".join(r))
    print("\n總結：", "不通過" if any_fail else "通過")
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
