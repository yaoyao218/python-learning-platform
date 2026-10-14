# 錯誤：直接把兩個陣列接起來就取中位數，忘了接起來之後不一定有排序
from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = nums1 + nums2
        n = len(merged)
        if n % 2 == 1:
            return float(merged[n // 2])
        return (merged[n // 2 - 1] + merged[n // 2]) / 2
