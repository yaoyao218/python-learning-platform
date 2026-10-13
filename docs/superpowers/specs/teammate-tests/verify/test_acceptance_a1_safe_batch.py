# -*- coding: utf-8 -*-
"""A1 安全批次執行器的驗收測試（負責人用）。

執行：
    python -m pytest docs/superpowers/specs/teammate-tests/verify/test_acceptance_a1_safe_batch.py -s -q
可選環境變數：VERIFY_SEED（固定隨機種子以便重現）、SAFE_BATCH_FILE（指定受測檔案）。

約定的介面（見 teammate-guide.md 的 A1 任務卡）：
    testgen/safe_batch.py
        ERR                         # 模組常數：該輸入出錯或沒跑到
        class BatchResult: outputs, status, timed_out_at, elapsed   # 屬性
        evaluate_solution(code, method, inputs, *, chunk_size=200, chunk_timeout=5.0,
                          total_timeout=120.0, max_output_bytes=1_000_000) -> BatchResult
        status ∈ {"ok","timeout","crash","too_much_output","forbidden","memory"}
"""
import ast
import inspect
import json
import re
import tempfile
import time
from pathlib import Path

import pytest

import _support as S

PROBLEMS = ["longest-substring", "best-time-stock", "longest-valid-parentheses"]


@pytest.fixture(scope="module")
def sb():
    if not S.IMPL_FILE.exists():
        pytest.fail(f"尚未實作：找不到 {S.IMPL_FILE}", pytrace=False)
    return S.load_module("sb_static", S.IMPL_FILE)


def seed_note():
    return f"（VERIFY_SEED={S.SEED}，可用同一個種子重現）"


# ---------------------------------------------------------------- 介面
def test_interface(sb):
    assert hasattr(sb, "ERR"), "缺少模組常數 ERR"
    assert hasattr(sb, "evaluate_solution"), "缺少 evaluate_solution"
    assert hasattr(sb, "BatchResult"), "缺少 BatchResult"
    sig = inspect.signature(sb.evaluate_solution)
    names = list(sig.parameters)
    assert names[:3] == ["code", "method", "inputs"], f"前三個參數應為 code, method, inputs，實際 {names[:3]}"
    for kw in ("chunk_size", "chunk_timeout", "total_timeout", "max_output_bytes"):
        assert kw in sig.parameters, f"缺少關鍵字參數 {kw}"
        assert sig.parameters[kw].kind is inspect.Parameter.KEYWORD_ONLY, f"{kw} 應為 keyword-only"


# ---------------------------------------------------------------- 靜態檢查
def test_no_exec_in_main_process(sb):
    src = S.IMPL_FILE.read_text(encoding="utf-8")
    tree = ast.parse(src)
    bad = [n.lineno for n in ast.walk(tree)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("exec", "eval", "compile")]
    assert not bad, f"safe_batch.py 在主程序程式碼中呼叫 exec/eval/compile（第 {bad} 行）；AI 程式只能在子程序執行"
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            imported.add((n.module or "").split(".")[0])
    assert imported & {"subprocess", "multiprocessing"}, "沒有使用 subprocess／multiprocessing"


def test_no_hardcoded_baseline(sb):
    src = S.IMPL_FILE.read_text(encoding="utf-8")
    data = json.loads(S.BASELINE_JSON.read_text(encoding="utf-8"))
    tokens = set()
    for prob in data["problems"].values():
        for pool in prob["fingerprints"].values():
            for name, fp in pool.items():
                tokens.add(fp["sha256_16"])
                tokens.add(name)
    hits = sorted(t for t in tokens if len(t) >= 6 and t in src)
    assert not hits, f"safe_batch.py 含有基準資料中的雜湊或解法名稱（疑似寫死）：{hits[:5]}"


# ---------------------------------------------------------------- 一致性（對照即時真值）
@pytest.mark.parametrize("pid", PROBLEMS)
def test_parity_with_live_oracle(sb, pid):
    from problem import PROBLEMS as P
    method = P[pid]["method"]
    inputs = S.make_inputs(pid)
    checked = 0
    for (kind, name), code in S.pools(pid).items():
        want = S.oracle_outputs(pid, code, inputs)
        got = S.call_impl(code, method, inputs, hard_timeout=180)
        assert got["status"] == "ok", f"{pid}/{kind}/{name}: status={got['status']} {seed_note()}"
        assert len(got["outputs"]) == len(inputs), f"{pid}/{kind}/{name}: 輸出筆數 {len(got['outputs'])} ≠ 輸入 {len(inputs)}"
        diff = [i for i in range(len(inputs)) if not S.same(want[i], got["outputs"][i])]
        assert not diff, (f"{pid}/{kind}/{name}: 與真值不一致 {len(diff)} 筆，例如輸入 {inputs[diff[0]]!r} "
                          f"真值 {want[diff[0]]!r} 實作 {got['outputs'][diff[0]]!r} {seed_note()}")
        checked += 1
    assert checked >= 6, "題庫的池數量異常"


def test_result_fields(sb):
    got = S.call_impl("class Solution:\n    def f(self, s):\n        return len(s)\n", "f", [("ab",), ("abc",)])
    assert all(got["fields"].values()), f"BatchResult 缺少欄位：{got['fields']}"
    assert got["status"] == "ok" and got["outputs"] == [2, 3]
    assert isinstance(got["elapsed_attr"], (int, float))


