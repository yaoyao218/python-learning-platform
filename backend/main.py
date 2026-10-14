import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from judge import judge
from ai import get_hint, build_prompt
from problem import PROBLEMS
from cloze import cloze_for

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
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SubmitRequest(BaseModel):
    code: str
    problem_id: str


@app.get("/problems")
async def list_problems():
    return [
        {"id": pid, "title": p["title"], "difficulty": p["difficulty"]}
        for pid, p in PROBLEMS.items()
    ]


@app.get("/problems/{problem_id}")
async def get_problem(problem_id: str):
    problem = PROBLEMS.get(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    detail = {
        "id": problem_id,
        "title": problem["title"],
        "difficulty": problem["difficulty"],
        "description": problem["description"],
        "examples": problem["examples"],
        "constraints": problem["constraints"],
        "starter_code": problem["starter_code"],
    }
    # 虛擬碼是可選欄位：只有通過往返檢查的題目才有（測資內容不送到前端）
    if "pseudocode" in problem:
        detail["pseudocode"] = problem["pseudocode"]
    return detail


@app.get("/problems/{problem_id}/cloze")
async def get_cloze(problem_id: str):
    """遮照填空：標準答案挖掉關鍵部分的版本。前端在學生連續失敗 3 次後才拿來顯示。
    只送挖洞後的程式碼與空格數，答案不送。"""
    if problem_id not in PROBLEMS:
        raise HTTPException(status_code=404, detail="Problem not found")
    cloze = cloze_for(problem_id)
    if cloze is None:
        raise HTTPException(status_code=404, detail="No cloze for this problem")
    return {"code": cloze.code, "blanks": len(cloze.answers)}


@app.post("/submit")
async def submit(req: SubmitRequest):
    if req.problem_id not in PROBLEMS:
        raise HTTPException(status_code=404, detail="Problem not found")

    problem = PROBLEMS[req.problem_id]
    title, context = problem["title"], problem["ai_context"]
    pseudocode = problem.get("pseudocode", {}).get("text")

    t0 = time.perf_counter()
    results = await judge(req.code, req.problem_id)
    hint = await get_hint(results, title, context, problem_id=req.problem_id, pseudocode=pseudocode)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    # 紀錄這次提交（只在 TESTGEN_SESSION_LOG=1 時實際寫檔）
    if LOG_ENABLED:
        await log_submission(
            code=req.code,
            results=results,
            hint=hint,
            ai_prompt=build_prompt(results, title, context, pseudocode),
            elapsed_ms=elapsed_ms,
        )
    return {"results": results, "hint": hint}
