# 錯誤：偶數長度時用整數除法 // 取平均，2.5 變成 2
from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = sorted(nums1 + nums2)
        n = len(merged)
        if n % 2 == 1:
            return float(merged[n // 2])
        return float((merged[n // 2 - 1] + merged[n // 2]) // 2)
