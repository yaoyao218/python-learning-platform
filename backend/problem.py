# 題目定義。每個題目：title / difficulty / method（Solution 類別要呼叫的方法名）
# / description / examples / constraints / starter_code / ai_context / test_cases。
#
# ai_context 是給 AI 提示用的純文字題意（不含 HTML），取代舊版寫死在 ai.py 裡的
# 「題目：Longest Substring...」字串，讓 code-blind 提示系統可以套用到任何題目。
#
# test_cases 裡每筆測資用 "input"（單一字串參數，向後相容 testgen/ 既有工具）
# 或 "args"（多參數時用 tuple）二選一表示呼叫參數。

def _stress_input() -> str:
    """長度 = 題目限制上限 5×10⁴ 的壓力測資，擋掉 O(n²) 的寫法。

    不能只用 'a' * 50000 這種單調字串：count_unique、no_reset_left 等錯誤解
    在上面剛好會答對，反而拉低 TNR。這裡的結構是：
      "abab..." 填充（最長只有 2）
      + x y [10 個字元] y         ← 類似 'abba' 的陷阱，擋 no_reset_left
      + [68 個不重複字元]           ← 答案 79，不等於全字串的不重複字元數 82
    遇到重複就 break 的暴力解（S+ 的 brute_force.py）內圈最多跑約 80 步，仍可在時限內通過。
    """
    pool = [chr(c) for c in range(32, 127) if chr(c) not in "ab"]
    tail = pool[0] + pool[1] + "".join(pool[2:12]) + pool[1] + "".join(pool[12:80])
    return ("ab" * 25000)[:50000 - len(tail)] + tail


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
    # 手動加的壓力測試，見下方 _stress_input()
    {"index": 18, "input": _stress_input(), "expected": 79, "is_stress": True},
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

# 第 0 輪：只有 LC 官方範例（AI 輔助測資實驗的起點，見
# docs/superpowers/plans/2026-10-07-ai-assisted-testgen.md）。
# 單一參數是 list 時用 args=(prices,)，因為 judge 的截斷顯示只處理字串型的 "input"。
# 由 testgen/export_round_to_problem.py 從 r3_tests.json 產生：共 4 道，前 2 道為 LC 官方範例，其餘依輸入長度由短到長，壓力測資在最後。
_BEST_TIME_STOCK_CASES = [
    # LC 官方範例 1
    {"index": 1, "args": ([7, 1, 5, 3, 6, 4],), "expected": 5, "is_stress": False},
    # LC 官方範例 2
    {"index": 2, "args": ([7, 6, 4, 3, 1],), "expected": 0, "is_stress": False},
    # r3
    {"index": 3, "args": ([2, 5, 1, 6, 0, 7, 3, 8],), "expected": 8, "is_stress": False},
    # r3
    {"index": 4, "args": ([10, 1, 2, 3, 4, 5, 6, 7, 8, 9],), "expected": 8, "is_stress": False},
]

