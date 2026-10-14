"""LC32 Longest Valid Parentheses — 輸入規格。

validate(args)    → 不合法時回傳原因字串，合法回傳 None（AI 提案的候選要先過這關）
random_args(rng)  → 隨機產生一組小型合法輸入（assess_problem 的一致性／等價性檢查用）
small_args()      → 窮舉所有小型合法輸入（估算 TNR 上限用）
"""
import itertools

MAX_LEN = 3 * 10 ** 4


def validate(args: tuple) -> str | None:
    if len(args) != 1:
        return f"需要 1 個參數（s），收到 {len(args)} 個"
    s = args[0]
    if not isinstance(s, str):
        return "s 必須是字串"
    if len(s) > MAX_LEN:
        return f"s 長度不能超過 {MAX_LEN}，收到 {len(s)}"
    if set(s) - {"(", ")"}:
        return f"s 只能包含 '(' 與 ')'，出現 {sorted(set(s) - {'(', ')'})}"
    return None


def random_args(rng) -> tuple:
    return ("".join(rng.choice("()") for _ in range(rng.randint(0, 12))),)


def small_args():
    for n in range(0, 13):
        for chars in itertools.product("()", repeat=n):
            yield ("".join(chars),)
