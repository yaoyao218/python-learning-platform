"""test_export_round.py — testgen/export_round_to_problem.py 的單元測試。

全部使用暫存的 problem.py 複本，不會動到真正的 backend/problem.py。
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from testgen import export_round_to_problem as ex   # noqa: E402

ARGS_SOURCE = '''# header
# 第 0 輪：只有 LC 官方範例。
_BEST_TIME_STOCK_CASES = [
    # LC 官方範例 1
    {"index": 1, "args": ([7, 1, 5, 3, 6, 4],), "expected": 5, "is_stress": False},
    # LC 官方範例 2
    {"index": 2, "args": ([7, 6, 4, 3, 1],), "expected": 0, "is_stress": False},
]

PROBLEMS = {}
'''

INPUT_SOURCE = '''_LONGEST_VALID_PARENTHESES_CASES = [
    # LC 官方範例 1
    {"index": 1, "input": "(()", "expected": 2, "is_stress": False},
    # LC 官方範例 2
    {"index": 2, "input": ")()())", "expected": 4, "is_stress": False},
    # LC 官方範例 3
    {"index": 3, "input": "", "expected": 0, "is_stress": False},
    # 我的備註
    {"index": 4, "input": "()", "expected": 2, "is_stress": False},
]
'''


def load_list(text: str, name: str):
    ns: dict = {}
    exec(text, ns)
    return ns[name]


# ---------------------------------------------------------------- 排序與格式
def test_ordering_official_first_then_short_to_long_then_stress_last():
    new = [
        {"index": 1, "args": [[7, 1, 5, 3, 6, 4]], "expected": 5, "is_stress": False},
        {"index": 2, "args": [[7, 6, 4, 3, 1]], "expected": 0, "is_stress": False},
        {"index": 3, "args": [[1, 2, 3, 4, 5, 6, 7, 8]], "expected": 7, "is_stress": False},
        {"index": 4, "args": [[3, 1]], "expected": 0, "is_stress": False},
        {"index": 5, "args": [list(range(1000))], "expected": 999, "is_stress": True},
        {"index": 6, "args": [[2, 4, 1]], "expected": 2, "is_stress": False},
    ]
    for c in new:
        c["args"] = tuple(c["args"])
    text, info = ex.build_new_source(ARGS_SOURCE, "best-time-stock", new, official=2, round_no=1)
    cases = load_list(text, "_BEST_TIME_STOCK_CASES")
    assert [c["index"] for c in cases] == [1, 2, 3, 4, 5, 6]
    sizes = [len(c["args"][0]) for c in cases]
    assert sizes[:2] == [6, 5], "前 K 道官方範例必須保持原順序"
    assert sizes[2:5] == sorted(sizes[2:5]) == [2, 3, 8], "其餘非壓力測資由短到長"
    assert cases[-1]["is_stress"] is True, "壓力測資在最後"
    assert info["total"] == 6 and info["stress"] == 1 and info["style"] == "args"


def test_style_follows_existing_block_input_vs_args():
    # 候選以 args 形式出現，但這一題現有寫法是 input → 必須轉成 input
    new = [
        {"index": 1, "input": "(()", "expected": 2, "is_stress": False},
        {"index": 2, "input": ")()())", "expected": 4, "is_stress": False},
        {"index": 3, "input": "", "expected": 0, "is_stress": False},
        {"index": 4, "input": "()", "expected": 2, "is_stress": False},
        {"index": 5, "args": ("(())",), "expected": 4, "is_stress": False},
    ]
    text, _ = ex.build_new_source(INPUT_SOURCE, "longest-valid-parentheses", new, official=3, round_no=2)
    cases = load_list(text, "_LONGEST_VALID_PARENTHESES_CASES")
    assert all("input" in c and "args" not in c for c in cases)
    assert [c["input"] for c in cases][-2:] == ["()", "(())"]


def test_existing_comments_are_kept_and_new_ones_marked():
    new = [
        {"index": 1, "input": "(()", "expected": 2, "is_stress": False},
        {"index": 2, "input": ")()())", "expected": 4, "is_stress": False},
        {"index": 3, "input": "", "expected": 0, "is_stress": False},
        {"index": 4, "input": "()", "expected": 2, "is_stress": False},
        {"index": 5, "input": "(())", "expected": 4, "is_stress": False},
    ]
    text, _ = ex.build_new_source(INPUT_SOURCE, "longest-valid-parentheses", new, official=3, round_no=2)
    assert "# 我的備註" in text, "現有案例前面的註解要保留"
    assert "# r2" in text, "新案例要標示來自哪一輪"
    assert "# LC 官方範例 3" in text


def test_stale_header_comment_is_replaced_not_duplicated():
    new = [{"index": 1, "args": ([7, 1, 5, 3, 6, 4],), "expected": 5, "is_stress": False},
           {"index": 2, "args": ([7, 6, 4, 3, 1],), "expected": 0, "is_stress": False}]
    text, _ = ex.build_new_source(ARGS_SOURCE, "best-time-stock", new, official=2, round_no=1)
    assert "第 0 輪" not in text
    assert text.count("# 由 testgen/export_round_to_problem.py") == 1
    text2, _ = ex.build_new_source(text, "best-time-stock", new, official=2, round_no=1)
    assert text2.count("# 由 testgen/export_round_to_problem.py") == 1


def test_idempotent():
    new = [
        {"index": 1, "input": "(()", "expected": 2, "is_stress": False},
        {"index": 2, "input": ")()())", "expected": 4, "is_stress": False},
        {"index": 3, "input": "", "expected": 0, "is_stress": False},
        {"index": 4, "input": "()", "expected": 2, "is_stress": False},
        {"index": 5, "input": "(())", "expected": 4, "is_stress": False},
    ]
    once, _ = ex.build_new_source(INPUT_SOURCE, "longest-valid-parentheses", new, official=3, round_no=2)
    twice, _ = ex.build_new_source(once, "longest-valid-parentheses", new, official=3, round_no=2)
    assert once == twice


# ---------------------------------------------------------------- 保護
def test_refuses_when_official_prefix_does_not_match():
    new = [{"index": 1, "args": ([1, 2],), "expected": 1, "is_stress": False},
           {"index": 2, "args": ([7, 6, 4, 3, 1],), "expected": 0, "is_stress": False}]
    with pytest.raises(SystemExit):
        ex.build_new_source(ARGS_SOURCE, "best-time-stock", new, official=2, round_no=1)


def test_refuses_to_drop_existing_cases_unless_allowed():
    # 這一輪缺少 problem.py 目前的「()」→ 會被丟掉
    new = [
        {"index": 1, "input": "(()", "expected": 2, "is_stress": False},
        {"index": 2, "input": ")()())", "expected": 4, "is_stress": False},
        {"index": 3, "input": "", "expected": 0, "is_stress": False},
    ]
    with pytest.raises(SystemExit) as e:
        ex.build_new_source(INPUT_SOURCE, "longest-valid-parentheses", new, official=3, round_no=2)
    assert "allow-drop" in str(e.value)
    text, _ = ex.build_new_source(INPUT_SOURCE, "longest-valid-parentheses", new, official=3, round_no=2, allow_drop=True)
    assert len(load_list(text, "_LONGEST_VALID_PARENTHESES_CASES")) == 3


def test_refuses_duplicates():
    new = [
        {"index": 1, "input": "(()", "expected": 2, "is_stress": False},
        {"index": 2, "input": ")()())", "expected": 4, "is_stress": False},
        {"index": 3, "input": "", "expected": 0, "is_stress": False},
        {"index": 4, "input": "()", "expected": 2, "is_stress": False},
        {"index": 5, "input": "()", "expected": 2, "is_stress": False},
    ]
    with pytest.raises(SystemExit):
        ex.build_new_source(INPUT_SOURCE, "longest-valid-parentheses", new, official=3, round_no=2)


def test_refuses_official_larger_than_cases():
    new = [{"index": 1, "input": "(()", "expected": 2, "is_stress": False}]
    with pytest.raises(SystemExit):
        ex.build_new_source(INPUT_SOURCE, "longest-valid-parentheses", new, official=3, round_no=2, allow_drop=True)


def test_missing_block_is_reported():
    with pytest.raises(SystemExit):
        ex.build_new_source("x = 1\n", "best-time-stock", [], official=0, round_no=1)


def test_only_the_target_block_changes():
    new = [{"index": 1, "args": ([7, 1, 5, 3, 6, 4],), "expected": 5, "is_stress": False},
           {"index": 2, "args": ([7, 6, 4, 3, 1],), "expected": 0, "is_stress": False},
           {"index": 3, "args": ([1, 2],), "expected": 1, "is_stress": False}]
    text, _ = ex.build_new_source(ARGS_SOURCE, "best-time-stock", new, official=2, round_no=1)
    assert text.rstrip().endswith("PROBLEMS = {}")
    assert text.startswith("# header")


# ---------------------------------------------------------------- 命令列：預設不寫檔，--write 才寫
def run_cli(tmp_path: Path, extra: list[str]):
    problem_file = tmp_path / "problem.py"
    problem_file.write_text(ARGS_SOURCE, encoding="utf-8")
    tests_json = tmp_path / "r1_tests.json"
    tests_json.write_text(json.dumps({"cases": [
        {"index": 1, "args": [[7, 1, 5, 3, 6, 4]], "expected": 5, "is_stress": False},
        {"index": 2, "args": [[7, 6, 4, 3, 1]], "expected": 0, "is_stress": False},
        {"index": 3, "args": [[1, 5]], "expected": 4, "is_stress": False},
    ]}), encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "testgen.export_round_to_problem", "--problem", "best-time-stock", "--round", "1",
                        "--official", "2", "--problem-file", str(problem_file), "--tests-json", str(tests_json), *extra],
                       cwd=BACKEND, capture_output=True, text=True, encoding="utf-8")
    return r, problem_file


def test_cli_default_does_not_write(tmp_path):
    r, problem_file = run_cli(tmp_path, [])
    assert r.returncode == 0, r.stderr
    assert problem_file.read_text(encoding="utf-8") == ARGS_SOURCE
    assert "沒有寫檔" in r.stdout


def test_cli_write_and_second_run_has_no_diff(tmp_path):
    r, problem_file = run_cli(tmp_path, ["--write"])
    assert r.returncode == 0, r.stderr
    assert len(load_list(problem_file.read_text(encoding="utf-8"), "_BEST_TIME_STOCK_CASES")) == 3
    r2 = subprocess.run([sys.executable, "-m", "testgen.export_round_to_problem", "--problem", "best-time-stock", "--round", "1",
                         "--official", "2", "--problem-file", str(problem_file), "--tests-json", str(tmp_path / "r1_tests.json")],
                        cwd=BACKEND, capture_output=True, text=True, encoding="utf-8")
    assert "沒有差異" in r2.stdout


# ---------------------------------------------------------------- 真實資料：不應該把 problem.py 現有案例丟掉（只讀）
def _latest_round(pid):
    from testgen import rounds
    return max(int(f.name[1:-len("_tests.json")]) for f in rounds.rounds_dir(pid).glob("r*_tests.json"))


@pytest.mark.parametrize("pid,official", [("longest-valid-parentheses", 3), ("best-time-stock", 2)])
def test_real_rounds_contain_current_problem_cases(pid, official):
    # 用該題最新一輪：舊輪次本來就不含之後才加進 problem.py 的案例
    from testgen import rounds
    rnd = _latest_round(pid)
    cases = rounds.load_round_tests(pid, rnd)["cases"]
    source = (BACKEND / "problem.py").read_text(encoding="utf-8")
    text, info = ex.build_new_source(source, pid, cases, official, rnd)
    assert info["total"] >= info["previous_total"]
