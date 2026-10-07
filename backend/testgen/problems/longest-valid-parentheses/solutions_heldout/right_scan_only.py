# 錯誤：只從右往左掃一次，漏掉右括號多出來的情況
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        left = right = best = 0
        for c in reversed(s):
            if c == ')':
                right += 1
            else:
                left += 1
            if left == right:
                best = max(best, 2 * left)
            elif left > right:
                left = right = 0
        return best
