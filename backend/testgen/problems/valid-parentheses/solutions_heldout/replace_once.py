# 錯誤：刪除相鄰配對只做一次，沒有反覆刪到不能再刪
class Solution:
    def isValid(self, s: str) -> bool:
        s = s.replace("()", "").replace("[]", "").replace("{}", "")
        return s == ""
