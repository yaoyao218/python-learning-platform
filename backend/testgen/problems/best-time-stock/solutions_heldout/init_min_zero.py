# 錯誤：最低價初值設成 0 而不是第一天的價格
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        lowest = 0
        best = 0
        for p in prices:
            lowest = min(lowest, p)
            best = max(best, p - lowest)
        return best
