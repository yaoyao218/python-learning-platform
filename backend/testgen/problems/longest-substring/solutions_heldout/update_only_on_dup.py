# 錯誤：只在遇到重複字元時才更新答案，漏掉結尾的最後一個視窗
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen = set()
        left = best = 0
        for right, c in enumerate(s):
            if c in seen:
                best = max(best, right - left)
                while c in seen:
                    seen.discard(s[left])
                    left += 1
            seen.add(c)
        return best
