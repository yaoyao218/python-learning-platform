# 錯誤：分別算兩個陣列的中位數再取平均；其中一個是空陣列時只回傳另一個的中位數
from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        def median(nums):
            n = len(nums)
            if n % 2 == 1:
                return float(nums[n // 2])
            return (nums[n // 2 - 1] + nums[n // 2]) / 2
        if not nums1:
            return median(nums2)
        if not nums2:
            return median(nums1)
        return (median(nums1) + median(nums2)) / 2
