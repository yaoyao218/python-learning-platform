# 正解：左右各掃一次，計數左右括號，O(n)、O(1) 空間
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        def scan(seq, opener):
            left = right = best = 0
            for c in seq:
                if c == opener:
                    left += 1
                else:
                    right += 1
                if left == right:
                    best = max(best, 2 * left)
                elif right > left:
                    left = right = 0
            return best

        return max(scan(s, '('), scan(s[::-1], ')'))
