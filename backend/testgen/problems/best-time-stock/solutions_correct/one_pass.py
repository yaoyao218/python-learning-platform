# 正解（S*）：一次掃描，記錄目前為止的最低價與最大利潤，O(n)
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        lowest = prices[0]
        best = 0
        for p in prices:
            lowest = min(lowest, p)
            best = max(best, p - lowest)
        return best
