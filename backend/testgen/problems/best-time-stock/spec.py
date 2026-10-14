"""LC121 Best Time to Buy and Sell Stock — 輸入規格。

validate(args)    → 不合法時回傳原因字串，合法回傳 None（AI 提案的候選要先過這關）
random_args(rng)  → 隨機產生一組小型合法輸入（assess_problem 的一致性／等價性檢查用）
small_args()      → 窮舉所有小型合法輸入（估算 TNR 上限用）
"""
import itertools

MAX_LEN = 10 ** 5
MAX_PRICE = 10 ** 4


def validate(args: tuple) -> str | None:
    if len(args) != 1:
        return f"需要 1 個參數（prices），收到 {len(args)} 個"
    prices = args[0]
    if not isinstance(prices, list):
        return "prices 必須是 list"
    if not 1 <= len(prices) <= MAX_LEN:
        return f"prices 長度必須在 1 到 {MAX_LEN} 之間，收到 {len(prices)}"
    for p in prices:
        if not isinstance(p, int) or isinstance(p, bool):
            return f"prices 只能包含整數，收到 {p!r}"
        if not 0 <= p <= MAX_PRICE:
            return f"價格必須在 0 到 {MAX_PRICE} 之間，收到 {p}"
    return None


def random_args(rng) -> tuple:
    return ([rng.randint(0, 9) for _ in range(rng.randint(1, 8))],)


def small_args():
    for n in range(1, 7):
        for prices in itertools.product(range(5), repeat=n):
            yield (list(prices),)
