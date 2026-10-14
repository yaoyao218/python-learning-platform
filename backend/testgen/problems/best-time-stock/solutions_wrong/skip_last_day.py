# 錯誤：迴圈範圍少一天，最後一天從未被當作賣出日
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        lowest = prices[0]
        best = 0
        for i in range(len(prices) - 1):
            lowest = min(lowest, prices[i])
            best = max(best, prices[i] - lowest)
        return best
