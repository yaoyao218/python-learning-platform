"""
masking.py — AI 提示遮罩層

偵測 AI 回覆裡是否夾帶可執行的完整解答，並用 LLM 遮蔽關鍵邏輯。

循環 import 規則
-----------------
本模組 **不得** 在模組層級 import ai.py。
client 與 model 必須由呼叫端（ai.py 的 get_hint）傳入。
judge 與 problem 的 import 放在函式內部，保持安全。
"""

from __future__ import annotations

import ast
import re

# ── 常數 ─────────────────────────────────────────────────────────────────────

# 通過幾筆測資就視為洩漏完整解答
MIN_PASS_TO_FLAG: int = 1

# 遮蔽失敗或遮蔽後仍能通過測資時，只替換該程式碼區塊為此佔位文字，其餘文字保留
_BLOCK_PLACEHOLDER: str = "（這裡原本有一段完整程式碼，已被隱藏。先自己試著寫寫看吧！）"

# 遮蔽用的 LLM prompt 模板
_MASK_PROMPT_TEMPLATE = """\
你是程式教學助教。以下是一段解 "{title}" 的程式碼：

```python
{code}
```

請把「解題關鍵邏輯」的行換成 `# TODO`，保留：
- 函式與類別的定義骨架（def、class 那行）
- 不含解法的初始化與輸入處理
- 所有中文或英文的說明性註解（除非那行本身就是解法）

只輸出修改後的程式碼，不要任何說明文字，也不要用 markdown 的反引號包裝。"""

# ── 正規表達式：抓取 fenced code block ───────────────────────────────────────

# 支援有無 language tag 的 fenced block（`）
# group 1 = 完整的原始 fence 字串（含 ``` 與換行），用於替換
# group 2 = code 內容
_FENCE_RE = re.compile(
    r"(```[^\n]*\n(.*?)```)",
    re.DOTALL,
)


# ── 公開 API ─────────────────────────────────────────────────────────────────


def extract_code_blocks(text: str) -> list[tuple[str, str]]:
    """從 markdown 文字抽出所有 fenced code block。

    Returns:
        list of (original_fence, code_content)
        original_fence 是含前後 ``` 的完整原始字串，用於字串替換時精確定位。
        code_content 是 ``` 之間的純程式碼內容。

    已知限制：
        只處理 fenced block（``` 包住的區塊），縮排式程式碼不在範圍內。
    """
    return [(m.group(1), m.group(2)) for m in _FENCE_RE.finditer(text)]


