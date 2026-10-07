# 錯誤：dict 版更新 left 時沒取 max，left 會往回跳（經典的 "abba" 錯誤）
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        last = {}
        left = best = 0
        for right, c in enumerate(s):
            if c in last:
                left = last[c] + 1
            last[c] = right
            best = max(best, right - left + 1)
        return best
