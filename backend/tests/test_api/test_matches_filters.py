"""Tests for match list filtering (q, location, workplace_type)."""

from httpx import AsyncClient


class TestMatchFilters:
    """Tests for GET /api/matches with filter parameters."""

    async def test_list_matches_returns_all(self, seeded_client: AsyncClient):
        """Returns all matches when no filters applied."""
        resp = await seeded_client.get("/api/matches")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    async def test_list_matches_ordered_by_score_desc(self, seeded_client: AsyncClient):
        """Matches are returned sorted by overall_score descending."""
        resp = await seeded_client.get("/api/matches")
        items = resp.json()["items"]
        scores = [item["overall_score"] for item in items]
        assert scores == sorted(scores, reverse=True)

    async def test_filter_by_min_score(self, seeded_client: AsyncClient):
        """Filter matches by minimum score."""
        resp = await seeded_client.get("/api/matches", params={"min_score": 9.0})
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["overall_score"] >= 9.0

    async def test_filter_by_q_title(self, seeded_client: AsyncClient):
        """Filter matches by text search in job title."""
        resp = await seeded_client.get("/api/matches", params={"q": "Engineer 0"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            job = item["job"]
            title_or_desc = (job["title"] + " " + job["description"]).lower()
            assert "engineer 0" in title_or_desc

    async def test_filter_by_q_no_results(self, seeded_client: AsyncClient):
        """Text search returns empty when no match."""
        resp = await seeded_client.get("/api/matches", params={"q": "nonexistentxyz"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_filter_by_location(self, seeded_client: AsyncClient):
        """Filter matches by job location."""
        resp = await seeded_client.get("/api/matches", params={"location": "Remote"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert "remote" in (item["job"]["location"] or "").lower()

    async def test_filter_by_location_nyc(self, seeded_client: AsyncClient):
        """Filter matches by NYC location."""
        resp = await seeded_client.get("/api/matches", params={"location": "NYC"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert "nyc" in (item["job"]["location"] or "").lower()

    async def test_filter_by_workplace_type(self, seeded_client: AsyncClient):
        """Filter matches by workplace type."""
        resp = await seeded_client.get("/api/matches", params={"workplace_type": "remote"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["job"]["workplace_type"] == "remote"

    async def test_filter_by_workplace_type_onsite(self, seeded_client: AsyncClient):
        """Filter matches by onsite workplace type."""
        resp = await seeded_client.get("/api/matches", params={"workplace_type": "onsite"})
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["job"]["workplace_type"] == "onsite"

    async def test_combined_filters(self, seeded_client: AsyncClient):
        """Multiple filters can be combined."""
        resp = await seeded_client.get(
            "/api/matches",
            params={"location": "Remote", "workplace_type": "remote"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert "remote" in (item["job"]["location"] or "").lower()
            assert item["job"]["workplace_type"] == "remote"

    async def test_pagination_with_filters(self, seeded_client: AsyncClient):
        """Pagination works with filters applied."""
        resp = await seeded_client.get(
            "/api/matches",
            params={"location": "Remote", "limit": 1, "offset": 0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 1
        assert data["limit"] == 1
        assert data["offset"] == 0
