"""S+ 正解 3：暴力法 O(n^2)。對每個起點往後掃直到遇到重複。
邏輯最直觀，學生第一次寫常是這版。會在壓力測試（n=50000）TLE，
但 5 秒內小規模 case 都能過。"""


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        best = 0
        n = len(s)
        for i in range(n):
            seen = set()
            for j in range(i, n):
                if s[j] in seen:
                    break
                seen.add(s[j])
            best = max(best, len(seen))
        return best
