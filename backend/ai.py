import os
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


def build_prompt(results: list[dict]) -> str | None:
    """
    組裝 AI prompt，完全不讀學生程式碼。
    - 全部通過 → 回傳 None
    - syntax_error  → 只送 stderr
    - runtime_error → 送觸發錯誤的 input + stderr
    - no_return     → 固定提示
    - wrong_answer  → 送所有失敗的 (input, expected, actual)，蘇格拉底式
    """
    failed = [r for r in results if not r["passed"]]
    if not failed:
        return None

    first_fail = failed[0]
    error_type = first_fail["error_type"]

    if error_type == "syntax_error":
        return f"""你是一個程式學習助教，幫助大一學生學習 Python。

學生在解 Longest Substring Without Repeating Characters 時發生語法錯誤：

{first_fail['stderr']}

請依序做三件事：
1. 用一句白話文解釋這個錯誤訊息的意思（20 字以內）
2. 提示學生根據行號找到問題位置
3. 用一個問題引導學生思考那個位置哪裡不對

規則：不要給出修正後的程式碼。繁體中文，語氣像陪學生 debug 的學長姐。120 字以內。"""

    if error_type == "runtime_error":
        return f"""你是一個程式學習助教，幫助大一學生學習 Python。

題目：Longest Substring Without Repeating Characters
（給一個字串，找不含重複字元的最長子字串長度）

學生程式在以下輸入時發生執行期錯誤：
- 輸入：{first_fail['input']!r}
- 錯誤訊息：{first_fail['stderr']}

請依序做三件事：
1. 用白話文解釋這個錯誤是什麼意思
2. 引導學生去看錯誤訊息中的行號
3. 問學生：「這個輸入有什麼特別的地方，可能讓程式在那行出錯？」

規則：不要給出修正後的程式碼。繁體中文，語氣友善鼓勵。150 字以內。"""

    if error_type == "no_return":
        return """你是一個程式學習助教，幫助大一學生學習 Python。

題目：Longest Substring Without Repeating Characters

學生的函式執行完後回傳了 None，代表答案沒有被傳出來。

請做兩件事：
1. 解釋 Python 函式為什麼需要 return 語句
2. 用一個問題讓學生思考：「你計算出來的答案，存在哪個變數裡？那個變數最後有沒有被回傳？」

規則：不要直接說程式碼要怎麼改。繁體中文，語氣像幫學生釐清思路的學長姐。100 字以內。"""

    # wrong_answer（error_type is None）
    def truncate(v, n=50):
        s = repr(v)
        return s if len(s) <= n else s[:n] + "..."

    n_fail = len(failed)
    failed_summary = "\n".join(
        f"- Input: {truncate(r['input'])} / Expected: {r['expected']} / Actual: {truncate(r['actual'])}"
        for r in failed
    )

    return f"""你是一個程式學習助教，專門幫助大一學生學習解題思維。

題目：Longest Substring Without Repeating Characters
定義：給一個字串，找「不含重複字元的最長子字串」的長度。
例如："abcabcbb" → 3，因為 "abc" 是最長的無重複子字串。

學生有 {n_fail}/17 筆測資失敗，以下是全部失敗案例：
{failed_summary}

請先分析這些失敗案例的數值 pattern（不要輸出分析過程），
再根據推斷出的理解落差，用一個蘇格拉底式問題引導學生。

提示深度原則：
- 學生答案方向完全錯誤 → 從觀念入手（子字串的定義、滑動視窗的概念）
- 學生方向正確但細節錯 → 從具體數字追問（為什麼這個 input 得到這個 output）

輸出規則：
- 只輸出給學生看的提示，不要輸出分析
- 不要給出正確程式碼或完整演算法步驟
- 結尾必須是一個問句
- 繁體中文，語氣像在討論題目的學長姐
- 200 字以內"""


async def get_hint(results: list[dict]) -> str | None:
    """呼叫 Groq/Gemini API 取得 AI 提示。全部通過時回傳 None。API 失敗時回傳 None。"""
    prompt = build_prompt(results)
    if prompt is None:
        return None

    try:
        response = await client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        if content is None:
            return None
        return content
    except openai.OpenAIError:
        return None
