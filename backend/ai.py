import logging
import os
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv

from hint_guard import guard

load_dotenv()

_logger = logging.getLogger(__name__)

_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY", "")
_use_gemini = bool(os.environ.get("GEMINI_API_KEY"))

client = AsyncOpenAI(
    api_key=_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/" if _use_gemini else "https://api.groq.com/openai/v1",
)

_MODEL = "gemini-2.0-flash" if _use_gemini else "openai/gpt-oss-20b"


def _pseudocode_parts(pseudocode: str | None) -> tuple[str, str]:
    """虛擬碼是題目材料（學生手上也有），不是學生程式碼。回傳 (材料段落, 額外規則)。"""
    if not pseudocode:
        return "", ""
    material = f"\n\n虛擬碼（學生手上也有同一份，步驟有編號）：\n{pseudocode.strip()}"
    rules = ("\n- 可以引用虛擬碼的步驟編號與意思（例如「想想第 4 步在這個輸入上會發生什麼？」），"
             "但不要整段複述虛擬碼"
             "\n- 不要斷言學生「第 N 步錯了」，用問句引導學生自己檢查")
    return material, rules


def build_prompt(results: list[dict], problem_title: str, problem_context: str,
                 pseudocode: str | None = None) -> str | None:
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
        pseudocode: 該題通過往返檢查的虛擬碼（可選）；runtime_error、timeout、
            wrong_answer 會放進題目材料
    """
    failed = [r for r in results if not r["passed"] and not r.get("skipped")]   # 超時後被略過的沒有執行結果，不給 AI
    pseudo_material, pseudo_rules = _pseudocode_parts(pseudocode)
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
（{problem_context}）{pseudo_material}

學生程式在以下輸入時發生執行期錯誤：
- 輸入：{first_fail['input']!r}
- 錯誤訊息：{first_fail['stderr']}

請依序做三件事：
1. 用白話文解釋這個錯誤是什麼意思
2. 引導學生去看錯誤訊息中的行號
3. 問學生：「這個輸入有什麼特別的地方，可能讓程式在那行出錯？」

規則：不要給出修正後的程式碼。繁體中文，語氣友善鼓勵。150 字以內。{pseudo_rules}"""

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
（{problem_context}）{pseudo_material}

{situation}
超時沒有錯誤訊息，也沒有行號可以看。

請依序做三件事：
{task}

規則：不要給出修正後的程式碼或完整演算法。繁體中文，語氣友善鼓勵。150 字以內。{pseudo_rules}"""

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
定義：{problem_context}{pseudo_material}

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
- 200 字以內{pseudo_rules}"""


async def get_hint(
    results: list[dict],
    problem_title: str,
    problem_context: str,
    problem_id: str | None = None,
    pseudocode: str | None = None,
) -> str | None:
    """呼叫 Groq/Gemini API 取得 AI 提示。全部通過時回傳 None。API 失敗時回傳 None。

    AI 回覆在送到學生畫面前會經過兩道輸出端檢查：
      1. masking（有 problem_id 時）：提示裡的程式碼區塊若能通過測資，
         把關鍵邏輯遮成 # TODO，其餘文字保留
      2. hint_guard：檢查程式碼區塊以外的文字（AI 沒用 ``` 包起來的程式碼）
         和結尾問句，不合格就整段換成安全的替代文字

    Args:
        results:         judge() 回傳的測資結果清單
        problem_title:   題目名稱
        problem_context: 純文字題意（給 AI 當上下文）
        problem_id:      題目 ID；提供時對 AI 回覆執行遮罩檢查，None 則跳過（向下相容）
        pseudocode:      該題虛擬碼（可選）；放進 prompt，並讓 hint_guard 擋整段複述
    """
    prompt = build_prompt(results, problem_title, problem_context, pseudocode)
    if prompt is None:
        return None

    try:
        # gpt-oss 預設推理可能把 2048 token 全用在推理、回傳空內容（K3），一律壓到 low
        extra = {"reasoning_effort": "low"} if "gpt-oss" in _MODEL else {}
        response = await client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            **extra,
        )
        content = response.choices[0].message.content
        if content is None:
            return None
    except openai.OpenAIError as e:
        _logger.warning("AI hint request failed (%s): %s", _MODEL, e)
        return None

    # 有 problem_id 時執行遮罩檢查；本地 import 避免循環依賴
    # （masking.py 不得在模組層級 import ai.py）
    if problem_id is not None:
        from masking import sanitize_hint  # noqa: PLC0415
        content = await sanitize_hint(content, problem_id, problem_title, client, _MODEL)

    safe_hint, problems = guard(content, code_blocks_vetted=problem_id is not None, pseudocode=pseudocode)
    if problems:
        _logger.warning("AI hint failed quality guard, using fallback: %s", problems)
    return safe_hint