# 由 testgen/export_round_to_problem.py 從 r5_tests.json 產生：共 54 道，前 3 道為 LC 官方範例，其餘依輸入長度由短到長，壓力測資在最後。
_LONGEST_VALID_PARENTHESES_CASES = [
    # LC 官方範例 1
    {"index": 1, "input": '(()', "expected": 2, "is_stress": False},
    # LC 官方範例 2
    {"index": 2, "input": ')()())', "expected": 4, "is_stress": False},
    # LC 官方範例 3
    {"index": 3, "input": '', "expected": 0, "is_stress": False},
    # r5
    {"index": 4, "input": '(())()', "expected": 6, "is_stress": False},
    # r5
    {"index": 5, "input": '())(()', "expected": 2, "is_stress": False},
    # r5
    {"index": 6, "input": '(((())', "expected": 4, "is_stress": False},
    # r5
    {"index": 7, "input": ')()(()', "expected": 2, "is_stress": False},
    # r5
    {"index": 8, "input": '(())()()', "expected": 8, "is_stress": False},
    # r5
    {"index": 9, "input": '(()())(()', "expected": 6, "is_stress": False},
    # r5
    {"index": 10, "input": '()(())()(()', "expected": 8, "is_stress": False},
    # r5
    {"index": 11, "input": '())()(()())', "expected": 8, "is_stress": False},
    # r5
    {"index": 12, "input": '((())())(()', "expected": 8, "is_stress": False},
    # r5
    {"index": 13, "input": '(()())())(()', "expected": 8, "is_stress": False},
    # r5
    {"index": 14, "input": '())((()))()(', "expected": 8, "is_stress": False},
    # r5
    {"index": 15, "input": '(()())(()(()))(()', "expected": 14, "is_stress": False},
    # r5
    {"index": 16, "input": '(()))(()())())(()', "expected": 8, "is_stress": False},
    # r5
    {"index": 17, "input": '())()(()())()(()))', "expected": 14, "is_stress": False},
    # r5
    {"index": 18, "input": '())()(()())(()()))', "expected": 14, "is_stress": False},
    # r5
    {"index": 19, "input": ')()(()())(()())(()', "expected": 14, "is_stress": False},
    # r5
    {"index": 20, "input": '())(()())()(()))(()', "expected": 12, "is_stress": False},
    # r5
    {"index": 21, "input": '()(()))(()())(()())', "expected": 12, "is_stress": False},
    # r5
    {"index": 22, "input": '((())())(()(()))(()', "expected": 16, "is_stress": False},
    # r5
    {"index": 23, "input": '((())())(()))(()())', "expected": 12, "is_stress": False},
    # r5
    {"index": 24, "input": '(()())()(()(()))(()', "expected": 16, "is_stress": False},
    # r5
    {"index": 25, "input": '((()()))(()(()))(()', "expected": 16, "is_stress": False},
    # r5
    {"index": 26, "input": '()((()))()(()())(()', "expected": 16, "is_stress": False},
    # r5
    {"index": 27, "input": '((())())(()())())(()', "expected": 16, "is_stress": False},
    # r5
    {"index": 28, "input": '(()(()))()(()()))(()', "expected": 16, "is_stress": False},
    # r5
    {"index": 29, "input": '())((()))(()())(()))', "expected": 16, "is_stress": False},
    # r5
    {"index": 30, "input": '())()(()())((()))(()', "expected": 14, "is_stress": False},
    # r5
    {"index": 31, "input": ')()()((()))(()())(()', "expected": 16, "is_stress": False},
    # r5
    {"index": 32, "input": '((()()))(()))(()(()))', "expected": 12, "is_stress": False},
    # r5
    {"index": 33, "input": '((()))()(()))((())())', "expected": 12, "is_stress": False},
    # r5
    {"index": 34, "input": '(()))(()())()(()(()))', "expected": 16, "is_stress": False},
    # r5
    {"index": 35, "input": '(()(()))()()((()))(()', "expected": 18, "is_stress": False},
    # r5
    {"index": 36, "input": '())((()))()(()()))(()', "expected": 14, "is_stress": False},
    # r5
    {"index": 37, "input": '())((()))()(()))(()())', "expected": 12, "is_stress": False},
    # r5
    {"index": 38, "input": '())()()((()))(()())(()', "expected": 16, "is_stress": False},
    # r5
    {"index": 39, "input": '(()())((()))()(()))(()', "expected": 18, "is_stress": False},
    # r5
    {"index": 40, "input": '()(()))((()))(()())(()', "expected": 12, "is_stress": False},
    # r5
    {"index": 41, "input": '())((()))(()())()(()))', "expected": 18, "is_stress": False},
    # r5
    {"index": 42, "input": '()((()))(()())())(()())', "expected": 16, "is_stress": False},
    # r5
    {"index": 43, "input": '((())())()(()()))(()())', "expected": 16, "is_stress": False},
    # r5
    {"index": 44, "input": '())((()))()(()())(()())', "expected": 20, "is_stress": False},
    # r5
    {"index": 45, "input": '(()(()))()(()()))(()())', "expected": 16, "is_stress": False},
    # r5
    {"index": 46, "input": '(()())()((()))(()())(()', "expected": 20, "is_stress": False},
    # r5
    {"index": 47, "input": '())()(()())((()))(()())', "expected": 20, "is_stress": False},
    # r5
    {"index": 48, "input": '()(()())((()))(()()))(()', "expected": 20, "is_stress": False},
    # r5
    {"index": 49, "input": '(()())((()))()(()()))(()', "expected": 20, "is_stress": False},
    # r5
    {"index": 50, "input": '())()((()))(()())(()(()))', "expected": 22, "is_stress": False},
    # r5
    {"index": 51, "input": '()(()))((()))(()())(()())', "expected": 18, "is_stress": False},
    # r5
    {"index": 52, "input": '())((()))()(()())(()(()))', "expected": 22, "is_stress": False},
    # r5
    {"index": 53, "input": '(()(()))()(()()))((()))(()', "expected": 16, "is_stress": False},
    # r5
    {"index": 54, "input": '())()((()))(()())(()())(()', "expected": 20, "is_stress": False},
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
    "best-time-stock": {
        "title": "Best Time to Buy and Sell Stock",
        "difficulty": "easy",
        "method": "maxProfit",
        "description": (
            '給定一個陣列 <code>prices</code>，<code>prices[i]</code> 是某支股票第 i 天的價格。'
            '你只能選擇<strong>某一天買入</strong>，並在<strong>之後的某一天賣出</strong>。'
            '回傳你能獲得的最大利潤；如果無法獲利，回傳 <code>0</code>。'
        ),
        "ai_context": '給一個每日股價陣列，只能買一次、之後賣一次，求最大利潤，無法獲利回傳 0。例如：[7,1,5,3,6,4] → 5（第 2 天以 1 買入、第 5 天以 6 賣出）。',
        "examples": [
            {"input": 'prices = [7,1,5,3,6,4]', "output": 5,
             "explanation": '第 2 天（價格 1）買入、第 5 天（價格 6）賣出，利潤 6-1 = 5；不能先賣後買'},
            {"input": 'prices = [7,6,4,3,1]', "output": 0,
             "explanation": '價格一路下跌，沒有任何交易能獲利，回傳 0'},
        ],
        "constraints": [
            "1 ≤ prices.length ≤ 10⁵",
            "0 ≤ prices[i] ≤ 10⁴",
        ],
        "starter_code": (
            "from typing import List\n\n"
            "class Solution:\n"
            "    def maxProfit(self, prices: List[int]) -> int:\n"
            "        # 在此撰寫你的解法\n"
            "        pass\n"
        ),
        "test_cases": _BEST_TIME_STOCK_CASES,
    },
    "longest-valid-parentheses": {
        "title": "Longest Valid Parentheses",
        "difficulty": "hard",
        "method": "longestValidParentheses",
        "description": (
            '給定一個只包含 <code>(</code> 與 <code>)</code> 的字串 <code>s</code>，'
            '回傳<strong>最長的合法（括號正確配對）且連續的子字串</strong>的長度。'
        ),
        "ai_context": '給一個只含 ( 和 ) 的字串，找出「括號正確配對且連續」的最長子字串長度。例如：")()())" → 4（最長合法子字串是 "()()"）。',
        "examples": [
            {"input": '(()', "output": 2, "explanation": '最長合法子字串為 "()"'},
            {"input": ')()())', "output": 4, "explanation": '最長合法子字串為 "()()"'},
            {"input": '', "output": 0, "explanation": '空字串沒有合法子字串'},
        ],
        "constraints": [
            "0 ≤ s.length ≤ 3 × 10⁴",
            "s[i] 只會是 '(' 或 ')'",
        ],
        "starter_code": (
            "class Solution:\n"
            "    def longestValidParentheses(self, s: str) -> int:\n"
            "        # 在此撰寫你的解法\n"
            "        pass\n"
        ),
        "test_cases": _LONGEST_VALID_PARENTHESES_CASES,
    },
}

# 向後相容別名：testgen/ 既有工具（run_eval.py、smoke_test.py 等）預設操作
# Longest Substring 這題，透過這兩個別名沿用舊的呼叫方式。
TEST_CASES = PROBLEMS["longest-substring"]["test_cases"]
METHOD = PROBLEMS["longest-substring"]["method"]
