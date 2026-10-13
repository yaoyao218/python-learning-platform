# -*- coding: utf-8 -*-
"""虛擬碼往返檢查（給組員測試用）。對應設計文件 2026-10-10-ai-pool-bootstrapping-design.md 第十四、十七、十八節。

做什麼：
  1. 以題庫中既有的 S+ 當來源，請「寫手」模型寫虛擬碼；
  2. 請「實作者」模型獨立 k 次，只看題目與虛擬碼（看不到任何 S+），各自寫成程式；
  3. 在子程序中執行這些程式（絕不在主程序 exec），與來源 S+ 在探測輸入上比對答案。

執行（在 repo 根目錄）：
    cd backend
    python ../docs/superpowers/specs/teammate-tests/pseudocode_roundtrip.py --problem longest-substring

前置：
  - backend/.env 內要有 GROQ_API_KEY（不要把金鑰貼到任何文件或對話）。
  - pip install openai python-dotenv
注意：
  - 這是實驗腳本，不會修改 repo 內任何檔案；結果只寫到 --out 指定的 JSON（預設在本腳本旁邊）。
  - AI 寫的程式在子程序執行，只有既有的 import 黑名單，沒有記憶體或 CPU 限制（見設計文件第九節）。
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[3] / "backend"          # docs/superpowers/specs/teammate-tests -> repo root
sys.path.insert(0, str(BACKEND))

from problem import PROBLEMS                    # noqa: E402
from executor import check_forbidden            # noqa: E402
from testgen import registry                    # noqa: E402

# 子程序內執行：讀 stdin 的 {code, method, inputs}，逐一呼叫，單筆例外記為 "__ERR__"
CHILD = r'''
import json, sys
d = json.loads(sys.stdin.read())
ns = {}
exec(d["code"], ns)
f = getattr(ns["Solution"](), d["method"])
out = []
for a in d["inputs"]:
    try:
        out.append(f(*[list(x) if isinstance(x, list) else x for x in a]))
    except Exception:
        out.append("__ERR__")
sys.stdout.write(json.dumps(out, default=repr))
'''

# 硬規則：違反就視為格式不合格，直接重寫（不進實作）
HARD_PATTERNS = [(r"```", "含程式碼區塊"), (r"def", "含 def"), (r"class", "含 class"), (r"import", "含 import")]
# 軟規則：預設只記錄為警告；加 --strict-format 時才當硬規則
SOFT_PATTERNS = [(r"range\(|len\(|self", "含程式語法"), (r":\s*$", "有以冒號結尾的行"),
                 (r"\w\[[^\]]+\]", "含索引寫法 x[i]")]   # 第十七節建議補強；實測寫手常不遵守，故預設為警告
MAX_STEPS = 15


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--problem", default="longest-substring", choices=list(registry.TESTGEN_PROBLEMS))
    p.add_argument("--source", default=None, help="來源 S+ 檔名（不含 .py）；預設用 registry 的參考解")
    p.add_argument("--writer", default="openai/gpt-oss-20b")
    p.add_argument("--impl", default="openai/gpt-oss-120b")
    p.add_argument("--k", type=int, default=3, help="獨立實作次數")
    p.add_argument("--tries", type=int, default=3, help="虛擬碼最多重寫幾次")
    p.add_argument("--n-random", type=int, default=2000)
    p.add_argument("--effort", default="low", help="reasoning_effort（gpt-oss 可用 low/medium/high）")
    p.add_argument("--strict-format", action="store_true", help="軟規則（索引寫法、len( 等）也當格式不合格而重寫")
    p.add_argument("--out", default=None)
    return p.parse_args()


def make_client():
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv(BACKEND / ".env")
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise SystemExit("backend/.env 沒有 GROQ_API_KEY")
    return OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")


def chat(client, model, prompt, effort, max_tokens=3000):
    for _ in range(4):
        try:
            r = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], temperature=0.5,
                                               max_completion_tokens=max_tokens, reasoning_effort=effort)
            return (r.choices[0].message.content or ""), (r.usage.total_tokens if r.usage else None)
        except Exception as e:  # noqa: BLE001
            print("   (API 錯誤", type(e).__name__, str(e)[:100], "，10 秒後重試)", flush=True)
            time.sleep(10)
    return "", None


def run_batch(method, code, inputs, timeout=60):
    try:
        r = subprocess.run([sys.executable, "-c", CHILD],
                           input=json.dumps({"code": code, "method": method, "inputs": [list(a) for a in inputs]}),
                           capture_output=True, text=True, timeout=timeout, encoding="utf-8")
    except subprocess.TimeoutExpired:
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def case_args(tc):
    return tuple(tc["args"]) if "args" in tc else (tc["input"],)


def check_pseudo(text, strict=False):
    """回傳 (硬性問題, 警告, 步驟數)。strict=True 時軟規則也算硬性問題。"""
    probs = [msg for pat, msg in HARD_PATTERNS if re.search(pat, text, re.M)]
    warns = [msg for pat, msg in SOFT_PATTERNS if re.search(pat, text, re.M)]
    steps = sum(1 for ln in text.splitlines() if re.match(r"\s*\d+[\.\)、]", ln))
    if steps == 0:
        probs.append("沒有編號步驟")
    if steps > MAX_STEPS:
        probs.append(f"步驟過多（{steps}）")
    if strict:
        probs, warns = probs + warns, []
    return probs, warns, steps


def main():
    a = parse_args()
    pid = a.problem
    prob = PROBLEMS[pid]
    method = prob["method"]
    client = make_client()

    desc = re.sub(r"<[^>]+>", "", prob["description"])
    cons = "\n".join("- " + c for c in prob["constraints"])
    examples = "\n".join(f'- 輸入 {e["input"]} → 輸出 {e["output"]}' for e in prob["examples"])
    starter = prob["starter_code"].split("# 在此")[0].rstrip() + "\n        ..."

    spec = registry.load_spec(pid)
    rng = random.Random(0)
    official_cases = [tc for tc in prob["test_cases"] if not tc.get("is_stress")][:3]
    official = [case_args(tc) for tc in official_cases]
    inputs = official + [spec.random_args(rng) for _ in range(a.n_random)] + list(spec.small_args())

    src_name = a.source or Path(registry.TESTGEN_PROBLEMS[pid]["reference"]).stem
    src_path = registry.pool_dir(pid, "correct") / f"{src_name}.py"
    src = src_path.read_text(encoding="utf-8")
    truth = run_batch(method, src, inputs)
    if truth is None:
        raise SystemExit("來源 S+ 執行失敗，請檢查")
    off_ok = all(str(truth[i]) == str(official_cases[i]["expected"]) for i in range(len(official)))
    print(f"題目 {pid}｜來源 S+ {src_path.name}｜探測輸入 {len(inputs)} 組｜來源通過官方範例：{off_ok}", flush=True)

    report = {"date": datetime.now().isoformat(timespec="seconds"), "problem": pid, "source": src_path.name,
              "writer": a.writer, "implementer": a.impl, "k": a.k, "effort": a.effort, "n_inputs": len(inputs),
              "source_passes_official": off_ok, "attempts": []}
    for attempt in range(1, a.tries + 1):
        wprompt = f"""以下是題目「{prob['title']}」的一份正確 Python 解法。請依它寫出『虛擬碼』，給具備基本程式能力的人閱讀。

