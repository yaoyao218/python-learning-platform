# 自動產出 — 由 testgen/export_to_problem_py.py 從 tests_v4 + LC 官方範例組成。
# 17 筆測資；首 3 筆為 LeetCode 官方範例（學生熱身用），
# 之後為論文方法收斂出的高鑑別度測資（catch>=5/6 的 S- bugs）。

TEST_CASES = [
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
