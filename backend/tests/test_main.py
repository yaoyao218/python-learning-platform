import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from main import app
from problem import PROBLEMS

TEST_CASES = PROBLEMS["longest-substring"]["test_cases"]

CORRECT_CODE = """
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        char_map = {}
        left = 0
        result = 0
        for right, char in enumerate(s):
            if char in char_map and char_map[char] >= left:
                left = char_map[char] + 1
            char_map[char] = right
            result = max(result, right - left + 1)
        return result
"""


@pytest.mark.asyncio
async def test_submit_returns_all_results_and_hint():
    with patch("main.get_hint", new_callable=AsyncMock, return_value="測試提示"):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/submit", json={"code": CORRECT_CODE, "problem_id": "longest-substring"}
            )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "hint" in data
    assert len(data["results"]) == len(TEST_CASES)


@pytest.mark.asyncio
async def test_submit_hint_none_when_all_pass():
    with patch("main.get_hint", new_callable=AsyncMock, return_value=None):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/submit", json={"code": CORRECT_CODE, "problem_id": "longest-substring"}
            )

    assert response.status_code == 200
    assert response.json()["hint"] is None


@pytest.mark.asyncio
async def test_submit_unknown_problem_returns_404():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/submit", json={"code": CORRECT_CODE, "problem_id": "does-not-exist"}
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_problems_returns_all():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/problems")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    ids = {p["id"] for p in data}
    assert ids == {
        "longest-substring", "valid-parentheses", "median-two-sorted-arrays",
        "best-time-stock", "longest-valid-parentheses",
    }


@pytest.mark.asyncio
async def test_get_problem_detail():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/problems/valid-parentheses")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Valid Parentheses"
    assert data["difficulty"] == "easy"
    assert "starter_code" in data


@pytest.mark.asyncio
async def test_get_problem_detail_404():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/problems/does-not-exist")
    assert response.status_code == 404


# ── C2：虛擬碼（只有通過往返檢查的才回傳） ─────────────────────────────

@pytest.mark.asyncio
async def test_get_problem_includes_passed_pseudocode():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/problems/best-time-stock")
    data = response.json()
    assert set(data["pseudocode"]) == {"version", "text"}
    assert data["pseudocode"]["text"].strip()


@pytest.mark.asyncio
async def test_get_problem_without_pseudocode_has_no_field(monkeypatch):
    from problem import PROBLEMS
    problem = {k: v for k, v in PROBLEMS["valid-parentheses"].items() if k != "pseudocode"}
    monkeypatch.setitem(PROBLEMS, "valid-parentheses", problem)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/problems/valid-parentheses")
    assert "pseudocode" not in response.json()


def test_load_pseudocode_skips_unpassed(tmp_path):
    import json
    from problem import _load_pseudocode
    d = tmp_path / "demo"
    d.mkdir()
    (d / "pseudocode.json").write_text(json.dumps({"version": "v1", "text": "1. x", "passed": False}), encoding="utf-8")
    assert _load_pseudocode("demo", tmp_path) is None
    (d / "pseudocode.json").write_text(json.dumps({"version": "v1", "text": "1. x", "passed": True}), encoding="utf-8")
    assert _load_pseudocode("demo", tmp_path) == {"version": "v1", "text": "1. x"}
    assert _load_pseudocode("missing", tmp_path) is None
