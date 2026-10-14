# 正解：反覆刪掉相鄰的 ()、[]、{}，刪到不能再刪，最後是空字串就有效，O(n²)
class Solution:
    def isValid(self, s: str) -> bool:
        while True:
            t = s.replace("()", "").replace("[]", "").replace("{}", "")
            if t == s:
                return s == ""
            s = t
