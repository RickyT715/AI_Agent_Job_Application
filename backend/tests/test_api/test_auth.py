"""Tests for API key authentication."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings, get_settings, reset_settings
from app.db.session import get_db_session
from app.main import app
from app.models.base import Base


@pytest.fixture
async def auth_db_engine():
    """In-memory SQLite engine for auth tests."""
    engine = create_async_engine("sqlite+aiosqlite:///", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def auth_client(auth_db_engine, monkeypatch):
    """Client with API key authentication enabled (api_key='test-secret-key')."""
    factory = async_sessionmaker(auth_db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_session():
        async with factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db_session] = _override_session

    # Mock ARQ pool
    mock_job = MagicMock()
    mock_job.job_id = "test-task-001"
    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=mock_job)
    app.state.arq_pool = mock_pool

    # Enable auth by setting a known api_key
    reset_settings()
    monkeypatch.setenv("API_KEY", "test-secret-key")
    reset_settings()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
    app.state.arq_pool = None
    reset_settings()


@pytest.fixture
async def noauth_client(auth_db_engine, monkeypatch):
    """Client with authentication disabled (api_key='')."""
    factory = async_sessionmaker(auth_db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_session():
        async with factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db_session] = _override_session

    mock_job = MagicMock()
    mock_job.job_id = "test-task-001"
    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=mock_job)
    app.state.arq_pool = mock_pool

    # Disable auth
    reset_settings()
    monkeypatch.setenv("API_KEY", "")
    reset_settings()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
    app.state.arq_pool = None
    reset_settings()


class TestAuthEnabled:
    """Tests when api_key is configured."""

    async def test_protected_endpoint_rejects_missing_key(self, auth_client: AsyncClient):
        """POST /api/matches/run requires auth and rejects requests without key."""
        resp = await auth_client.post("/api/matches/run")
        assert resp.status_code == 401
        assert "Invalid or missing API key" in resp.json()["detail"]

    async def test_protected_endpoint_rejects_wrong_key(self, auth_client: AsyncClient):
        """Wrong API key should be rejected."""
        resp = await auth_client.post(
            "/api/matches/run",
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    async def test_protected_endpoint_accepts_correct_key(self, auth_client: AsyncClient):
        """Correct API key should allow access."""
        resp = await auth_client.post(
            "/api/matches/run",
            headers={"X-API-Key": "test-secret-key"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"

    async def test_rescore_requires_auth(self, auth_client: AsyncClient):
        """POST /api/matches/{id}/rescore requires auth."""
        resp = await auth_client.post("/api/matches/1/rescore")
        assert resp.status_code == 401

    async def test_rescore_with_correct_key(self, auth_client: AsyncClient):
        """POST /api/matches/{id}/rescore works with correct key."""
        resp = await auth_client.post(
            "/api/matches/1/rescore",
            headers={"X-API-Key": "test-secret-key"},
        )
        assert resp.status_code == 200

    async def test_get_matches_no_auth_needed(self, auth_client: AsyncClient):
        """GET /api/matches does not require API key."""
        resp = await auth_client.get("/api/matches")
        assert resp.status_code == 200

    async def test_get_health_no_auth_needed(self, auth_client: AsyncClient):
        """GET /health does not require API key."""
        resp = await auth_client.get("/health")
        assert resp.status_code == 200

    async def test_get_preferences_no_auth_needed(self, auth_client: AsyncClient):
        """GET /api/config/preferences does not require API key."""
        resp = await auth_client.get("/api/config/preferences")
        assert resp.status_code == 200

    async def test_scrape_requires_auth(self, auth_client: AsyncClient):
        """POST /api/jobs/scrape requires auth."""
        resp = await auth_client.post(
            "/api/jobs/scrape",
            json={"queries": ["Python Dev"], "location": "Remote"},
        )
        assert resp.status_code == 401

    async def test_scrape_with_correct_key(self, auth_client: AsyncClient):
        """POST /api/jobs/scrape works with correct key."""
        resp = await auth_client.post(
            "/api/jobs/scrape",
            json={"queries": ["Python Dev"], "location": "Remote"},
            headers={"X-API-Key": "test-secret-key"},
        )
        assert resp.status_code == 200

    async def test_agent_start_requires_auth(self, auth_client: AsyncClient):
        """POST /api/agent/start requires auth."""
        resp = await auth_client.post(
            "/api/agent/start",
            json={"job_id": 1},
        )
        assert resp.status_code == 401

    async def test_agent_start_with_correct_key(self, auth_client: AsyncClient):
        """POST /api/agent/start works with correct key."""
        resp = await auth_client.post(
            "/api/agent/start",
            json={"job_id": 1},
            headers={"X-API-Key": "test-secret-key"},
        )
        assert resp.status_code == 200

    async def test_get_jobs_no_auth_needed(self, auth_client: AsyncClient):
        """GET /api/jobs does not require API key."""
        resp = await auth_client.get("/api/jobs")
        assert resp.status_code == 200


class TestAuthDisabled:
    """Tests when api_key is empty (dev mode)."""

    async def test_protected_endpoint_allowed_without_key(self, noauth_client: AsyncClient):
        """When auth is disabled, protected endpoints work without a key."""
        resp = await noauth_client.post("/api/matches/run")
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"

    async def test_rescore_allowed_without_key(self, noauth_client: AsyncClient):
        """Rescore endpoint works without auth when disabled."""
        resp = await noauth_client.post("/api/matches/1/rescore")
        assert resp.status_code == 200
