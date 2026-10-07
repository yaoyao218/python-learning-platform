# 錯誤：只計算第一段「谷底到山頂」的利潤
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        i, n = 0, len(prices)
        while i + 1 < n and prices[i + 1] <= prices[i]:
            i += 1
        j = i
        while j + 1 < n and prices[j + 1] >= prices[j]:
            j += 1
        return prices[j] - prices[i]
