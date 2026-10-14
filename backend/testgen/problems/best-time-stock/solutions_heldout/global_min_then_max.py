# 錯誤：先找全域最低價，只看它之後的最高價（最佳買點不一定是全域最低）
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        i = prices.index(min(prices))
        return max(prices[i:]) - prices[i]
