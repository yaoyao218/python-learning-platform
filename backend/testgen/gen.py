"""gen.py — Python 測資生成器（取代論文中的 testlib C++ 生成器）。

每個 mode 對應一個函式，回傳測資字串。所有 mode 都接受 seed 參數
（即使不用隨機）以保持 API 一致，與論文中 testlib 的 registerGen 一樣
讓同一條命令可重現。

可用模式（每個都對應 baseline 分析中的某個漏洞）：

  random          隨機英文字母（基準）
  all_same        全部同一個字元（catch always_len / off_by_one）
  no_repeat       字典順序 N 個 distinct 字元（catch always_len：實際答案=n）
  doubled_distinct  'aabbccdd' 雙倍 distinct（KILLER：catch count_unique）
  abba_chain      'abbaCDDCeFFE...' 鏈式 ABBA（KILLER：catch no_reset_left）
  late_window     'aaa' + 'bcdefg'（KILLER：catch inner_return）
  alternating     'abababab'
  punctuation     隨機標點字元
  stress          壓力測試（n=50000）

執行：
    python -m testgen.gen --mode doubled_distinct --n 8 --seed 1
    python -m testgen.gen --mode abba_chain --repeats 4 --seed 2
"""
from __future__ import annotations
import argparse
import random
import string


def random_str(n: int, seed: int, alphabet: str = "abcdefghij") -> str:
    rng = random.Random(seed)
    return "".join(rng.choice(alphabet) for _ in range(n))


def all_same(n: int, seed: int, char: str = "a") -> str:
    return char * n


