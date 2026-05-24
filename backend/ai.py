import json
import os
import re
import inspect
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY", "")
_use_gemini = bool(os.environ.get("GEMINI_API_KEY"))

client = AsyncOpenAI(
    api_key=_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/" if _use_gemini else "https://api.groq.com/openai/v1",
)

_MODEL = "gemini-2.0-flash" if _use_gemini else "llama-3.1-8b-instant"


# ── helpers ──────────────────────────────────────────────────────────────────

def _truncate(v, n=50) -> str:
    s = repr(v)
    return s if len(s) <= n else s[:n] + "..."


def _failed_lines(results: list[dict], limit: int = 5) -> str:
    failed = [r for r in results if not r["passed"]]
    return "\n".join(
        f"- 輸入 {_truncate(r['input'])} → 預期 {r['expected']}，你的輸出 {_truncate(r['actual'])}"
        for r in failed[:limit]
    )


def _extract_json(text: str) -> dict:
    """從 AI 回應中擷取 JSON 物件，容錯處理 markdown code block。"""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("No valid JSON found in AI response")


async def _call_ai(prompt: str) -> str | None:
    """呼叫 AI API，回傳原始文字。失敗時回傳 None。"""
    try:
        result = client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        resp = await result if inspect.isawaitable(result) else result
        return resp.choices[0].message.content
    except openai.OpenAIError:
        return None


# ── prompt builders ───────────────────────────────────────────────────────────

def build_prompt(code: str, results: list[dict]) -> str | None:
    """舊版 prompt（syntax / runtime / no_return 仍沿用）。"""
    failed = [r for r in results if not r["passed"]]
    if not failed:
        return None

    first_fail = failed[0]
    error_type = first_fail["error_type"]

    if error_type == "syntax_error":
        return f"""你是一個程式學習助教，目標是幫助大一學生學習 Python。

學生程式碼：
{code}

程式碼有語法錯誤，無法執行。錯誤訊息如下：
{first_fail['stderr']}

請解釋這個語法錯誤的意思，並引導學生找到並修正問題。

規則：
1. 不要直接給出修正後的程式碼
2. 用繁體中文回答，語氣友善鼓勵
3. 回答控制在 150 字以內"""

    if error_type == "runtime_error":
        return f"""你是一個程式學習助教，目標是幫助大一學生學習 Python。

學生程式碼：
{code}

程式執行時發生錯誤，錯誤訊息如下：
{first_fail['stderr']}

請解釋這個錯誤訊息的意思，並引導學生找到並修正問題。

規則：
1. 不要直接給出修正後的程式碼
2. 用繁體中文回答，語氣友善鼓勵
3. 回答控制在 150 字以內"""

    if error_type == "no_return":
        return f"""你是一個程式學習助教，目標是幫助大一學生學習 Python。

學生程式碼：
{code}

問題：函式執行後回傳了 None，代表函式內沒有 return 語句或 return 沒有帶值。

請提醒學生函式需要回傳值，並說明 return 的用法。

規則：
1. 不要直接給出答案
2. 用繁體中文回答，語氣友善鼓勵
3. 回答控制在 100 字以內"""

    return None  # wrong_answer 走新的診斷流程


def _build_diagnosis_prompt(code: str, results: list[dict]) -> str:
    lines = _failed_lines(results)
    return f"""你是程式學習助教，題目是 Longest Substring Without Repeating Characters。

學生程式碼：
{code}

失敗測資：
{lines}

任務：分析程式碼找出真正的錯誤，設計 3 個選項讓學生自我診斷。
選項用學生第一人稱描述他「以為自己做對的事」，其中一個是真正問題，另外兩個是同類題常見的干擾項。

只回傳 JSON，不要其他文字：
{{"intro":"一句引導語讓學生思考","options":[{{"id":"A","text":"我..."}},{{"id":"B","text":"我..."}},{{"id":"C","text":"我..."}}]}}"""


def _build_followup_prompt(code: str, results: list[dict], selected_text: str, attempt: int) -> str:
    lines = _failed_lines(results)
    depth = "給一個方向性提示（不要太具體）" if attempt <= 1 else "給較具體提示（指出哪個邏輯要修改，但不給出程式碼）"
    return f"""你是程式學習助教，題目是 Longest Substring Without Repeating Characters。

程式碼：
{code}

失敗測資：
{lines}

學生認為他的問題是：「{selected_text}」

判斷這個描述是否符合程式碼的實際錯誤：
- 符合 → {depth}（繁體中文，150字內）
- 不符合 → 簡短說明為何不對（50字內）+ 重新給 2 個更精準的選項

只回傳 JSON，不要其他文字：
符合：{{"correct":true,"hint":"提示文字"}}
不符合：{{"correct":false,"message":"說明","options":[{{"id":"A","text":"我..."}},{{"id":"B","text":"我..."}}]}}"""


# ── public API ────────────────────────────────────────────────────────────────

async def get_hint(code: str, results: list[dict]) -> str | dict | None:
    """
    主要入口。依 error_type 決定回傳格式：
    - syntax_error / runtime_error / no_return → str（舊版）
    - wrong_answer → dict {type:"diagnosis", intro, options}
    - 全部通過 → None
    """
    failed = [r for r in results if not r["passed"]]
    if not failed:
        return None

    error_type = failed[0]["error_type"]

    # 語法 / 執行 / 沒 return → 直接給文字提示
    if error_type in ("syntax_error", "runtime_error", "no_return"):
        prompt = build_prompt(code, results)
        text = await _call_ai(prompt)
        return text  # str or None

    # wrong_answer → 回傳診斷選項
    prompt = _build_diagnosis_prompt(code, results)
    text = await _call_ai(prompt)
    if not text:
        return None
    try:
        data = _extract_json(text)
        return {"type": "diagnosis", "intro": data["intro"], "options": data["options"]}
    except Exception:
        # fallback：如果 JSON 解析失敗，直接給文字提示
        return text


async def evaluate_selection(
    code: str,
    results: list[dict],
    selected_text: str,
    attempt: int,
) -> dict:
    """
    評估學生選擇。回傳：
    - {correct: True, hint: str}
    - {correct: False, message: str, options: list}
    """
    prompt = _build_followup_prompt(code, results, selected_text, attempt)
    text = await _call_ai(prompt)
    if not text:
        return {"correct": True, "hint": "系統暫時無法判斷，請重新提交程式碼再試。"}
    try:
        return _extract_json(text)
    except Exception:
        # fallback：視為正確並把回應當 hint
        return {"correct": True, "hint": text[:300]}


def build_prompt_for_log(code: str, results: list[dict]) -> str | None:
    """給 session_logger 用，永遠回傳舊版 prompt（不走診斷流程）。"""
    failed = [r for r in results if not r["passed"]]
    if not failed:
        return None
    first_fail = failed[0]
    error_type = first_fail["error_type"]

    simple = build_prompt(code, results)
    if simple:
        return simple

    # wrong_answer fallback
    failed_summary = "\n".join(
        f"- Input: {_truncate(r['input'])} / Expected: {r['expected']} / Actual: {_truncate(r['actual'])}"
        for r in failed
    )
    return f"[wrong_answer] first_fail input={first_fail['input']!r}\n{failed_summary}"
