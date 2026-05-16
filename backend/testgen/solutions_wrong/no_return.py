"""S- bug 6：演算法正確，但忘了 return。
executor.py 會把這歸類為 error_type='no_return'，
觸發 ai.py 的 no_return 分支提示。判 0/18 通過。"""


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
        # BUG: 忘了 return best
