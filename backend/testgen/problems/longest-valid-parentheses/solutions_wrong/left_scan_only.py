# 錯誤：只從左往右掃一次，漏掉左括號多出來的情況（如 "(()"）
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        left = right = best = 0
        for c in s:
            if c == '(':
                left += 1
            else:
                right += 1
            if left == right:
                best = max(best, 2 * left)
            elif right > left:
                left = right = 0
        return best
