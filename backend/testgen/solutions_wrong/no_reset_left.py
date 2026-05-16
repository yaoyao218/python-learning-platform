"""S- bug 4：遇到重複時 left 直接跳到 right，沒有逐步移除中間字元。
這在 'abba' 這類 case 會出錯：遇到第二個 a 時 left 跳到 3，但實際上
seen 還記著 'b'，下一輪 s[right]='a' 又會被認定重複錯亂。
這是 LC 3 教學裡最經典的陷阱之一。"""


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen = set()
        left = 0
        best = 0
        for right in range(len(s)):
            if s[right] in seen:
                seen = set()      # BUG: 直接清空，沒考慮殘留
                left = right
            seen.add(s[right])
            best = max(best, right - left + 1)
        return best
