# 錯誤：每種括號各自一個計數器，中途變負就無效；不同種類交錯（如 "([)]"）抓不到
class Solution:
    def isValid(self, s: str) -> bool:
        depth = {"(": 0, "[": 0, "{": 0}
        open_of = {")": "(", "]": "[", "}": "{"}
        for c in s:
            if c in depth:
                depth[c] += 1
            else:
                depth[open_of[c]] -= 1
                if depth[open_of[c]] < 0:
                    return False
        return all(v == 0 for v in depth.values())
