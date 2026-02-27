"""Tests for the agent API router."""

from httpx import AsyncClient


class TestAgentEndpoints:
    """Tests for agent start/resume endpoints."""

    async def test_start_agent(self, client: AsyncClient):
        resp = await client.post(
            "/api/agent/start",
            json={"job_id": 1},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "queued"

    async def test_resume_with_approve(self, client: AsyncClient):
        resp = await client.post(
            "/api/agent/resume/thread-123",
            json={"action": "approve"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["action"] == "approve"

    async def test_resume_with_reject(self, client: AsyncClient):
        resp = await client.post(
            "/api/agent/resume/thread-456",
            json={"action": "reject"},
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["action"] == "reject"

    async def test_resume_with_edit(self, client: AsyncClient):
        resp = await client.post(
            "/api/agent/resume/thread-789",
            json={"action": "edit", "edits": {"field1": "new_value"}},
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["action"] == "edit"
