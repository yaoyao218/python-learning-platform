# 題目定義。每個題目：title / difficulty / method（Solution 類別要呼叫的方法名）
# / description / examples / constraints / starter_code / ai_context / test_cases。
#
# ai_context 是給 AI 提示用的純文字題意（不含 HTML），取代舊版寫死在 ai.py 裡的
# 「題目：Longest Substring...」字串，讓 code-blind 提示系統可以套用到任何題目。
#
# test_cases 裡每筆測資用 "input"（單一字串參數，向後相容 testgen/ 既有工具）
# 或 "args"（多參數時用 tuple）二選一表示呼叫參數。

_LONGEST_SUBSTRING_CASES = [
    # LC 官方範例 1
    {"index":  1, "input": 'abcabcbb', "expected": 3, "is_stress": False},
    # LC 官方範例 2
    {"index":  2, "input": 'bbbbb', "expected": 1, "is_stress": False},
    # LC 官方範例 3
    {"index":  3, "input": 'pwwkew', "expected": 3, "is_stress": False},
    # v4: catch 5/6 from carry_kill      --prefix_len 1 --tail_le
    {"index":  4, "input": 'gogn', "expected": 3, "is_stress": False},
    # v4: catch 5/6 from carry_kill      --prefix_len 2 --tail_le
    {"index":  5, "input": 'qmjqztg', "expected": 6, "is_stress": False},
    # v4: catch 5/6 from carry_kill      --prefix_len 3 --tail_le
    {"index":  6, "input": 'zuxtzrhmqc', "expected": 9, "is_stress": False},
    # v4: catch 5/6 from doubled_distinct --n 6  --seed 12
    {"index":  7, "input": 'aabbccddeeff', "expected": 2, "is_stress": False},
    # v4: catch 6/6 from combo_kill      --n 2 --tail_len 5  --se
    {"index":  8, "input": 'mmiictscxgyvo', "expected": 8, "is_stress": False},
    # v4: catch 6/6 from combo_kill      --n 3 --tail_len 6  --se
    {"index":  9, "input": 'ttdduuycnysbaleg', "expected": 9, "is_stress": False},
    # v4: catch 6/6 from combo_kill      --n 3 --tail_len 8  --se
    {"index": 10, "input": 'rroouumszmdgjakhwc', "expected": 11, "is_stress": False},
    # v4: catch 6/6 from combo_kill      --n 4 --tail_len 6  --se
    {"index": 11, "input": 'hhjjiinnyduyskmrec', "expected": 9, "is_stress": False},
    # v4: catch 6/6 from random          --n 20 --seed 3   --alph
    {"index": 12, "input": 'beebcedfeaeadcebbfde', "expected": 5, "is_stress": False},
    # v4: catch 5/6 from doubled_distinct --n 10 --seed 14
    {"index": 13, "input": 'aabbccddeeffgghhiijj', "expected": 2, "is_stress": False},
    # v4: catch 6/6 from combo_kill      --n 4 --tail_len 10 --se
    {"index": 14, "input": 'ffbbuuccgqzgwisanldxtk', "expected": 13, "is_stress": False},
    # v4: catch 6/6 from combo_kill      --n 5 --tail_len 8  --se
    {"index": 15, "input": 'ddrrsskkhhbtxbanquoiym', "expected": 11, "is_stress": False},
    # v4: catch 6/6 from combo_kill      --n 3 --tail_len 12 --se
    {"index": 16, "input": 'wwzzooueyudmficvgrxnjp', "expected": 15, "is_stress": False},
    # v4: catch 6/6 from combo_kill      --n 5 --tail_len 10 --se
    {"index": 17, "input": 'qqccffzzkkidaiwntpherjlm', "expected": 13, "is_stress": False},
]

# 手動設計，涵蓋 LC 官方範例 + 邊界 + 壓力測試。
# index 4 = "("（stack 未清空 bug 在此掛）、index 5 = "([)]"（純計數 bug 在此掛）——
# 這兩個 index 是刻意調整過的：「stack 未清空」那版 bug 其實永遠回傳 True，
# 只要遇到任何一筆 expected=False 的測資就會第一時間掛掉，不可能撐到比
# 「純計數」bug 更後面的 index。
_VALID_PARENTHESES_CASES = [
    {"index":  1, "input": "()", "expected": True, "is_stress": False},
    {"index":  2, "input": "()[]{}", "expected": True, "is_stress": False},
    {"index":  3, "input": "{[]}", "expected": True, "is_stress": False},
    {"index":  4, "input": "(", "expected": False, "is_stress": False},
    {"index":  5, "input": "([)]", "expected": False, "is_stress": False},
    {"index":  6, "input": "", "expected": True, "is_stress": False},
    {"index":  7, "input": "]", "expected": False, "is_stress": False},
    {"index":  8, "input": "((()))", "expected": True, "is_stress": False},
    {"index":  9, "input": "(()", "expected": False, "is_stress": False},
    {"index": 10, "input": "([{}])", "expected": True, "is_stress": False},
    {"index": 11, "input": "}{", "expected": False, "is_stress": False},
    {"index": 12, "input": "(" * 1000 + ")" * 1000, "expected": True, "is_stress": True},
]

