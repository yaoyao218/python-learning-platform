"""LC20 Valid Parentheses — 輸入規格。

validate(args)    → 不合法時回傳原因字串，合法回傳 None（AI 提案的候選要先過這關）
random_args(rng)  → 隨機產生一組小型合法輸入（一致性／等價性檢查用）
small_args()      → 窮舉所有小型合法輸入
"""
import itertools

MAX_LEN = 10 ** 4
MIN_LEN = 0   # 題目限制寫 1 ≤ 長度，但 problem.py 原有手寫測資含空字串（期望 True），保留它所以放寬為 0
CHARS = "()[]{}"


def validate(args: tuple) -> str | None:
    if len(args) != 1:
        return f"需要 1 個參數（s），收到 {len(args)} 個"
    s = args[0]
    if not isinstance(s, str):
        return "s 必須是字串"
    if not MIN_LEN <= len(s) <= MAX_LEN:
        return f"s 長度必須在 {MIN_LEN} 到 {MAX_LEN} 之間，收到 {len(s)}"
    bad = set(s) - set(CHARS)
    if bad:
        return f"s 只能包含 {CHARS}，收到 {sorted(bad)}"
    return None


def _balanced(rng, pairs: int) -> str:
    """隨機產生一個有效字串（純隨機字串幾乎都無效，有效的要另外產生）。"""
    if pairs == 0:
        return ""
    k = rng.randint(0, pairs - 1)
    o, c = rng.choice(["()", "[]", "{}"])
    return o + _balanced(rng, k) + c + _balanced(rng, pairs - 1 - k)


def random_args(rng) -> tuple:
    if rng.random() < 0.5:
        return (_balanced(rng, rng.randint(1, 5)),)
    return ("".join(rng.choice(CHARS) for _ in range(rng.randint(1, 10))),)


def small_args():
    for n in range(1, 6):
        for t in itertools.product(CHARS, repeat=n):
            yield ("".join(t),)
