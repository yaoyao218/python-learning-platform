# 錯誤：stack 清空後忘了放入新的基準點
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        stack = [-1]
        best = 0
        for i, c in enumerate(s):
            if c == '(':
                stack.append(i)
            elif stack:
                stack.pop()
                if stack:
                    best = max(best, i - stack[-1])
        return best