要求：
- 先用一兩行說明輸入與輸出。
- 之後用編號步驟（1. 2. 3. …，最多 {MAX_STEPS} 步），每步一句話，用變數、條件、更新、回傳描述。
- 不要使用任何程式語言的語法（不要出現 def、class、import、range(、len(，不要用 x[i] 的索引寫法，也不要用程式碼區塊或以冒號結尾的行）。
- 語氣一致，不要重複描述同一件事。
- 不要寫解釋或複雜度分析，只輸出虛擬碼。

```python
{src}
```"""
        pseudo, wtok = chat(client, a.writer, wprompt, a.effort)
        probs, warns, steps = check_pseudo(pseudo, a.strict_format)
        rec = {"attempt": attempt, "steps": steps, "format_problems": probs, "format_warnings": warns, "writer_tokens": wtok,
               "pseudocode": pseudo, "impls": []}
        print(f"\n== 第 {attempt} 次虛擬碼（{steps} 步｜格式問題：{probs or '無'}｜警告：{warns or '無'}）==\n{pseudo}\n", flush=True)
        if probs:
            report["attempts"].append(rec)
            continue
        for k in range(1, a.k + 1):
            iprompt = f"""請把下面的虛擬碼寫成 Python 程式。嚴格依照虛擬碼的步驟實作，不要自行改進、不要換成別的演算法。

## 題目：{prob['title']}
{desc}
限制：
{cons}
官方範例：
{examples}

## 虛擬碼
{pseudo}

## 格式
只輸出完整程式碼（不要解釋），格式為：
{starter}"""
            out, itok = chat(client, a.impl, iprompt, a.effort)
            m = re.search(r"```(?:python)?\s*(.*?)```", out, re.S)
            code = m.group(1) if m else out
            item = {"k": k, "tokens": itok}
            forbidden = check_forbidden(code)
            if forbidden:
                item["result"] = f"forbidden: {forbidden}"
            else:
                res = run_batch(method, code, inputs)
                if res is None:
                    item["result"] = "timeout/crash"
                else:
                    diff = [i for i in range(len(inputs)) if str(res[i]) != str(truth[i])]
                    item["n_diff"] = len(diff)
                    item["result"] = "一致" if not diff else f"不一致（{len(diff)} 組輸入）"
                    if diff:
                        item["first_diff"] = [(list(inputs[i]), truth[i], res[i]) for i in diff[:3]]
            rec["impls"].append(item)
            print(f"  實作 {k}: {item['result']}｜tokens={itok}", flush=True)
        rec["passed"] = all(i.get("result") == "一致" for i in rec["impls"])
        report["attempts"].append(rec)
        if rec["passed"]:
            break

    report["final_passed"] = any(x.get("passed") for x in report["attempts"])
    out_path = Path(a.out) if a.out else HERE / f"result_{pid}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n最終：", "通過" if report["final_passed"] else "未通過", "｜虛擬碼嘗試次數", len(report["attempts"]), "｜結果檔", out_path)


if __name__ == "__main__":
    main()
