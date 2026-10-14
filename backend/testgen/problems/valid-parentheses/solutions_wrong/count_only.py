# 錯誤：只檢查三種括號的左右數量各自相等，忽略順序
class Solution:
    def isValid(self, s: str) -> bool:
        return (s.count("(") == s.count(")") and s.count("[") == s.count("]")
                and s.count("{") == s.count("}"))
