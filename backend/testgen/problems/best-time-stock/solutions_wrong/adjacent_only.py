# 錯誤：只比較相鄰兩天的價差，沒考慮隔好幾天再賣
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        best = 0
        for i in range(len(prices) - 1):
            best = max(best, prices[i + 1] - prices[i])
        return best
