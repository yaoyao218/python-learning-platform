"""S- bug 5：在內層迴圈遇到重複就直接 return，沒掃完整個字串。
這是 CLAUDE.md 裡明確提到的『return 縮排錯誤 / 迴圈提早終止』的典型版本。
ai.py 的 wrong_answer prompt 有特別提醒 AI 要檢查這個。"""


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        best = 0
        seen = set()
        for ch in s:
            if ch in seen:
                return best       # BUG: 一遇重複就提早結束
            seen.add(ch)
            best = len(seen)
        return best
