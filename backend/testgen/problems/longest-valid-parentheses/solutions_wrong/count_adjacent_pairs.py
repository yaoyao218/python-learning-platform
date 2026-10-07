# 錯誤：只認相鄰的 "()"，不認巢狀的 "(())"
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        best = cur = 0
        i = 0
        while i < len(s) - 1:
            if s[i] == '(' and s[i + 1] == ')':
                cur += 2
                best = max(best, cur)
                i += 2
            else:
                cur = 0
                i += 1
        return best
