# 錯誤：回傳最大巢狀深度 × 2，把「深度」誤當成「長度」
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        depth = deepest = 0
        for c in s:
            depth = depth + 1 if c == '(' else max(0, depth - 1)
            deepest = max(deepest, depth)
        return 2 * deepest
