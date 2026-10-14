# 錯誤：雙指標合併後只接上 nums1 剩下的元素，忘了 nums2 也可能有剩
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
        merged.extend(nums1[i:])
        if not merged:
            merged = nums2
        n = len(merged)
        if n % 2 == 1:
            return float(merged[n // 2])
        return (merged[n // 2 - 1] + merged[n // 2]) / 2
