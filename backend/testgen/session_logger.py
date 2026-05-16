"""session_logger.py — 把每次 /submit 完整 trace 寫進 JSONL。

設計：
  * 一筆一行 JSON，append-only（不會被讀寫衝突）
  * 預設關閉，TESTGEN_SESSION_LOG=1 才啟用
  * Log 路徑可由 TESTGEN_LOG_PATH 設定，預設 backend/testgen/sessions/<date>.jsonl
  * 每筆紀錄含：時間戳、學生程式碼、執行結果（每筆 case）、AI prompt、AI 回應、總耗時
  * 跟 main.py 解耦——只攔 /submit 的 response，原本流程完全不動

啟用方式：
    TESTGEN_SESSION_LOG=1 uvicorn main:app --reload --port 8000
"""
from __future__ import annotations
import asyncio
import datetime as dt
import json
import os
import time
from pathlib import Path
from typing import Any

LOG_ENABLED = os.environ.get("TESTGEN_SESSION_LOG", "0") == "1"


def _default_log_path() -> Path:
    base = Path(__file__).resolve().parent / "sessions"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{dt.date.today().isoformat()}.jsonl"


LOG_PATH = Path(os.environ.get("TESTGEN_LOG_PATH") or _default_log_path())


def _serialize(obj: Any):
    """把無法直接 JSON 化的物件（如 datetime）轉成可序列化形態。"""
    if isinstance(obj, dt.datetime):
        return obj.isoformat()
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        return repr(obj)


_lock = asyncio.Lock()


async def append_record(record: dict):
    """非阻塞 append 一筆紀錄。多 worker 安全（用 asyncio.Lock）。"""
    if not LOG_ENABLED:
        return
    payload = {k: _serialize(v) for k, v in record.items()}
    line = json.dumps(payload, ensure_ascii=False)
    async with _lock:
        # 用 thread 寫檔避免阻塞 event loop
        await asyncio.to_thread(_append_line, line)


def _append_line(line: str):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


async def log_submission(code: str, results: list[dict], hint: str | None,
                         ai_prompt: str | None = None,
                         elapsed_ms: float | None = None):
    """便利包裝：在 main.py 的 /submit handler 結尾呼叫即可。"""
    fails = [r for r in results if not r.get("passed")]
    first_fail = fails[0] if fails else None
    error_type = first_fail.get("error_type") if first_fail else None
    record = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "elapsed_ms": elapsed_ms,
        "code_len": len(code),
        "code": code,
        "n_test_cases": len(results),
        "n_pass": sum(1 for r in results if r.get("passed")),
        "n_fail": len(fails),
        "first_fail_index": first_fail.get("index") if first_fail else None,
        "first_fail_input": first_fail.get("input") if first_fail else None,
        "first_fail_expected": first_fail.get("expected") if first_fail else None,
        "first_fail_actual": first_fail.get("actual") if first_fail else None,
        "first_fail_error_type": error_type,
        "ai_prompt": ai_prompt,
        "ai_hint": hint,
        "results": results,
    }
    await append_record(record)