def no_repeat(n: int, seed: int) -> str:
    alphabet = string.ascii_lowercase
    if n <= 26:
        return alphabet[:n]
    # 超過 26 就重複序列，但保留前段 distinct
    return (alphabet * ((n // 26) + 1))[:n]


def doubled_distinct(n: int, seed: int) -> str:
    """'aabbccdd...' — set_size = n, 最長 no-repeat 永遠是 2。
    這是論文 anti-set 思維的 Python 版本，專殺 count_unique。
    參數 n 是雙倍對的個數（不是字串長度）。"""
    chars = string.ascii_lowercase[:n]
    return "".join(c * 2 for c in chars)


def abba_chain(repeats: int, seed: int) -> str:
    """'abba CDDC eFFe ...' — no_reset_left 在每個 ABBA 區段都會出錯。
    跟 baseline 案例 12 'abba' 同 pattern 但延伸到很多區段，
    且每段用不同字元組，避免互相干擾。"""
    rng = random.Random(seed)
    pool = list(string.ascii_lowercase)
    rng.shuffle(pool)
    out = []
    idx = 0
    for _ in range(repeats):
        a, b = pool[idx], pool[idx + 1]
        idx += 2
        if idx + 1 >= len(pool):  # 重抽
            rng.shuffle(pool); idx = 0
        out.append(a + b + b + a)
    return "".join(out)


def late_window(prefix_repeat: int, tail_len: int, seed: int) -> str:
    """'aaa' + 'bcdefg...' — 前段有 dup（inner_return 看到就回傳），
    但實際最長 no-repeat 在後段的長 distinct tail。"""
    prefix = "a" * prefix_repeat
    tail = string.ascii_lowercase[1 : 1 + tail_len]  # 跳過 'a' 避免衝突
    return prefix + tail


def alternating(n: int, seed: int) -> str:
    return ("ab" * (n // 2 + 1))[:n]


def punctuation(n: int, seed: int) -> str:
    rng = random.Random(seed)
    chars = "!@#$%^&*()"
    return "".join(rng.choice(chars) for _ in range(n))


def stress_same(n: int = 50000, seed: int = 0, char: str = "a") -> str:
    return char * n


def stress_random(n: int = 1000, seed: int = 0) -> str:
    return random_str(n, seed)



def carry_kill(prefix_len: int, tail_len: int, seed: int) -> str:
    """X + Y_1..Y_k + X + Z_1..Z_j 模式（KILLER：殺 no_reset_left）。
    正確 sliding window 遇第二個 X 時只丟掉前面的 X 並保留 Y_i，所以答案 = k+1+j。
    no_reset_left 整個清空，答案 = j+1。落差 = k = prefix_len。
    這是 baseline 中 'dvdf'（k=1）的一般化版本。"""
    rng = random.Random(seed)
    chars = list(string.ascii_lowercase)
    rng.shuffle(chars)
    X = chars[0]
    Ys = chars[1 : 1 + prefix_len]
    Zs = chars[1 + prefix_len : 1 + prefix_len + tail_len]
    return X + "".join(Ys) + X + "".join(Zs)



def combo_kill(n: int, tail_len: int, seed: int) -> str:
    """超級殺手：doubled_distinct 前綴 + carry_kill 中段 + 長 distinct 尾段。
    同一個字串可同時殺 count_unique / always_len / no_reset_left / inner_return。
    模式：'aabbcc...XYZX' + 長 distinct tail
      - doubled prefix 讓 set_size >> answer  → 殺 count_unique
      - 第一個 'a' 重複 → 殺 inner_return
      - XYZX carry pattern → 殺 no_reset_left（sliding 能保留 YZ，bug 全清空）
      - len(s) >> answer → 殺 always_len
    """
    rng = random.Random(seed)
    pool = list(string.ascii_lowercase)
    rng.shuffle(pool)
    # 雙倍前綴
    prefix_chars = pool[:n]
    prefix = "".join(c * 2 for c in prefix_chars)
    # carry pattern：X + Y + X，其中 X 跟 Y 都不在 prefix
    X = pool[n]
    Y = pool[n + 1]
    Z = pool[n + 2]
    carry = X + Y + Z + X
    # tail：跟前面都不衝突的 distinct 字元
    tail = "".join(pool[n + 3 : n + 3 + tail_len])
    return prefix + carry + tail


# 把每個 mode 映射到「合理參數名稱集合」，方便 synthesize.py 用 argparse
MODES = {
    "random":            random_str,
    "all_same":          all_same,
    "no_repeat":         no_repeat,
    "doubled_distinct":  doubled_distinct,
    "abba_chain":        abba_chain,
    "carry_kill":        carry_kill,
    "combo_kill":        combo_kill,
    "late_window":       late_window,
    "alternating":       alternating,
    "punctuation":       punctuation,
    "stress_same":       stress_same,
    "stress_random":     stress_random,
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=list(MODES))
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--repeats", type=int, default=4)
    p.add_argument("--prefix_repeat", type=int, default=3)
    p.add_argument("--prefix_len", type=int, default=3)
    p.add_argument("--tail_len", type=int, default=10)
    p.add_argument("--char", type=str, default="a")
    p.add_argument("--alphabet", type=str, default="abcdefghij")
    args = p.parse_args()

    # 依 mode 挑能用的參數丟進去
    if args.mode == "random":           print(random_str(args.n, args.seed, args.alphabet))
    elif args.mode == "all_same":       print(all_same(args.n, args.seed, args.char))
    elif args.mode == "no_repeat":      print(no_repeat(args.n, args.seed))
    elif args.mode == "doubled_distinct": print(doubled_distinct(n=args.n, seed=args.seed))
    elif args.mode == "abba_chain":     print(abba_chain(args.repeats, args.seed))
    elif args.mode == "carry_kill":     print(carry_kill(args.prefix_len, args.tail_len, args.seed))
    elif args.mode == "combo_kill":     print(combo_kill(args.n, args.tail_len, args.seed))
    elif args.mode == "late_window":    print(late_window(args.prefix_repeat, args.tail_len, args.seed))
    elif args.mode == "alternating":    print(alternating(args.n, args.seed))
    elif args.mode == "punctuation":    print(punctuation(args.n, args.seed))
    elif args.mode == "stress_same":    print(stress_same(args.n, args.seed, args.char))
    elif args.mode == "stress_random":  print(stress_random(args.n, args.seed))


if __name__ == "__main__":
    main()
