# 錯誤：迴圈中配對都檢查了，但結尾沒檢查堆疊是否為空，多出的左括號被當成有效
class Solution:
    def isValid(self, s: str) -> bool:
        pairs = {")": "(", "]": "[", "}": "{"}
        stack = []
        for c in s:
            if c in pairs:
                if not stack or stack.pop() != pairs[c]:
                    return False
            else:
                stack.append(c)
        return True
