"""S- bug 3：sliding window 但長度算錯一個。
right - left 而非 right - left + 1 ⇒ 答案永遠少 1。
特別在 n=1 / 全相同字元（答案應該是 1）會明顯出錯。"""


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
            best = max(best, right - left)  # BUG: 少 +1
        return best
