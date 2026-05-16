"""S- bug 1：誤把題目讀成「不重複字元的總數」。
直接回傳 len(set(s))。在『沒有重複字元的字串』case 上會剛好答對。"""


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return len(set(s))
