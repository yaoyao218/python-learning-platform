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
async def test_list_problems_returns_three():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/problems")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    ids = {p["id"] for p in data}
    assert ids == {"longest-substring", "valid-parentheses", "median-two-sorted-arrays"}


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
