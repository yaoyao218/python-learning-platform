# 錯誤：固定在第一天買入，只找之後的最高價
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        return max(0, max(prices) - prices[0])
