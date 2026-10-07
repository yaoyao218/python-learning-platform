# 錯誤：利潤初值設成第一天到第二天的差價，無法獲利時回傳負數而不是 0
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        if len(prices) < 2:
            return 0
        best = prices[1] - prices[0]
        lowest = prices[0]
        for p in prices[1:]:
            best = max(best, p - lowest)
            lowest = min(lowest, p)
        return best
