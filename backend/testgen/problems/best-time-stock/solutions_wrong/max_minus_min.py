# 錯誤：直接回傳 max(prices) - min(prices)，忽略「必須先買後賣」的順序
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        return max(prices) - min(prices)
