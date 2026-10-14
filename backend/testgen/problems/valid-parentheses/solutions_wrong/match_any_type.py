# 錯誤：遇到右括號只要堆疊不空就彈出，沒檢查括號種類是否相同
class Solution:
    def isValid(self, s: str) -> bool:
        stack = []
        for c in s:
            if c in ")]}":
                if not stack:
                    return False
                stack.pop()
            else:
                stack.append(c)
        return not stack
