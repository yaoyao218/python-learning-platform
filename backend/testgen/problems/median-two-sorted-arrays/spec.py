"""LC4 Median of Two Sorted Arrays — 輸入規格。

validate(args)    → 不合法時回傳原因字串，合法回傳 None（AI 提案的候選要先過這關）
random_args(rng)  → 隨機產生一組小型合法輸入（一致性／等價性檢查用）
small_args()      → 窮舉所有小型合法輸入
"""
import itertools

MAX_VALUE = 10 ** 6


def validate(args: tuple) -> str | None:
    if len(args) != 2:
        return f"需要 2 個參數（nums1, nums2），收到 {len(args)} 個"
    for name, nums in zip(("nums1", "nums2"), args):
        if not isinstance(nums, list):
            return f"{name} 必須是 list"
        for x in nums:
            if not isinstance(x, int) or isinstance(x, bool):
                return f"{name} 只能包含整數，收到 {x!r}"
            if not -MAX_VALUE <= x <= MAX_VALUE:
                return f"{name} 的值必須在 ±{MAX_VALUE} 之間，收到 {x}"
        if nums != sorted(nums):
            return f"{name} 必須由小到大排序"
    if len(args[0]) + len(args[1]) < 1:
        return "nums1 與 nums2 的總長度至少為 1"
    return None


def random_args(rng) -> tuple:
    while True:
        a = sorted(rng.randint(-9, 9) for _ in range(rng.randint(0, 7)))
        b = sorted(rng.randint(-9, 9) for _ in range(rng.randint(0, 7)))
        if a or b:
            return (a, b)


def _sorted_lists(max_len: int, values: range):
    for n in range(max_len + 1):
        for t in itertools.combinations_with_replacement(values, n):
            yield list(t)


def small_args():
    lists = list(_sorted_lists(3, range(-1, 3)))
    for a in lists:
        for b in lists:
            if a or b:
                yield (a, b)
