"""code-blind 提示系統的輸出端安全網。

ai.py 的 build_prompt() 從源頭就不把學生程式碼交給 LLM，這是第一道、也是最
主要的防線。但 LLM 不保證完全遵守「不要給程式碼」的指令——即使 prompt 裡
明講了，模型仍可能在示範概念時夾帶一段程式碼。這個模組是第二道防線：在把
提示顯示給學生之前，檢查輸出本身有沒有洩漏的跡象，有的話換成安全的替代文字，
而不是直接把可能夾帶程式碼的內容送到使用者畫面上。

跟先遮罩再顯示（mask then show）的做法不同，這裡選擇「不合格就整句換掉」
而非「局部塗黑」：提示是自然語言敘述，不是結構化的程式碼，逐詞塗黑會讓句子
讀起來破碎不通順，風險跟收益不成比例，所以採用更簡單、更不會出錯的整句替換。
"""
import re

_DEF_PATTERN = re.compile(r"def\s+\w+\s*\(")

FALLBACK_HINT = (
    "這次的提示內容不適合直接顯示，可能不小心夾帶了程式碼片段。"
    "你可以先回頭看看目前測資失敗的地方，想想看是哪一步算錯了？"
)


def check_hint_quality(hint: str) -> list[str]:
    """回傳這則提示違反 code-blind 規則的項目；空 list 代表沒問題。"""
    problems = []
    if "```" in hint:
        problems.append("包含程式碼區塊標記 ```")
    if _DEF_PATTERN.search(hint):
        problems.append("包含函式定義（def ...）")
    if "class Solution" in hint:
        problems.append("包含 'class Solution'")
    if "?" not in hint and "？" not in hint:
        problems.append("沒有問句（結尾應引導學生思考，而非直接給答案）")
    return problems


def guard(hint: str) -> tuple[str, list[str]]:
    """套用品質檢查。回傳 (實際要顯示給學生的文字, 違規項目清單)。

    違規時回傳 FALLBACK_HINT 取代原文，違規清單非空；
    通過時原樣回傳 hint，違規清單是空的。
    """
    problems = check_hint_quality(hint)
    if problems:
        return FALLBACK_HINT, problems
    return hint, []