def _wrap_if_needed(code: str, method: str) -> str:
    """若 code 只有裸 def（無 class Solution），在後面附加委派用的 class Solution。

    executor.run_code 固定執行 `Solution().{method}(...)`。
    將裸函式直接縮排進 class 會因為缺少 self 而 TypeError；
    改為在原程式碼後附加一個委派包裝，把 Solution().method(*args) 轉發給頂層函式。

    目標函式尋找順序：
        1. 頂層函式中名稱等於 method 的
        2. 最後一個頂層函式（fallback）

    語法錯誤的 code 原樣回傳，讓 judge 自然回傳失敗。
    頂層已有 class Solution 則原樣回傳，不附加包裝。
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    # 頂層已有 class Solution → 不需要包裝
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Solution":
            return code

    # 找所有頂層函式
    top_level_funcs = [
        node for node in tree.body if isinstance(node, ast.FunctionDef)
    ]
    if not top_level_funcs:
        # 沒有可用的函式，原樣回傳（judge 會自然失敗）
        return code

    # 優先找名稱等於 method 的，否則用最後一個
    target_func = next(
        (f for f in top_level_funcs if f.name == method),
        top_level_funcs[-1],
    )
    target_name = target_func.name

    # 在原程式碼後附加委派 class，不縮排原始程式碼
    wrapper = (
        f"\nclass Solution:\n"
        f"    def {method}(self, *args):\n"
        f"        return {target_name}(*args)\n"
    )
    return code + wrapper



async def is_full_solution(code: str, problem_id: str) -> bool:
    """判斷 code 是否能通過 >= MIN_PASS_TO_FLAG 筆測資。

    複用 judge() 跑全部測資；judge 出錯時保守回傳 False。
    自動補上 class Solution 包裝（若需要）。
    """
    # 本地 import，避免循環依賴
    from problem import PROBLEMS  # noqa: PLC0415
    from judge import judge        # noqa: PLC0415

    problem = PROBLEMS.get(problem_id)
    if problem is None:
        return False

    method = problem["method"]
    wrapped = _wrap_if_needed(code, method)

    try:
        results = await judge(wrapped, problem_id)
    except Exception:
        return False

    passed_count = sum(1 for r in results if r["passed"])
    return passed_count >= MIN_PASS_TO_FLAG


async def mask_code(code: str, title: str, client, model: str) -> str | None:
    """呼叫 LLM，把程式碼的解題關鍵邏輯換成 # TODO。

    Args:
        code:   要遮蔽的程式碼字串
        title:  題目名稱（放進 prompt 提供上下文）
        client: AsyncOpenAI instance，由呼叫端傳入
        model:  模型名稱字串

    Returns:
        遮蔽後的程式碼字串；LLM 呼叫失敗時回傳 None。
    """
    import openai  # noqa: PLC0415

    prompt = _MASK_PROMPT_TEMPLATE.format(title=title, code=code)
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        if not content:
            return None
        # LLM 可能仍回傳 markdown fence，去除之
        stripped = content.strip()
        if stripped.startswith("```"):
            # 移除首尾 fence
            lines = stripped.splitlines()
            # 第一行是 ```python 或 ```，最後一行是 ```
            inner_lines = lines[1:] if lines[-1].strip() == "```" else lines[1:]
            if inner_lines and inner_lines[-1].strip() == "```":
                inner_lines = inner_lines[:-1]
            stripped = "\n".join(inner_lines)
        return stripped
    except openai.OpenAIError:
        return None
    except Exception:
        return None


async def sanitize_hint(
    hint: str | None,
    problem_id: str,
    title: str,
    client,
    model: str,
) -> str | None:
    """完整的遮罩 pipeline，對 get_hint 的回傳值做後處理。

    流程：
        1. hint 為 None → 直接回傳 None
        2. 無 code block → 原樣回傳
        3. 對每個 block：
            a. 跑不過任何測資 → 不處理，繼續
            b. 洩漏 + mask 失敗 → 只替換此 block 為 _BLOCK_PLACEHOLDER，繼續
            c. 洩漏 + 遮蔽後仍能通過 → 只替換此 block 為 _BLOCK_PLACEHOLDER，繼續
            d. 洩漏 + 遮蔽成功且安全 → 替換此 block 為遮蔽後程式碼，繼續
        4. 回傳替換後的 hint（其餘文字完整保留）
    """
    if hint is None:
        return None

    blocks = extract_code_blocks(hint)
    if not blocks:
        return hint

    sanitized = hint

    for original_fence, code_content in blocks:
        leaked = await is_full_solution(code_content, problem_id)
        if not leaked:
            continue

        # 嘗試遮蔽
        masked = await mask_code(code_content, title, client, model)
        if masked is None:
            # 遮蔽失敗：只替換此區塊，保留其餘文字
            sanitized = sanitized.replace(original_fence, _BLOCK_PLACEHOLDER, 1)
            continue

        # 驗證遮蔽後是否仍能通過
        still_leaks = await is_full_solution(masked, problem_id)
        if still_leaks:
            # 遮蔽不充分：只替換此區塊，保留其餘文字
            sanitized = sanitized.replace(original_fence, _BLOCK_PLACEHOLDER, 1)
            continue

        # 安全：替換原始 fence 為遮蔽版本（保留 python language tag）
        masked_fence = f"```python\n{masked}\n```"
        sanitized = sanitized.replace(original_fence, masked_fence, 1)

    return sanitized
