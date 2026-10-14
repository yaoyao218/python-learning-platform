# 錯誤：遇到右括號直接看堆疊頂端，沒先檢查堆疊是否為空，開頭就是右括號時會 IndexError
class Solution:
    def isValid(self, s: str) -> bool:
        pairs = {")": "(", "]": "[", "}": "{"}
        stack = []
        for c in s:
            if c in pairs:
                if stack[-1] != pairs[c]:
                    return False
                stack.pop()
            else:
                stack.append(c)
        return not stack
