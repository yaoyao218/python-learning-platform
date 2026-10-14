"""遮照填空（cloze.py）：extension-plan.md 第 2 節的環境測試——
填回原內容後測資全過；挖洞後的版本不會直接通過測資。"""
import pytest
from httpx import ASGITransport, AsyncClient

from cloze import BLANK_RE, MAX_BLANKS, fill, make_cloze, strip_header, cloze_for
from judge import judge
from main import app
from problem import PROBLEMS

PIDS = list(PROBLEMS)


@pytest.mark.parametrize("pid", PIDS)
def test_every_problem_has_a_cloze_with_numbered_blanks(pid):
    c = cloze_for(pid)
    assert c is not None
    assert 1 <= len(c.answers) <= MAX_BLANKS
    assert [int(n) for n in BLANK_RE.findall(c.code)] == list(range(1, len(c.answers) + 1))


@pytest.mark.parametrize("pid", PIDS)
def test_filling_back_gives_the_original(pid):
    c = cloze_for(pid)
    assert fill(c.code, c.answers) == c.original


@pytest.mark.asyncio
@pytest.mark.parametrize("pid", PIDS)
async def test_filled_back_passes_all_tests(pid):
    c = cloze_for(pid)
    results = await judge(fill(c.code, c.answers), pid)
    assert all(r["passed"] for r in results)


@pytest.mark.asyncio
@pytest.mark.parametrize("pid", PIDS)
async def test_cloze_itself_does_not_pass(pid):
    results = await judge(cloze_for(pid).code, pid)
    assert not all(r["passed"] for r in results)


def test_header_comments_and_docstring_are_removed():
    src = '"""S+ 正解：sliding window"""\n# 正解（S*）：說明\n\nclass Solution:\n    def f(self, s):\n        return len(s) + 1\n'
    assert strip_header(src).startswith("class Solution:")
    assert "正解" not in make_cloze(src).code


def test_trivial_parts_are_not_blanked():
    src = ("class Solution:\n    def f(self, xs):\n        seen = set()\n        best = 0\n"
           "        for x in xs:\n            best += 1\n        return best\n")
    assert make_cloze(src).answers == ()


@pytest.mark.asyncio
async def test_cloze_endpoint_sends_code_but_not_answers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/problems/best-time-stock/cloze")
        missing = await client.get("/problems/no-such-problem/cloze")
    assert r.status_code == 200
    data = r.json()
    assert set(data) == {"code", "blanks"}
    assert data["blanks"] == len(cloze_for("best-time-stock").answers)
    assert "min(lowest, p)" not in data["code"]
    assert missing.status_code == 404
