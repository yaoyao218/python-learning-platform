# 錯誤：配對完一次、堆疊變空時就提早回傳 True，沒有檢查後面的字元
class Solution:
    def isValid(self, s: str) -> bool:
        pairs = {")": "(", "]": "[", "}": "{"}
        stack = []
        for c in s:
            if c in pairs:
                if not stack or stack.pop() != pairs[c]:
                    return False
                if not stack:
                    return True
            else:
                stack.append(c)
        return not stack
