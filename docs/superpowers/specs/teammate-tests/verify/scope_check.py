# -*- coding: utf-8 -*-
"""範圍與品質檢查（負責人用）：檢查某個任務的改動有沒有超出範圍、有沒有動到受保護檔案、
有沒有削弱既有測試、有沒有常見的「讓測試過關」的壞味道。唯讀。

用法（在 repo 根目錄）：
    python docs/superpowers/specs/teammate-tests/verify/scope_check.py --task A1 [--base main]
    python docs/superpowers/specs/teammate-tests/verify/scope_check.py --task A1 --files a.py b.py   # 指定檔案清單（測試用）

「改動」＝ 與 --base 比較的所有差異（已提交、未提交、未追蹤的檔案）。
檢查項目：
  1. 範圍：只能改進度總表裡該任務「產出檔案」所列的檔案，加上 backend/tests/ 新增的 test_*.py 與指南的進度表；
  2. 受保護：驗收測試、基準檔、設計文件、檢查腳本一律不可改；指南 0.4「方法凍結」那一段不可改；
  3. 其他任務的進度列不可被改動（例如把別人的任務標成完成）；
  4. 既有測試不可被刪改（已存在的 backend/tests/test_*.py 有被刪除的行就視為違規）；
  5. 壞味道（新增的行）：高風險＝skip/xfail、assert True、NotImplementedError、寫死的基準雜湊；注意＝except: pass（清理程式也常見，需人工確認）、shell=True、TODO。
結束碼：有違規或高風險壞味道為 1。
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))
import progress_check as pc            # noqa: E402

GUIDE_REL = "docs/superpowers/specs/teammate-guide.md"
PROTECTED = [
    "docs/superpowers/specs/teammate-tests/verify/",
    "docs/superpowers/specs/baseline_assess.json",
    "docs/superpowers/specs/2026-10-10-ai-pool-bootstrapping-design.md",
    "docs/superpowers/specs/teammate-tests/progress_check.py",
    "docs/superpowers/specs/teammate-tests/baseline_assess.py",
]
SMELLS = [  # (regex, 說明, 嚴重度, 只看測試檔?)
    (r"pytest\.mark\.(skip|xfail|skipif)", "新增 skip／xfail（測試被關掉）", "HIGH", True),
    (r"^\+?\s*except[^:\n]*:\s*(pass|\.\.\.)\s*$", "吞掉例外（except: pass；請確認不是在掩蓋錯誤）", "MED", False),
    (r"\bassert\s+True\b", "assert True（沒有檢查任何東西）", "HIGH", False),
    (r"raise\s+NotImplementedError", "NotImplementedError（空殼）", "HIGH", False),
    (r"shell\s*=\s*True|os\.system\(", "shell=True／os.system", "MED", False),
    (r"\b(TODO|FIXME|XXX)\b", "TODO／FIXME", "MED", False),
]


def git(*args, check=False):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout


def changed_files(base):
    names = set()
    for cmd in (["diff", "--name-only", base], ["ls-files", "--others", "--exclude-standard"]):
        names |= {ln.strip() for ln in git(*cmd).splitlines() if ln.strip()}
    return sorted(names)


def exists_at_base(path, base):
    return subprocess.run(["git", "cat-file", "-e", f"{base}:{path}"], cwd=REPO, capture_output=True).returncode == 0


def added_lines(path, base):
    """回傳 [(行號, 內容)]：與 base 比較新增的行；未追蹤的新檔案則整個檔案。"""
    full = REPO / path
    if not full.exists() or full.suffix != ".py":
        return []
    if not exists_at_base(path, base):
        return [(i + 1, ln) for i, ln in enumerate(full.read_text(encoding="utf-8", errors="replace").splitlines())]
    out, cur = [], 0
    for ln in git("diff", "-U0", base, "--", path).splitlines():
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", ln)
        if m:
            cur = int(m.group(1)) - 1
        elif ln.startswith("+") and not ln.startswith("+++"):
            cur += 1
            out.append((cur, ln[1:]))
        elif not ln.startswith("-"):
            cur += 1
    return out


def removed_count(path, base):
    for ln in git("diff", "--numstat", base, "--", path).splitlines():
        parts = ln.split("\t")
        if len(parts) == 3 and parts[1].isdigit():
            return int(parts[1])
    return 0


def baseline_tokens():
    p = REPO / "docs/superpowers/specs/baseline_assess.json"
    toks = set()
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        for prob in d["problems"].values():
            for pool in prob["fingerprints"].values():
                toks |= {fp["sha256_16"] for fp in pool.values()}
    return toks


def section(text, start, end):
    i = text.find(start)
    j = text.find(end, i + 1)
    return text[i:j] if i >= 0 and j >= 0 else ""


def run(task, base, files=None):
    findings = {"violations": [], "high": [], "med": []}
    guide_text = (REPO / GUIDE_REL).read_text(encoding="utf-8")
    board = {r["ID"]: r for r in pc.parse_board(guide_text)}
    if task not in board:
        raise SystemExit(f"進度總表沒有任務 {task}")
    allowed = [f.strip().strip("`") for f in board[task]["產出檔案"].split(",") if f.strip()]
    files = files if files is not None else changed_files(base)

    for f in files:
        if any(f == p or (p.endswith("/") and f.startswith(p)) for p in PROTECTED):
            findings["violations"].append(f"改動了受保護的檔案：{f}")
            continue
        if f == GUIDE_REL:
            continue
        ok = any(f == a or (a.endswith("/") and f.startswith(a)) for a in allowed)
        new_test = f.startswith("backend/tests/") and Path(f).name.startswith("test_") and not exists_at_base(f, base)
        if not ok and not new_test:
            findings["violations"].append(f"超出任務 {task} 範圍的檔案：{f}（允許：{allowed or '尚未列出'}）")

    # 既有測試被刪改
    for f in files:
        if f.startswith("backend/tests/") and exists_at_base(f, base) and removed_count(f, base) > 0:
            findings["violations"].append(f"既有測試被刪改：{f}（刪除 {removed_count(f, base)} 行）")

    # 指南：0.4 方法凍結不可改；其他任務的列不可改
    if GUIDE_REL in files and exists_at_base(GUIDE_REL, base):
        old_text = git("show", f"{base}:{GUIDE_REL}")
        if section(old_text, "### 0.4", "### 0.5") != section(guide_text, "### 0.4", "### 0.5"):
            findings["violations"].append("指南第 0.4 節（方法凍結）被修改")
        old_board = {r["ID"]: r for r in pc.parse_board(old_text)}
        for rid, row in board.items():
            if rid != task and old_board.get(rid) != row:
                findings["violations"].append(f"改動了其他任務的進度列：{rid}")

    # 壞味道
    tokens = baseline_tokens()
    for f in files:
        is_test = f.startswith("backend/tests/") or Path(f).name.startswith("test_")
        lines = added_lines(f, base)
        # 跨行的「except ...:」下一行只有 pass／...（吞掉例外）
        for (n1, t1), (n2, t2) in zip(lines, lines[1:]):
            if n2 == n1 + 1 and re.match(r"\s*except\b[^:\n]*:\s*$", t1) and t2.strip() in ("pass", "..."):
                findings["med"].append(f"{f}:{n1} 吞掉例外（except 後只有 {t2.strip()}；請確認不是在掩蓋錯誤）")
        for lineno, text in lines:
            for pat, label, sev, test_only in SMELLS:
                if test_only and not is_test:
                    continue
                if re.search(pat, text):
                    findings["high" if sev == "HIGH" else "med"].append(f"{f}:{lineno} {label} → {text.strip()[:80]}")
            for t in tokens:
                if t in text:
                    findings["high"].append(f"{f}:{lineno} 出現基準資料的雜湊（疑似寫死）→ {t}")
    return findings, files, allowed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--base", default="main")
    ap.add_argument("--files", nargs="*", default=None)
    a = ap.parse_args()
    try:
        git("rev-parse", "--verify", a.base, check=True)
    except RuntimeError:
        print(f"找不到 base「{a.base}」；請用 --base 指定（例如 origin/main）")
        sys.exit(2)
    findings, files, allowed = run(a.task, a.base, a.files)
    print(f"任務 {a.task}｜base={a.base}｜改動檔案 {len(files)} 個｜允許：{allowed or '（尚未列出）'}")
    for key, title in (("violations", "違規"), ("high", "高風險壞味道"), ("med", "注意")):
        if findings[key]:
            print(f"\n{title}（{len(findings[key])}）：")
            for x in findings[key]:
                print("  -", x)
    bad = findings["violations"] or findings["high"]
    print("\n結果：", "不通過" if bad else "通過（沒有違規或高風險壞味道）")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
