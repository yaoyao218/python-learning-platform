# 錯誤：以為有效字串一定是「兩兩相鄰配對」，只檢查第 0-1、2-3、… 個字元
class Solution:
    def isValid(self, s: str) -> bool:
        if len(s) % 2:
            return False
        for i in range(0, len(s), 2):
            if s[i:i + 2] not in ("()", "[]", "{}"):
                return False
        return True
