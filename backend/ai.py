import os
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


def build_prompt(code: str, results: list[dict]) -> str | None:
    """
    組裝 AI prompt。
    - 全部通過 → 回傳 None
    - 依 first_fail 的 error_type（4 種）選擇 3 個 prompt 分支：
      * syntax_error / runtime_error → 簡化版，傳 stderr（error_label 不同）
      * no_return → 簡化版，提醒 return
      * None (wrong answer) → 完整版，傳所有失敗 cases 做 pattern 推斷
    """
    failed = [r for r in results if not r["passed"]]
    if not failed:
        return None

    first_fail = failed[0]
    error_type = first_fail["error_type"]

    if error_type in ("syntax_error", "runtime_error"):
        error_label = "語法錯誤（程式無法執行）" if error_type == "syntax_error" else "執行時期錯誤（runtime error）"
        return f"""你是一個程式學習助教，目標是幫助大一學生學習 Python。

學生程式碼：
{code}

發生了{error_label}，錯誤訊息如下：
{first_fail['stderr']}

請依序做三件事：
1. 用一句話解釋這個錯誤訊息的意思
2. 提示學生看錯誤訊息中的行號或關鍵字，幫他定位問題位置
3. 問一個引導性問題，讓學生自己找到修正方向

規則：
- 不要直接給出修正後的程式碼
- 用繁體中文，語氣友善鼓勵
- 回答控制在 150 字以內"""

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

    # wrong_answer (error_type is None): use full pattern-analysis prompt
    def truncate(v, n=50):
        s = repr(v)
        return s if len(s) <= n else s[:n] + '...'

    failed_summary = "\n".join(
        f"- Input: {truncate(r['input'])} / Expected: {r['expected']} / Actual: {truncate(r['actual'])}"
        for r in failed
    )

    return f"""你是一個程式學習助教，幫助大一學生學習 Python。

題目：Longest Substring Without Repeating Characters
學生程式碼：
{code}

目前學生看到的第一個失敗案例：
- 輸入：{first_fail['input']!r}
- 學生程式碼的輸出：{first_fail['actual']}
- 正確答案：{first_fail['expected']}

其他失敗案例（輔助參考）：
{failed_summary}

分析前請先檢查這些常見 Python 問題：
- return 語句的縮排層級是否正確（是在最內層迴圈內提早回傳，還是在正確位置）
- 迴圈是否提早終止導致只處理了部分輸入

請根據「這個輸入」和「學生程式碼實際給出的輸出」，找出最可能的根本原因，給學生一個引導式提示讓他能朝正確方向思考。

要求：
1. 不要直接給出正確程式碼
2. 提示要具體，針對這個 input/output 的落差，不要泛泛而談
3. 用繁體中文，語氣自然友善，像在跟學生說話
4. 控制在 150 字以內"""


async def get_hint(code: str, results: list[dict]) -> str | None:
    """呼叫 Groq/Gemini API 取得 AI 提示。全部通過時回傳 None。API 失敗時回傳 None。"""
    prompt = build_prompt(code, results)
    if prompt is None:
        return None

    try:
        result = client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        response = await result if inspect.isawaitable(result) else result
        content = response.choices[0].message.content
        if content is None:
            return None
        return content
    except openai.OpenAIError:
        return None
