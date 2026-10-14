# 錯誤：以為有效字串一定左右對稱，只比對 s[i] 與 s[n-1-i] 是否配對
class Solution:
    def isValid(self, s: str) -> bool:
        pairs = {"(": ")", "[": "]", "{": "}"}
        n = len(s)
        if n % 2:
            return False
        for i in range(n // 2):
            if pairs.get(s[i]) != s[n - 1 - i]:
                return False
        return True
