# 錯誤：沒有區分奇偶，一律回傳 merged[n // 2]；偶數長度時取到的是右邊那個中間值
from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = sorted(nums1 + nums2)
        return float(merged[len(merged) // 2])
