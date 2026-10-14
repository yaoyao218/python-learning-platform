# 錯誤：偶數長度時取 merged[n // 2] 與 merged[n // 2 + 1]，中間兩個往右偏了一格
from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = sorted(nums1 + nums2)
        n = len(merged)
        if n % 2 == 1:
            return float(merged[n // 2])
        if n // 2 + 1 >= n:
            return float(merged[n // 2])
        return (merged[n // 2] + merged[n // 2 + 1]) / 2
