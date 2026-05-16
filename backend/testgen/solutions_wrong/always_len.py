"""S- bug 2：偷懶解，直接回傳字串長度。
僅在『字串本身就沒有重複』時答對（即 LC 範例 abcdefg）。"""


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        return len(s)
