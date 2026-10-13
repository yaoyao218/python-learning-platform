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

_MODEL = "gemini-2.0-flash" if _use_gemini else "openai/gpt-oss-20b"


def build_prompt(results: list[dict], problem_title: str, problem_context: str) -> str | None:
    """
    組裝 AI prompt，完全不讀學生程式碼。
    - 全部通過 → 回傳 None
    - syntax_error  → 只送 stderr
    - runtime_error → 送觸發錯誤的 input + stderr
    - timeout       → 壓力測資超時談效率；一般測資超時談無窮迴圈（沒有行號可看）
    - no_return     → 固定提示
    - wrong_answer  → 送所有失敗的 (input, expected, actual)，蘇格拉底式

    Args:
        problem_title: 題目名稱（如 "Valid Parentheses"）
        problem_context: 題目定義的純文字描述（給 AI 當上下文，不含 HTML）
    """
    failed = [r for r in results if not r["passed"]]
    if not failed:
        return None

    first_fail = failed[0]
    error_type = first_fail["error_type"]

    if error_type == "syntax_error":
        return f"""你是一個程式學習助教，幫助大一學生學習 Python。

學生在解 {problem_title} 時發生語法錯誤：

{first_fail['stderr']}

請依序做三件事：
1. 用一句白話文解釋這個錯誤訊息的意思（20 字以內）
2. 提示學生根據行號找到問題位置
3. 用一個問題引導學生思考那個位置哪裡不對

規則：不要給出修正後的程式碼。繁體中文，語氣像陪學生 debug 的學長姐。120 字以內。"""

    if error_type == "runtime_error":
        return f"""你是一個程式學習助教，幫助大一學生學習 Python。

題目：{problem_title}
（{problem_context}）

學生程式在以下輸入時發生執行期錯誤：
- 輸入：{first_fail['input']!r}
- 錯誤訊息：{first_fail['stderr']}

請依序做三件事：
1. 用白話文解釋這個錯誤是什麼意思
2. 引導學生去看錯誤訊息中的行號
3. 問學生：「這個輸入有什麼特別的地方，可能讓程式在那行出錯？」

規則：不要給出修正後的程式碼。繁體中文，語氣友善鼓勵。150 字以內。"""

    if error_type == "timeout":
        if first_fail.get("is_stress"):
            situation = "學生程式在一筆很長的壓力測資上超過時間限制，較短的測資都沒有超時，代表寫法正確但效率不夠。"
            task = """1. 用白話文說明「超過時間限制」代表程式跑太慢，不是答案錯
2. 引導學生估算：輸入長度變成幾萬時，自己的寫法大概要做幾次操作
3. 用一個問題引導學生思考：「有哪些重複的計算，可以記下來不用每次重算？」"""
        else:
            situation = f"學生程式在一筆很短的測資（輸入：{first_fail['input']!r}）上就超過時間限制，很可能是無窮迴圈。"
            task = """1. 用白話文說明短輸入也超時，通常代表迴圈停不下來（無窮迴圈）
2. 引導學生檢查迴圈的結束條件，以及每一輪有沒有讓變數往結束的方向前進
3. 用一個問題引導學生，拿這筆輸入手動跑幾輪迴圈看看"""
        return f"""你是一個程式學習助教，幫助大一學生學習 Python。

題目：{problem_title}
（{problem_context}）

{situation}
超時沒有錯誤訊息，也沒有行號可以看。

請依序做三件事：
{task}

規則：不要給出修正後的程式碼或完整演算法。繁體中文，語氣友善鼓勵。150 字以內。"""

    if error_type == "no_return":
        return f"""你是一個程式學習助教，幫助大一學生學習 Python。

題目：{problem_title}

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
    n_total = len(results)
    # 只放答錯的測資：後面若有超時或執行錯誤，Actual 是 None，會干擾數值 pattern 分析
    failed_summary = "\n".join(
        f"- Input: {truncate(r['input'])} / Expected: {r['expected']} / Actual: {truncate(r['actual'])}"
        for r in failed
        if r["error_type"] is None
    )

    return f"""你是一個程式學習助教，專門幫助大一學生學習解題思維。

題目：{problem_title}
定義：{problem_context}

學生有 {n_fail}/{n_total} 筆測資失敗，以下是其中答錯（有輸出但數值不對）的案例：
{failed_summary}

請先分析這些失敗案例的數值 pattern（不要輸出分析過程），
再根據推斷出的理解落差，用一個蘇格拉底式問題引導學生。

提示深度原則：
- 學生答案方向完全錯誤 → 從觀念入手（題目的核心定義、關鍵演算法概念）
- 學生方向正確但細節錯 → 從具體數字追問（為什麼這個 input 得到這個 output）

輸出規則：
- 只輸出給學生看的提示，不要輸出分析
- 不要給出正確程式碼或完整演算法步驟
- 結尾必須是一個問句
- 繁體中文，語氣像在討論題目的學長姐
- 200 字以內"""


async def get_hint(results: list[dict], problem_title: str, problem_context: str) -> str | None:
    """呼叫 Groq/Gemini API 取得 AI 提示。全部通過時回傳 None。API 失敗時回傳 None。"""
    prompt = build_prompt(results, problem_title, problem_context)
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
