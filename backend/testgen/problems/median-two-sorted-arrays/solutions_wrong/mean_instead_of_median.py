# 錯誤：把中位數當成平均數，回傳全部數字的平均
from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = nums1 + nums2
        return sum(merged) / len(merged)
