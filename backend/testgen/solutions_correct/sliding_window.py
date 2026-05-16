"""S+ 正解 1：經典 sliding window（用 set 維護當前視窗）。
這是 LeetCode 官方題解推薦寫法，O(n) 時間。"""


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen = set()
        left = 0
        best = 0
        for right in range(len(s)):
            while s[right] in seen:
                seen.remove(s[left])
                left += 1
            seen.add(s[right])
            best = max(best, right - left + 1)
        return best
