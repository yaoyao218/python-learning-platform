"""README.md 與 CLAUDE.md 的題目表要和 problem.PROBLEMS 一致。"""
import re
from pathlib import Path

import pytest

from problem import PROBLEMS

_ROOT = Path(__file__).resolve().parents[2]
_ROW = re.compile(r"^\| `([a-z0-9-]+)` \|[^|]*\|[^|]*\| (\d+) \|", re.MULTILINE)


@pytest.mark.parametrize("doc", ["README.md", "CLAUDE.md"])
def test_problem_table_matches_registry(doc):
    rows = dict(_ROW.findall((_ROOT / doc).read_text(encoding="utf-8")))
    expected = {pid: str(len(p["test_cases"])) for pid, p in PROBLEMS.items()}
    assert rows == expected
