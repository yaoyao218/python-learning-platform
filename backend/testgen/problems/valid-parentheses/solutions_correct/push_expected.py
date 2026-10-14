# 正解：遇到左括號就推入「期待的右括號」，遇到右括號時必須等於堆疊頂端，O(n)
class Solution:
    def isValid(self, s: str) -> bool:
        close_of = {"(": ")", "[": "]", "{": "}"}
        stack = []
        for c in s:
            if c in close_of:
                stack.append(close_of[c])
            elif not stack or stack.pop() != c:
                return False
        return len(stack) == 0
