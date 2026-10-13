#!/usr/bin/env python3
"""propose.py — AI 提案器：請 LLM 針對 S- 訓練池提出候選測資（實驗計畫 Phase 2）。

給 AI 的資訊：
  * 題目敘述（ai_context）、函式簽名（starter_code）、constraints
  * 參考正解 S* 的原始碼
  * S- 訓練池每個錯誤的「一行描述」（檔頭註解）——不給 S- 原始碼，也完全不提驗收池
  * 上一輪正式測資，以及每個 S- 目前的通過率、被哪幾筆抓到（結構化數字）
  * 第 2 輪起：上一輪每筆候選的評測結果與人工裁決（結構化，不含自由敘述）

規則：
  * AI 只提供輸入，不提供 expected；回傳裡若有 expected 一律丟掉並記錄次數
  * 每筆候選先過 spec.validate，不合法的記入 rejected（validator 擋掉率是 AI 品質指標之一）
  * 同一輪的提案預設不能覆寫；用 --force 重新提案時，舊檔改名保留，避免「抽到滿意為止」

執行：
    cd backend
    python -m testgen.propose --problem longest-valid-parentheses --round 1 --dry-run   # 只印 prompt
    python -m testgen.propose --problem longest-valid-parentheses --round 1
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from problem import PROBLEMS        # noqa: E402
from testgen import registry        # noqa: E402
from testgen import rounds          # noqa: E402

DEFAULT_MODEL = "openai/gpt-oss-120b"
PROVIDERS = {
    "groq": {"base_url": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "key_env": "GEMINI_API_KEY"},
}
_DISPLAY_MAX = 60

SYSTEM_PROMPT = """你是協助設計程式題測資的助理。目標是提出「能讓特定初學者錯誤寫法答錯、但正確寫法一定答對」的測試輸入。
規則：
1. 只提供輸入，不要提供預期輸出（預期輸出會由參考正解計算）。
2. 輸入必須完全符合題目限制。
3. 優先提出短小、人類一眼看得懂的輸入（長度盡量 ≤ 20），方便學生看到失敗時理解。
4. 一筆輸入可以同時抓到多種錯誤；target_bug 填你最主要鎖定的那一個。
5. 不要重複目前已有的測資。
6. 只回覆一個 JSON 物件，不要有其他文字。"""

# v2：把目標明講成「一筆輸入同時抓到的錯誤種類數」。v1 的 target_bug 設計傾向每筆只鎖定一種錯誤，
# 試跑第 2 輪時單筆最多只抓到 4/6（見 rounds/ 下的紀錄）。v1 保留，供重現。
SYSTEM_PROMPT_V2 = """你是協助設計程式題測資的助理。目標是提出「能同時讓盡量多種初學者錯誤寫法答錯、但正確寫法一定答對」的測試輸入。
評分方式：每筆輸入會拿去測全部的錯誤寫法，看它讓幾種錯誤答錯。一筆輸入讓越多種錯誤答錯越好；只針對單一種錯誤的輸入價值低。
規則：
1. 只提供輸入，不要提供預期輸出（預期輸出會由參考正解計算）。
2. 輸入必須完全符合題目限制。
3. 輸入長度盡量 ≤ 20，讓學生看到失敗時能看懂。
4. target_bug 填這筆輸入最難抓、目前通過率最高的那一種錯誤；但整筆輸入的目標是同時抓到盡量多種。
5. 不要重複目前已有的測資，也不要重複先前被丟棄的測資。
6. 只回覆一個 JSON 物件，不要有其他文字。"""

SYSTEM_PROMPTS = {"v1": SYSTEM_PROMPT, "v2": SYSTEM_PROMPT_V2}


def bug_descriptions(problem_id: str) -> dict[str, str]:
    out = {}
    for path in sorted(registry.pool_dir(problem_id, "wrong").glob("*.py")):
        first = path.read_text(encoding="utf-8").splitlines()[0]
        desc = first.lstrip("# ").strip()
        out[path.stem] = desc.removeprefix("錯誤：")
    return out


def show_args(args: tuple) -> str:
    s = ", ".join(repr(a) for a in args)
    return s if len(s) <= _DISPLAY_MAX else s[:_DISPLAY_MAX] + f"...（共 {len(s)} 字元）"


def previous_round_record(problem_id: str, n: int, with_count: bool = False) -> list[dict] | None:
    """第 n 輪（n ≥ 1）每筆候選的評測與人工裁決，結構化。with_count：另附抓到的錯誤種類數（v2）。"""
    review_path = rounds.round_path(problem_id, n, "review")
    if not review_path.exists():
        raise SystemExit(f"找不到 {review_path.relative_to(BACKEND)}：第 {n} 輪還沒審核完，不能提第 {n + 1} 輪")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    out = []
    for item in review["items"]:
        rec = {
            "input": show_args(tuple(item["args"])),
            "target_bug": item.get("target_bug"),
            "caught": item.get("kills", []),
            "decision": item.get("decision"),
        }
        if with_count:
            rec["n_caught"] = len(rec["caught"])
        out.append(rec)
    return out


def build_messages(problem_id: str, n: int, n_candidates: int, version: str = "v2") -> list[dict]:
    prob = PROBLEMS[problem_id]
    prev = rounds.load_round_tests(problem_id, n - 1)
    ev = prev["evaluation"]
    bugs = bug_descriptions(problem_id)
    ref_code = registry.reference_path(problem_id).read_text(encoding="utf-8")

    lines = [
        f"# 題目：{prob['title']}",
        prob["ai_context"],
        "",
        "## 函式簽名",
        "```python", prob["starter_code"].rstrip(), "```",
        "",
        "## 限制",
        *[f"- {c}" for c in prob["constraints"]],
        "",
        "## 參考正解",
        "```python", ref_code.rstrip(), "```",
        "",
        "## 要抓的錯誤寫法（target_bug 必須是下列名稱之一）",
        *[f"- {name}：{desc}" for name, desc in bugs.items()],
        "",
        f"## 目前的正式測資（第 {n - 1} 輪結束時，共 {len(prev['cases'])} 筆）",
        *[f"- #{c['index']}：{show_args(c['args'] if 'args' in c else (c['input'],))}" for c in prev["cases"]],
        "",
        "## 每種錯誤目前的狀況（通過率越高 = 越難被抓到）",
        *[f"- {name}：通過率 {rate * 100:.0f}%，被測資 {ev['S_minus_caught_by'][name] or '（沒有任何一筆）'} 抓到"
          for name, rate in ev["S_minus_pass_rates"].items()],
    ]
    v2 = version == "v2"
    max_kills = 0
    if v2:
        total = len(ev["S_minus_caught_by"])
        per_case = {c["index"]: 0 for c in prev["cases"]}
        for idxs in ev["S_minus_caught_by"].values():
            for i in idxs:
                per_case[i] = per_case.get(i, 0) + 1
        max_kills = max(per_case.values(), default=0)
        lines += [
            "",
            "## 單筆輸入抓到幾種錯誤（越多越好）",
            *[f"- #{i}：抓到 {k}/{total} 種" for i, k in sorted(per_case.items())],
            f"目前正式測資中，單筆最多抓到 {max_kills}/{total} 種。",
        ]
    if n >= 2:
        record = previous_round_record(problem_id, n - 1, with_count=v2)
        lines += [
            "",
            f"## 第 {n - 1} 輪的候選與人工裁決",
            "caught 是實際評測抓到的錯誤；decision：keep=採用、drop=丟棄、edit=修改後採用。",
            "```json", json.dumps(record, ensure_ascii=False, indent=1), "```",
        ]
        if v2:
            lines.append(f"上一輪候選中，單筆最多抓到 {max((r['n_caught'] for r in record), default=0)}/{total} 種。")
    n_args = len(prev["cases"][0]["args"]) if prev["cases"] and "args" in prev["cases"][0] else 1
    ask = (f"提出 {n_candidates} 筆新的候選測資。目標是讓「單筆輸入同時抓到的錯誤種類數」盡量高，"
           f"至少要超過目前的 {max_kills} 種；只抓到一兩種的輸入價值低。格式："
           if v2 else f"提出 {n_candidates} 筆新的候選測資，優先鎖定通過率高、還沒被抓到的錯誤。格式：")
    lines += [
        "",
        "## 請回覆",
        ask,
        "```json",
        '{"candidates": [{"args": [<第 1 個參數>' + (", ..." if n_args > 1 else "") + '], '
        '"target_bug": "<錯誤名稱>", "rationale": "<一句話說明為什麼這筆會讓它答錯>"}]}',
        "```",
        f"args 是呼叫 {prob['method']} 時的位置參數列表（本題 {n_args} 個參數）。不要提供預期輸出。",
    ]
    return [{"role": "system", "content": SYSTEM_PROMPTS[version]},
            {"role": "user", "content": "\n".join(lines)}]


def call_model(provider: str, model: str, messages: list[dict], temperature: float,
               reasoning_effort: str | None) -> tuple[str, dict]:
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv(BACKEND / ".env")
    cfg = PROVIDERS[provider]
    key = os.environ.get(cfg["key_env"], "")
    if not key:
        raise SystemExit(f"backend/.env 沒有 {cfg['key_env']}")
    client = OpenAI(api_key=key, base_url=cfg["base_url"])
    kwargs = dict(model=model, messages=messages, temperature=temperature,
                  response_format={"type": "json_object"}, max_completion_tokens=8000)
    if reasoning_effort:
        kwargs["reasoning_effort"] = reasoning_effort
    resp = client.chat.completions.create(**kwargs)
    usage = resp.usage.model_dump() if resp.usage else {}
    return resp.choices[0].message.content or "", usage


def parse_candidates(problem_id: str, raw: str, n: int) -> tuple[list[dict], list[dict], dict]:
    """回傳 (accepted, rejected, stats)。"""
    spec = registry.load_spec(problem_id)
    bugs = set(bug_descriptions(problem_id))
    prev_cases = rounds.load_round_tests(problem_id, n - 1)["cases"]
    existing = {repr(c["args"] if "args" in c else (c["input"],)) for c in prev_cases}
    dropped = set()                      # 先前各輪被審核丟棄的輸入，不要再提
    for k in range(1, n):
        rp = rounds.round_path(problem_id, k, "review")
        if rp.exists():
            for it in json.loads(rp.read_text(encoding="utf-8"))["items"]:
                if it.get("decision") == "drop":
                    dropped.add(repr(tuple(it["args"])))

    stats = {"n_returned": 0, "dropped_expected_fields": 0, "unknown_target_bug": 0}
    try:
        items = json.loads(raw)["candidates"]
        assert isinstance(items, list)
    except Exception as e:
        return [], [{"reason": f"回覆不是預期的 JSON 格式：{type(e).__name__}", "raw": raw[:500]}], stats

    accepted, rejected, seen = [], [], set()
    stats["n_returned"] = len(items)
    for k, item in enumerate(items, 1):
        if not isinstance(item, dict) or not isinstance(item.get("args"), list):
            rejected.append({"item": item, "reason": "缺少 args 或 args 不是 list"})
            continue
        if any(key in item for key in ("expected", "output", "expected_output")):
            stats["dropped_expected_fields"] += 1
        args = tuple(item["args"])
        reason = spec.validate(args)
        key = repr(args)
        if reason:
            rejected.append({"item": item, "reason": f"不合法：{reason}"})
        elif key in existing:
            rejected.append({"item": item, "reason": "與目前正式測資重複"})
        elif key in dropped:
            rejected.append({"item": item, "reason": "與先前被丟棄的候選重複"})
        elif key in seen:
            rejected.append({"item": item, "reason": "與本輪其他候選重複"})
        else:
            seen.add(key)
            target = item.get("target_bug")
            if target not in bugs:
                stats["unknown_target_bug"] += 1
            accepted.append({
                "id": f"r{n}c{len(accepted) + 1}",
                "args": list(args),
                "target_bug": target if target in bugs else None,
                "target_bug_raw": target,
                "rationale": str(item.get("rationale", "")),
            })
    return accepted, rejected, stats


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--problem", required=True)
    p.add_argument("--round", type=int, required=True, help="第幾輪（≥ 1）")
    p.add_argument("--n", type=int, default=12, help="要求 AI 提出幾筆候選（預設 12）")
    p.add_argument("--provider", default="groq", choices=list(PROVIDERS))
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--reasoning-effort", default=None, choices=["low", "medium", "high"],
                   help="推理模型（如 gpt-oss）的推理強度；不給就用模型預設")
    p.add_argument("--prompt-version", default="v2", choices=list(SYSTEM_PROMPTS),
                   help="提示版本。v1=每筆鎖定一種錯誤；v2=目標是單筆輸入同時抓到的錯誤種類數（預設）")
    p.add_argument("--dry-run", action="store_true", help="只印出 prompt，不呼叫 API")
    p.add_argument("--force", action="store_true", help="這一輪已有提案時重新提案（舊檔改名保留）")
    p.add_argument("--pilot", action="store_true",
                   help="試跑：結果寫到 rounds/pilot/，不計入實驗（測試 API 與格式用）")
    args = p.parse_args()
    if args.round < 1:
        p.error("--round 必須 ≥ 1（第 0 輪用 rounds.py init 建立）")

    messages = build_messages(args.problem, args.round, args.n, args.prompt_version)
    if args.dry_run:
        for m in messages:
            print(f"----- {m['role']} -----\n{m['content']}\n")
        return

    out = rounds.round_path(args.problem, args.round, "candidates")
    if args.pilot:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = rounds.rounds_dir(args.problem) / "pilot" / f"r{args.round}_candidates.{stamp}.json"
    elif out.exists():
        if not args.force:
            raise SystemExit(f"{out.relative_to(BACKEND)} 已存在。同一輪重新提案要加 --force（舊檔會保留）")
        k = 1
        while (archived := out.with_name(f"{out.stem}.attempt{k}.json")).exists():
            k += 1
        out.rename(archived)
        print(f"[propose] 舊提案已保留為 {archived.name}")

    t0 = time.time()
    raw, usage = call_model(args.provider, args.model, messages, args.temperature, args.reasoning_effort)
    elapsed = round(time.time() - t0, 2)
    accepted, rejected, stats = parse_candidates(args.problem, raw, args.round)

    rounds.write_json(out, {
        "problem": args.problem,
        "round": args.round,
        "pilot": args.pilot,
        "meta": {
            "provider": args.provider, "model": args.model, "temperature": args.temperature,
            "reasoning_effort": args.reasoning_effort, "n_requested": args.n,
            "prompt_version": args.prompt_version,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "elapsed_sec": elapsed, "usage": usage,
        },
        "stats": {**stats, "n_accepted": len(accepted), "n_rejected": len(rejected)},
        "candidates": accepted,
        "rejected": rejected,
        "messages": messages,
        "raw_response": raw,
    })
    print(f"[propose] {args.model}：回傳 {stats['n_returned']} 筆，接受 {len(accepted)}、拒絕 {len(rejected)}"
          f"（{elapsed} 秒）")
    for r in rejected:
        print(f"  ✗ {r['reason']}：{json.dumps(r.get('item'), ensure_ascii=False)[:80]}")
    if stats["dropped_expected_fields"]:
        print(f"  ⚠ 有 {stats['dropped_expected_fields']} 筆附了預期輸出，已忽略")
    if stats["unknown_target_bug"]:
        print(f"  ⚠ 有 {stats['unknown_target_bug']} 筆的 target_bug 不在 S- 清單裡（保留輸入，target 記為 None）")
    print(f"已寫入 {out.relative_to(BACKEND)}（AI 理由存在檔案裡，審核前不要先看）")


if __name__ == "__main__":
    main()
