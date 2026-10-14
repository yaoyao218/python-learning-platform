# 錯誤：計算全部能配對的括號數 × 2，沒要求子字串必須連續
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        open_count = pairs = 0
        for c in s:
            if c == '(':
                open_count += 1
            elif open_count:
                open_count -= 1
                pairs += 1
        return 2 * pairs