# ---------------------------------------------------------------- 惡意／異常程式
def test_infinite_loop_is_terminated(sb):
    code = "class Solution:\n    def f(self, s):\n        while True:\n            pass\n"
    t0 = time.time()
    got = S.call_impl(code, "f", [("a",)] * 5, hard_timeout=60, check_descendants=True,
                      chunk_size=2, chunk_timeout=2.0, total_timeout=6.0)
    assert got["status"] == "timeout", f"無窮迴圈應回報 timeout，實際 {got['status']}"
    assert got["wall"] < 6.0 + 8.0, f"應在約 total_timeout 內返回，實際 {got['wall']:.1f} 秒"
    assert len(got["outputs"]) == 5 and all(o == "__ERR__" for o in got["outputs"]), "沒跑完的輸入必須全部標為 ERR"
    assert got["descendants"] == [], f"逾時後仍有殘留的子程序：{got['descendants']}"


def test_partial_progress_is_kept(sb):
    # 前面的輸入正常，遇到特定輸入才卡住：已完成的塊必須保留
    code = ("class Solution:\n    def f(self, s):\n        if s == 'hang':\n            while True:\n                pass\n"
            "        return len(s)\n")
    inputs = [("a",), ("bb",), ("ccc",), ("hang",), ("dddd",), ("eeeee",)]
    got = S.call_impl(code, "f", inputs, hard_timeout=60, chunk_size=2, chunk_timeout=2.0, total_timeout=8.0)
    assert got["status"] == "timeout"
    assert got["outputs"][:2] == [1, 2], f"卡住之前已完成的塊必須保留，實際 {got['outputs'][:2]}"
    assert got["outputs"][3] == "__ERR__"


def test_exception_does_not_fail_batch(sb):
    code = ("class Solution:\n    def f(self, s):\n        if s == 'boom':\n            raise ValueError('x')\n"
            "        return len(s)\n")
    got = S.call_impl(code, "f", [("a",), ("boom",), ("bb",)])
    assert got["status"] == "ok"
    assert got["outputs"] == [1, "__ERR__", 2], f"單筆例外只影響該筆，實際 {got['outputs']}"


def test_output_flood_is_handled(sb):
    code = ("class Solution:\n    def f(self, s):\n        print('x' * 2_000_000)\n        return len(s)\n")
    got = S.call_impl(code, "f", [("a",), ("bb",), ("ccc",)], hard_timeout=60, max_output_bytes=100_000)
    assert got["status"] in ("too_much_output", "ok"), f"未預期的 status：{got['status']}"
    if got["status"] == "ok":
        assert got["outputs"] == [1, 2, 3], "若回報 ok，結果必須正確（程式自己 print 的內容不能混進答案）"


def test_forbidden_import_not_executed(sb):
    with tempfile.TemporaryDirectory() as d:
        marker = Path(d) / "pwned.txt"
        code = (f"import os\nopen(r'{marker}', 'w').write('x')\n"
                "class Solution:\n    def f(self, s):\n        return 1\n")
        got = S.call_impl(code, "f", [("a",)])
        assert got["status"] == "forbidden", f"含禁用模組的程式應回報 forbidden，實際 {got['status']}"
        assert not marker.exists(), "含禁用模組的程式被執行了（留下了檔案）"


def test_open_builtin_is_blocked_for_ai_code(sb):
    # 對應 A2：AI 程式路徑必須使用嚴格檢查（不能用 open 寫檔）
    with tempfile.TemporaryDirectory() as d:
        marker = Path(d) / "pwned2.txt"
        code = (f"class Solution:\n    def f(self, s):\n        open(r'{marker}', 'w').write('x')\n        return 1\n")
        got = S.call_impl(code, "f", [("a",)])
        assert not marker.exists(), "AI 程式用 open() 寫出了檔案；safe_batch 必須使用嚴格檢查（A2）"
        assert got["status"] in ("forbidden", "ok"), got["status"]
        if got["status"] == "ok":
            assert got["outputs"] == ["__ERR__"], "若沒有被擋，至少該輸入必須是錯誤，而不是正常回傳 1"


def test_input_not_shared_between_calls(sb):
    code = "class Solution:\n    def f(self, a):\n        a.append(0)\n        return len(a)\n"
    shared = [1]
    got = S.call_impl(code, "f", [(shared,), (shared,), ([1, 2],)])
    assert got["outputs"] == [2, 2, 3], f"每筆輸入必須獨立（參數不可被前一筆改動），實際 {got['outputs']}"


# ---------------------------------------------------------------- 效能（對照即時基準，不用寫死秒數）
def test_performance_within_5x_of_live_oracle(sb):
    pid = "longest-valid-parentheses"
    from problem import PROBLEMS as P
    method = P[pid]["method"]
    inputs = S.make_inputs(pid, n_random=20000, n_small=100000)
    codes = list(S.pools(pid).values())
    t0 = time.perf_counter()
    for c in codes:
        S.oracle_outputs(pid, c, inputs)
    base = time.perf_counter() - t0
    t0 = time.perf_counter()
    for c in codes:
        got = S.call_impl(c, method, inputs, hard_timeout=300)
        assert got["status"] == "ok"
    impl = time.perf_counter() - t0
    assert impl <= 5 * base + 3, f"實作 {impl:.1f} 秒 > 5×即時基準 {base:.1f} 秒 + 3 秒緩衝（{len(inputs)} 組輸入、{len(codes)} 份解法）"
