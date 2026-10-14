# 錯誤：只計算單一配對區段的長度，沒把相鄰的合法區段（如 "()()"）接起來
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        stack = []
        best = 0
        for i, c in enumerate(s):
            if c == '(':
                stack.append(i)
            elif stack:
                best = max(best, i - stack.pop() + 1)
        return best
