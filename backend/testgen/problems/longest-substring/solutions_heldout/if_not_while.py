# 錯誤：遇到重複字元時只移除視窗最左邊一個字元（用 if 而不是 while）
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen = set()
        left = best = 0
        for right, c in enumerate(s):
            if c in seen:
                seen.discard(s[left])
                left += 1
            seen.add(c)
            best = max(best, right - left + 1)
        return best