# 手動設計。nums1/nums2 用 args=(nums1, nums2) 表示。
# index 1 刻意放「忘記排序」bug 的觸發案例——它天生保證是「第一個失敗」，
# 因為它就是 index 1，不需要额外調整順序。
_MEDIAN_CASES = [
    {"index":  1, "args": ([1, 3], [2]), "expected": 2.0, "is_stress": False},
    {"index":  2, "args": ([1, 2], [3, 4]), "expected": 2.5, "is_stress": False},
    {"index":  3, "args": ([], [1]), "expected": 1.0, "is_stress": False},
    {"index":  4, "args": ([2], []), "expected": 2.0, "is_stress": False},
    {"index":  5, "args": ([0, 0], [0, 0]), "expected": 0.0, "is_stress": False},
    {"index":  6, "args": ([1, 3, 5], [2, 4, 6]), "expected": 3.5, "is_stress": False},
    {"index":  7, "args": ([1, 1, 1], [1, 1, 1]), "expected": 1.0, "is_stress": False},
    {"index":  8, "args": ([-5, -3, -1], [-4, -2, 0]), "expected": -2.5, "is_stress": False},
    {"index":  9, "args": ([1], [2, 3, 4, 5, 6]), "expected": 3.5, "is_stress": False},
    {"index": 10, "args": (list(range(0, 2000, 2)), list(range(1, 2000, 2))), "expected": 999.5, "is_stress": True},
    {"index": 11, "args": ([100000], [100000]), "expected": 100000.0, "is_stress": False},
]


PROBLEMS = {
    "longest-substring": {
        "title": "Longest Substring Without Repeating Characters",
        "difficulty": "medium",
        "method": "lengthOfLongestSubstring",
        "description": '給定一個字串 <code>s</code>，請找出不含重複字元的<strong>最長子字串</strong>的長度。',
        "ai_context": '給一個字串，找「不含重複字元的最長子字串」的長度。例如："abcabcbb" → 3，因為 "abc" 是最長的無重複子字串。',
        "examples": [
            {"input": 'abcabcbb', "output": 3, "explanation": '最長不重複子字串為 "abc"，長度為 3'},
            {"input": 'bbbbb',    "output": 1, "explanation": '最長子字串為 "b"，長度為 1'},
            {"input": 'pwwkew',   "output": 3, "explanation": '最長不重複子字串為 "wke"，長度為 3'},
        ],
        "constraints": [
            "0 ≤ s.length ≤ 5 × 10⁴",
            "s 只包含英文字母、數字、符號與空白字元",
        ],
        "starter_code": (
            "class Solution:\n"
            "    def lengthOfLongestSubstring(self, s: str) -> int:\n"
            "        # 在此撰寫你的解法\n"
            "        pass\n"
        ),
        "test_cases": _LONGEST_SUBSTRING_CASES,
    },
    "valid-parentheses": {
        "title": "Valid Parentheses",
        "difficulty": "easy",
        "method": "isValid",
        "description": (
            '給定一個只包含 <code>(</code>、<code>)</code>、<code>{</code>、'
            '<code>}</code>、<code>[</code>、<code>]</code> 的字串 <code>s</code>，'
            '判斷字串是否<strong>有效</strong>。有效字串需滿足：左括號必須用同類型的'
            '右括號閉合，且左括號必須以正確的順序閉合。'
        ),
        "ai_context": '給一個只含括號的字串，判斷括號是否成對且順序正確地閉合。例如："()[]{}" → true，"([)]" → false（順序錯誤）。',
        "examples": [
            {"input": '()',     "output": 'true',  "explanation": '一組小括號，順序正確'},
            {"input": '()[]{}', "output": 'true',  "explanation": '三種括號皆正確配對'},
            {"input": '(]',     "output": 'false', "explanation": '括號類型不匹配'},
        ],
        "constraints": [
            "1 ≤ s.length ≤ 10⁴",
            "s 僅由括號字元 '()[]{}' 組成",
        ],
        "starter_code": (
            "class Solution:\n"
            "    def isValid(self, s: str) -> bool:\n"
            "        # 在此撰寫你的解法\n"
            "        pass\n"
        ),
        "test_cases": _VALID_PARENTHESES_CASES,
    },
    "median-two-sorted-arrays": {
        "title": "Median of Two Sorted Arrays",
        "difficulty": "hard",
        "method": "findMedianSortedArrays",
        "description": (
            '給定兩個已排序的陣列 <code>nums1</code> 與 <code>nums2</code>，'
            '回傳這兩個陣列合併後的<strong>中位數</strong>。'
        ),
        "ai_context": '給兩個已排序的陣列，回傳合併後的中位數（浮點數）。例如：nums1=[1,3], nums2=[2] → 2.0（合併後為 [1,2,3]）。',
        "examples": [
            {"input": 'nums1 = [1,3], nums2 = [2]', "output": '2.0',
             "explanation": '合併後為 [1,2,3]，中位數為 2'},
            {"input": 'nums1 = [1,2], nums2 = [3,4]', "output": '2.5',
             "explanation": '合併後為 [1,2,3,4]，中位數為 (2+3)/2 = 2.5'},
        ],
        "constraints": [
            "nums1.length + nums2.length ≥ 1",
            "-10⁶ ≤ nums1[i], nums2[i] ≤ 10⁶",
            "nums1 與 nums2 皆已由小到大排序",
        ],
        "starter_code": (
            "from typing import List\n\n"
            "class Solution:\n"
            "    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:\n"
            "        # 在此撰寫你的解法\n"
            "        pass\n"
        ),
        "test_cases": _MEDIAN_CASES,
    },
}

# 向後相容別名：testgen/ 既有工具（run_eval.py、smoke_test.py 等）預設操作
# Longest Substring 這題，透過這兩個別名沿用舊的呼叫方式。
TEST_CASES = PROBLEMS["longest-substring"]["test_cases"]
METHOD = PROBLEMS["longest-substring"]["method"]
