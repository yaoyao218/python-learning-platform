# 正解：暴力檢查每個偶數長度子字串是否合法，O(n^3)
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        def valid(t):
            depth = 0
            for c in t:
                depth += 1 if c == '(' else -1
                if depth < 0:
                    return False
            return depth == 0

        n = len(s)
        best = 0
        for i in range(n):
            for j in range(i + 2, n + 1, 2):
                if valid(s[i:j]):
                    best = max(best, j - i)
        return best
