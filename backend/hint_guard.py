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

# 完整的 fenced code block（跟 masking.py 的 _FENCE_RE 抓法一致）
_FENCE_PATTERN = re.compile(r"```[^\n]*\n.*?```", re.DOTALL)

# 虛擬碼的編號步驟（「3. 對於每一天的價格 `p`：」）
_STEP_PATTERN = re.compile(r"^\s*\d+\.\s*(.+)$", re.MULTILINE)

# 提示裡逐字出現幾個虛擬碼步驟就算「整段複述」。引用一兩步的意思是允許的（G1）。
MAX_COPIED_STEPS = 2

FALLBACK_HINT = (
    "這次的提示內容不適合直接顯示，可能不小心夾帶了程式碼片段。"
    "你可以先回頭看看目前測資失敗的地方，想想看是哪一步算錯了？"
)


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _copied_steps(hint: str, pseudocode: str) -> int:
    """提示裡逐字出現了幾個虛擬碼步驟（忽略空白差異）。"""
    flat = _squash(hint)
    steps = [_squash(m) for m in _STEP_PATTERN.findall(pseudocode)]
    return sum(1 for step in steps if len(step) >= 6 and step in flat)


def check_hint_quality(hint: str, code_blocks_vetted: bool = False,
                       pseudocode: str | None = None) -> list[str]:
    """回傳這則提示違反 code-blind 規則的項目；空 list 代表沒問題。

    code_blocks_vetted=True 表示 masking 已經檢查過完整的 ``` 程式碼區塊
    （洩漏的已遮罩或隱藏，剩下的是跑不過測資的片段），這時只檢查區塊以外的
    文字，抓 AI 沒用 ``` 包起來、直接寫在句子裡的程式碼。

    pseudocode：該題給學生的虛擬碼。提示可以引用步驟編號與意思，但逐字抄了
    超過 MAX_COPIED_STEPS 個步驟就算整段複述（學生手上已有，複述沒有引導意義）。
    虛擬碼是自然語言步驟，不含 ```、def、class Solution，不會被當成程式碼。
    """
    problems = []
    code_text = _FENCE_PATTERN.sub("", hint) if code_blocks_vetted else hint
    if "```" in code_text:
        problems.append("包含程式碼區塊標記 ```")
    if _DEF_PATTERN.search(code_text):
        problems.append("包含函式定義（def ...）")
    if "class Solution" in code_text:
        problems.append("包含 'class Solution'")
    if "?" not in hint and "？" not in hint:
        problems.append("沒有問句（結尾應引導學生思考，而非直接給答案）")
    if pseudocode:
        copied = _copied_steps(hint, pseudocode)
        if copied > MAX_COPIED_STEPS:
            problems.append(f"整段複述虛擬碼（逐字抄了 {copied} 個步驟）")
    return problems


def guard(hint: str, code_blocks_vetted: bool = False,
          pseudocode: str | None = None) -> tuple[str, list[str]]:
    """套用品質檢查。回傳 (實際要顯示給學生的文字, 違規項目清單)。

    code_blocks_vetted、pseudocode 見 check_hint_quality。

    違規時回傳 FALLBACK_HINT 取代原文，違規清單非空；
    通過時原樣回傳 hint，違規清單是空的。
    """
    problems = check_hint_quality(hint, code_blocks_vetted, pseudocode)
    if problems:
        return FALLBACK_HINT, problems
    return hint, []
