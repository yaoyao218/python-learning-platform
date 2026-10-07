# 錯誤：遇到多餘的 ')' 會重設起點，但沒處理結尾多出來、沒配對的 '('
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        stack = []
        best = 0
        start = 0
        for i, c in enumerate(s):
            if c == '(':
                stack.append(i)
            elif stack:
                stack.pop()
                best = max(best, i - start + 1)
            else:
                start = i + 1
        return best
