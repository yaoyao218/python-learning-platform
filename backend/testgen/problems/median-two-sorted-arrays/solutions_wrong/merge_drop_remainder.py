# 錯誤：雙指標合併時，其中一邊走完就停，忘了把另一邊剩下的元素接上
from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = []
        i = j = 0
        while i < len(nums1) and j < len(nums2):
            if nums1[i] <= nums2[j]:
                merged.append(nums1[i])
                i += 1
            else:
                merged.append(nums2[j])
                j += 1
        if not merged:
            merged = nums1 or nums2
        n = len(merged)
        if n % 2 == 1:
            return float(merged[n // 2])
        return (merged[n // 2 - 1] + merged[n // 2]) / 2
