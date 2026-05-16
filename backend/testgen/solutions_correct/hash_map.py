"""S+ 正解 2：用 dict 紀錄每個字元最後出現的 index，發現重複直接跳。
比 sliding_window.py 多一個常數倍速度，邏輯不同但結果一致。"""


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        last = {}
        left = 0
        best = 0
        for right, ch in enumerate(s):
            if ch in last and last[ch] >= left:
                left = last[ch] + 1
            last[ch] = right
            best = max(best, right - left + 1)
        return best
