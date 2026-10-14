# 錯誤：把所有上漲的價差加總，誤解成可以多次買賣
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        total = 0
        for i in range(len(prices) - 1):
            total += max(0, prices[i + 1] - prices[i])
        return total
