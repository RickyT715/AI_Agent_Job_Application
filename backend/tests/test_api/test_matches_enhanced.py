"""Tests for matches router: trigger_matching, rescore, ARQ pool behavior."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_db_session
from app.main import app
from app.models.base import Base


@pytest.fixture
async def matches_db_engine():
    """In-memory SQLite engine."""
    engine = create_async_engine("sqlite+aiosqlite:///", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def no_pool_client(matches_db_engine):
    """Client with ARQ pool set to None (task queue unavailable)."""
    factory = async_sessionmaker(matches_db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_session():
        async with factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db_session] = _override_session
    app.state.arq_pool = None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def pool_client(matches_db_engine):
    """Client with a mock ARQ pool that tracks enqueue calls."""
    factory = async_sessionmaker(matches_db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_session():
        async with factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db_session] = _override_session

    mock_job = MagicMock()
    mock_job.job_id = "match-task-123"
    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=mock_job)
    app.state.arq_pool = mock_pool

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client, mock_pool

    app.dependency_overrides.clear()
    app.state.arq_pool = None


class TestTriggerMatching:
    """Tests for POST /api/matches/run."""

    async def test_returns_503_when_no_arq_pool(self, no_pool_client: AsyncClient):
        """Returns 503 when task queue is unavailable."""
        resp = await no_pool_client.post("/api/matches/run")
        assert resp.status_code == 503
        assert "Task queue unavailable" in resp.json()["detail"]

    async def test_enqueues_run_matching_job(self, pool_client):
        """Enqueues a 'run_matching' ARQ job and returns task ID."""
        client, mock_pool = pool_client
        resp = await client.post("/api/matches/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == "match-task-123"
        assert data["status"] == "queued"
        mock_pool.enqueue_job.assert_called_once_with("run_matching")

    async def test_returns_task_id_in_response(self, pool_client):
        """Response includes the task_id from the enqueued job."""
        client, _ = pool_client
        resp = await client.post("/api/matches/run")
        assert "task_id" in resp.json()
        assert resp.json()["task_id"] == "match-task-123"


class TestRescoreMatch:
    """Tests for POST /api/matches/{match_id}/rescore."""

    async def test_returns_503_when_no_arq_pool(self, no_pool_client: AsyncClient):
        """Returns 503 when task queue is unavailable."""
        resp = await no_pool_client.post("/api/matches/42/rescore")
        assert resp.status_code == 503

    async def test_enqueues_rescore_job(self, pool_client):
        """Enqueues a 'run_matching' ARQ job with rescore job_id."""
        client, mock_pool = pool_client
        resp = await client.post("/api/matches/42/rescore")
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"
        mock_pool.enqueue_job.assert_called_once_with(
            "run_matching", _job_id="rescore-42"
        )

    async def test_rescore_job_id_includes_match_id(self, pool_client):
        """The enqueued job ID contains the match ID for traceability."""
        client, mock_pool = pool_client
        await client.post("/api/matches/99/rescore")
        call_args = mock_pool.enqueue_job.call_args
        assert call_args.kwargs["_job_id"] == "rescore-99"
