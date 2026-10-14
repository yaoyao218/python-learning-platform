"""
cloze.py — 遮照填空：把標準答案的關鍵部分挖洞，做成學生連續卡關時才看到的填空題

設計見 docs/superpowers/specs/extension-plan.md 第 2 節：
挖洞的對象是**標準答案**（testgen registry 的參考解），不是學生程式；AI 全程不參與，
同一份標準答案每次挖出來的結果都一樣。

挖哪裡（依優先順序，取前 MAX_BLANKS 個、不重疊、同一行只挖一個）：
    1. if／while 的條件
    2. 迴圈內的變數更新（指定式右邊）
    3. for 的迴圈範圍（只挖函式呼叫，例如 range(len(s))，不挖單一變數）
    4. 不只是單一變數的 return 值
    5. 迴圈外的初始值（例如 stack = [-1]）
    6. 迴圈內呼叫的參數（例如 seen.add(s[right])）
太簡單的不挖：單一變數、常數、空容器（例如 return best、i += 1、seen = set()）。

空格寫成 ____1____（合法的變數名稱）：挖洞後的程式碼仍能被解析，但執行到空格就 NameError，
所以不會直接通過測資；把答案填回去會得到原本的標準答案。
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from functools import lru_cache

MAX_BLANKS = 5

BLANK_RE = re.compile(r"____(\d+)____")


def blank(n: int) -> str:
    return f"____{n}____"


@dataclass(frozen=True)
class Cloze:
    code: str                  # 挖洞後的程式碼（給學生）
    answers: tuple[str, ...]   # 第 n 個空格的原文（只在後端用，不送前端）
    original: str              # 去掉開頭說明後的標準答案


def strip_header(source: str) -> str:
    """去掉開頭的模組說明字串與註解（會寫出解法名稱，例如「正解（S*）：一次掃描…」）。"""
    lines = source.splitlines()
    tree = ast.parse(source)
    start = 0
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(getattr(tree.body[0], "value", None), ast.Constant) \
            and isinstance(tree.body[0].value.value, str):
        start = tree.body[0].end_lineno
    while start < len(lines) and (not lines[start].strip() or lines[start].lstrip().startswith("#")):
        start += 1
    return "\n".join(lines[start:]).rstrip() + "\n"


def _trivial(node: ast.AST) -> bool:
    """單一變數、常數、空容器（[]、{}、set()）太簡單，不挖。"""
    if isinstance(node, (ast.Name, ast.Constant)):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)) and not node.elts:
        return True
    if isinstance(node, ast.Dict) and not node.keys:
        return True
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in ("set", "list", "dict", "tuple") and not node.args and not node.keywords)


def _candidates(tree: ast.AST) -> list[tuple[int, ast.AST]]:
    """回傳 (優先順序, 要挖掉的節點)。"""
    out: list[tuple[int, ast.AST]] = []

    def visit(node: ast.AST, in_loop: bool) -> None:
        if isinstance(node, (ast.If, ast.While)):
            out.append((1, node.test))
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
            out.append((3, node.iter))
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)) and node.value is not None \
                and not _trivial(node.value):
            out.append((2 if in_loop else 5, node.value))
        if isinstance(node, ast.Return) and node.value is not None and not _trivial(node.value):
            out.append((4, node.value))
        if in_loop and isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            for arg in node.value.args:
                if not _trivial(arg):
                    out.append((6, arg))
        loop = in_loop or isinstance(node, (ast.For, ast.While))
        for child in ast.iter_child_nodes(node):
            visit(child, loop)

    visit(tree, False)
    return out


def _char_col(line: str, byte_col: int) -> int:
    """ast 的 col_offset 是 UTF-8 位元組位置，換成字元位置。"""
    return len(line.encode("utf-8")[:byte_col].decode("utf-8"))


def make_cloze(source: str, max_blanks: int = MAX_BLANKS) -> Cloze:
    original = strip_header(source)
    lines = original.splitlines()
    tree = ast.parse(original)

    chosen: list[ast.AST] = []
    used_lines: set[int] = set()
    for _, node in sorted(_candidates(tree), key=lambda c: (c[0], c[1].lineno, c[1].col_offset)):
        if len(chosen) >= max_blanks:
            break
        if node.lineno != node.end_lineno or node.lineno in used_lines:
            continue
        chosen.append(node)
        used_lines.add(node.lineno)

    chosen.sort(key=lambda n: (n.lineno, n.col_offset))
    answers = []
    for k, node in enumerate(chosen, 1):
        answers.append(ast.get_source_segment(original, node))
    # 從後面往前替換，前面的位置才不會跑掉
    for k, node in reversed(list(enumerate(chosen, 1))):
        i = node.lineno - 1
        line = lines[i]
        a, b = _char_col(line, node.col_offset), _char_col(line, node.end_col_offset)
        lines[i] = line[:a] + blank(k) + line[b:]
    return Cloze(code="\n".join(lines) + "\n", answers=tuple(answers), original=original)


def fill(code: str, answers: tuple[str, ...]) -> str:
    """把答案填回空格（測試用：填回去必須等於原本的標準答案）。"""
    return BLANK_RE.sub(lambda m: answers[int(m.group(1)) - 1], code)


@lru_cache(maxsize=None)
def cloze_for(problem_id: str) -> Cloze | None:
    """該題的填空題；沒有登記標準答案的題目回傳 None。"""
    from testgen import registry  # noqa: PLC0415  只有用到時才載入

    try:
        path = registry.reference_path(problem_id)
    except KeyError:
        return None
    if not path.exists():
        return None
    return make_cloze(path.read_text(encoding="utf-8"))
