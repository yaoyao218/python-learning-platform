"""LC3 Longest Substring Without Repeating Characters — 輸入規格。

validate(args)    → 不合法時回傳原因字串，合法回傳 None（AI 提案的候選要先過這關）
random_args(rng)  → 隨機產生一組小型合法輸入（assess_problem 的一致性／等價性檢查用）
small_args()      → 窮舉所有小型合法輸入（估算 TNR 上限用）
"""
import itertools

MAX_LEN = 5 * 10 ** 4


def validate(args: tuple) -> str | None:
    if len(args) != 1:
        return f"需要 1 個參數（s），收到 {len(args)} 個"
    s = args[0]
    if not isinstance(s, str):
        return "s 必須是字串"
    if len(s) > MAX_LEN:
        return f"s 長度不能超過 {MAX_LEN}，收到 {len(s)}"
    # 題目限制：英文字母、數字、符號與空白 → 可列印的 ASCII
    bad = sorted({c for c in s if not 32 <= ord(c) < 127})
    if bad:
        return f"s 只能包含英文字母、數字、符號與空白，出現 {bad[:5]!r}"
    return None


def random_args(rng) -> tuple:
    return ("".join(rng.choice("abcde ") for _ in range(rng.randint(0, 12))),)


def small_args():
    for n in range(0, 8):
        for chars in itertools.product("abcd", repeat=n):
            yield ("".join(chars),)
