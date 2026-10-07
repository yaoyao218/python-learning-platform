# 正解：雙層迴圈枚舉所有「先買後賣」的組合，O(n^2)
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        best = 0
        for i in range(len(prices)):
            for j in range(i + 1, len(prices)):
                best = max(best, prices[j] - prices[i])
        return best
