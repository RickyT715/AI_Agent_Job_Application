"""Tests for the health check endpoint."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_db_session
from app.main import app
from app.models.base import Base


@pytest.fixture
async def health_db_engine():
    """In-memory SQLite engine for health tests."""
    engine = create_async_engine("sqlite+aiosqlite:///", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def healthy_client(health_db_engine):
    """Client with healthy DB and ARQ pool."""
    factory = async_sessionmaker(health_db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_session():
        async with factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db_session] = _override_session

    # Set up healthy ARQ pool
    mock_pool = MagicMock()
    app.state.arq_pool = mock_pool

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
    app.state.arq_pool = None


@pytest.fixture
async def no_redis_client(health_db_engine):
    """Client with healthy DB but no Redis/ARQ pool."""
    factory = async_sessionmaker(health_db_engine, class_=AsyncSession, expire_on_commit=False)

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
async def broken_db_client():
    """Client with a DB session that always raises on execute."""
    async def _broken_session():
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock(side_effect=Exception("DB connection failed"))
        yield session

    app.dependency_overrides[get_db_session] = _broken_session
    app.state.arq_pool = MagicMock()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
    app.state.arq_pool = None


class TestHealthCheck:
    """Tests for GET /health."""

    async def test_healthy_status(self, healthy_client: AsyncClient):
        """All services healthy returns 200 with status=healthy."""
        resp = await healthy_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["checks"]["api"] == "healthy"
        assert data["checks"]["database"] == "healthy"
        assert data["checks"]["redis"] == "healthy"

    async def test_includes_all_checks(self, healthy_client: AsyncClient):
        """Response includes api, database, and redis checks."""
        resp = await healthy_client.get("/health")
        checks = resp.json()["checks"]
        assert "api" in checks
        assert "database" in checks
        assert "redis" in checks

    async def test_redis_unavailable_still_healthy(self, no_redis_client: AsyncClient):
        """Redis unavailable (not configured) still returns 200."""
        resp = await no_redis_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["checks"]["redis"] == "unavailable"
        assert data["checks"]["database"] == "healthy"

    async def test_degraded_when_db_unhealthy(self, broken_db_client: AsyncClient):
        """Database failure returns 503 with status=degraded."""
        resp = await broken_db_client.get("/health")
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["checks"]["database"] == "unhealthy"
        assert data["checks"]["api"] == "healthy"
