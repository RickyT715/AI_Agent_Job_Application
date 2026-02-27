"""Tests for the matches API router."""

import pytest
from httpx import AsyncClient


class TestListMatches:
    """Tests for GET /api/matches."""

    async def test_list_matches_sorted_by_score(self, seeded_client: AsyncClient):
        resp = await seeded_client.get("/api/matches")
        assert resp.status_code == 200
        data = resp.json()
        scores = [m["overall_score"] for m in data["items"]]
        assert scores == sorted(scores, reverse=True)

    async def test_list_matches_with_min_score_filter(self, seeded_client: AsyncClient):
        resp = await seeded_client.get("/api/matches", params={"min_score": 8.0})
        assert resp.status_code == 200
        data = resp.json()
        for match in data["items"]:
            assert match["overall_score"] >= 8.0

    async def test_list_matches_pagination(self, seeded_client: AsyncClient):
        resp = await seeded_client.get("/api/matches", params={"limit": 2, "offset": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5


class TestGetMatch:
    """Tests for GET /api/matches/{id}."""

    async def test_get_match_detail(self, seeded_client: AsyncClient):
        list_resp = await seeded_client.get("/api/matches", params={"limit": 1})
        match_id = list_resp.json()["items"][0]["id"]
        resp = await seeded_client.get(f"/api/matches/{match_id}")
        assert resp.status_code == 200
        detail = resp.json()
        assert "reasoning" in detail
        assert "missing_skills" in detail
        assert "strengths" in detail

    async def test_get_match_not_found(self, seeded_client: AsyncClient):
        resp = await seeded_client.get("/api/matches/99999")
        assert resp.status_code == 404


class TestMatchActions:
    """Tests for match action endpoints."""

    async def test_trigger_matching(self, client: AsyncClient):
        resp = await client.post("/api/matches/run")
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"

    async def test_rescore_match(self, seeded_client: AsyncClient):
        list_resp = await seeded_client.get("/api/matches", params={"limit": 1})
        match_id = list_resp.json()["items"][0]["id"]
        resp = await seeded_client.post(f"/api/matches/{match_id}/rescore")
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"
