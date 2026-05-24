import asyncio
import sys
import time

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from judge import judge
from ai import get_hint, build_prompt, evaluate_selection

# 可選 session logger：TESTGEN_SESSION_LOG=1 才啟用，預設不影響線上行為
try:
    from testgen.session_logger import log_submission, LOG_ENABLED
except ImportError:
    LOG_ENABLED = False
    async def log_submission(*args, **kwargs): pass

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+|https://.*\.vercel\.app",
    allow_methods=["POST"],
    allow_headers=["*"],
)


class SubmitRequest(BaseModel):
    code: str


class HintRequest(BaseModel):
    code: str
    results: list[dict]
    selected_text: str
    attempt: int = 1


@app.post("/submit")
async def submit(req: SubmitRequest):
    t0 = time.perf_counter()
    results = await judge(req.code)
    hint = await get_hint(req.code, results)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    # 紀錄這次提交（只在 TESTGEN_SESSION_LOG=1 時實際寫檔）
    if LOG_ENABLED:
        await log_submission(
            code=req.code,
            results=results,
            hint=hint,
            ai_prompt=build_prompt(req.code, results),
            elapsed_ms=elapsed_ms,
        )
    return {"results": results, "hint": hint}


@app.post("/hint")
async def hint_endpoint(req: HintRequest):
    """學生選完診斷選項後，評估是否正確並回傳提示或新選項。"""
    result = await evaluate_selection(
        req.code, req.results, req.selected_text, req.attempt
    )
    return result
