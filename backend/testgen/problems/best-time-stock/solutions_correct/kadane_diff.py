# 正解：對每日價差做 Kadane 最大子陣列和，O(n)
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        cur = best = 0
        for i in range(1, len(prices)):
            cur = max(0, cur + prices[i] - prices[i - 1])
            best = max(best, cur)
        return best
