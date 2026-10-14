# 錯誤：用 set 合併，把重複的數字去掉了
from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = sorted(set(nums1 + nums2))
        n = len(merged)
        if n % 2 == 1:
            return float(merged[n // 2])
        return (merged[n // 2 - 1] + merged[n // 2]) / 2
