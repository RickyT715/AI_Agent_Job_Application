"""Tests for the jobs API router."""

import pytest
from httpx import AsyncClient


class TestListJobs:
    """Tests for GET /api/jobs."""

    async def test_list_jobs_returns_paginated(self, seeded_client: AsyncClient):
        resp = await seeded_client.get("/api/jobs", params={"limit": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 5
        assert data["total"] == 5

    async def test_list_jobs_respects_limit(self, seeded_client: AsyncClient):
        resp = await seeded_client.get("/api/jobs", params={"limit": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5

    async def test_list_jobs_filter_by_location(self, seeded_client: AsyncClient):
        resp = await seeded_client.get("/api/jobs", params={"location": "Remote"})
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert "Remote" in (item["location"] or "")

    async def test_list_jobs_filter_by_workplace_type(self, seeded_client: AsyncClient):
        resp = await seeded_client.get("/api/jobs", params={"workplace_type": "remote"})
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["workplace_type"] == "remote"

    async def test_list_jobs_full_text_search(self, seeded_client: AsyncClient):
        resp = await seeded_client.get("/api/jobs", params={"q": "Engineer 0"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) >= 1

    async def test_list_jobs_empty_result(self, seeded_client: AsyncClient):
        resp = await seeded_client.get("/api/jobs", params={"q": "nonexistentxyz"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestGetJob:
    """Tests for GET /api/jobs/{id}."""

    async def test_get_job_by_id(self, seeded_client: AsyncClient):
        # First list to get an ID
        list_resp = await seeded_client.get("/api/jobs", params={"limit": 1})
        job_id = list_resp.json()["items"][0]["id"]
        resp = await seeded_client.get(f"/api/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id

    async def test_get_job_not_found(self, seeded_client: AsyncClient):
        resp = await seeded_client.get("/api/jobs/99999")
        assert resp.status_code == 404


class TestScraping:
    """Tests for scraping endpoints."""

    async def test_trigger_scraping(self, client: AsyncClient):
        resp = await client.post(
            "/api/jobs/scrape",
            json={"queries": ["Python Dev"], "location": "Remote"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "queued"

    async def test_scraping_status(self, client: AsyncClient):
        resp = await client.get("/api/jobs/scrape/test-task-001/status")
        assert resp.status_code == 200
        assert resp.json()["task_id"] == "test-task-001"
