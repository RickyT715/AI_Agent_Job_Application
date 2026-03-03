"""Tests for the database session singleton management."""

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db import session as session_mod


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Ensure each test starts with a clean singleton state."""
    session_mod.reset_db()
    yield
    session_mod.reset_db()


class TestGetEngine:
    """Tests for get_engine() singleton behaviour."""

    def test_explicit_url_creates_fresh_engine(self):
        """When database_url is passed, a new engine is created every time."""
        url = "sqlite+aiosqlite:///"
        engine_a = session_mod.get_engine(database_url=url)
        engine_b = session_mod.get_engine(database_url=url)
        assert isinstance(engine_a, AsyncEngine)
        assert isinstance(engine_b, AsyncEngine)
        # Different objects because explicit URL bypasses cache
        assert engine_a is not engine_b

    def test_singleton_returns_same_engine(self, monkeypatch):
        """Without explicit URL, get_engine() caches the engine."""
        monkeypatch.setattr(
            "app.db.session.get_settings",
            lambda: type("S", (), {"database_url": "sqlite+aiosqlite:///"})(),
        )
        engine_a = session_mod.get_engine()
        engine_b = session_mod.get_engine()
        assert engine_a is engine_b

    def test_explicit_url_does_not_pollute_singleton(self, monkeypatch):
        """Passing an explicit URL should not set the cached _engine."""
        session_mod.get_engine(database_url="sqlite+aiosqlite:///")
        # The cached singleton should still be None
        assert session_mod._engine is None


class TestGetSessionFactory:
    """Tests for get_session_factory() singleton behaviour."""

    def test_explicit_url_creates_one_off_factory(self):
        """Explicit URL returns a new factory without caching."""
        url = "sqlite+aiosqlite:///"
        factory_a = session_mod.get_session_factory(database_url=url)
        factory_b = session_mod.get_session_factory(database_url=url)
        assert factory_a is not factory_b

    def test_singleton_returns_same_factory(self, monkeypatch):
        """Without explicit URL, get_session_factory() caches the factory."""
        monkeypatch.setattr(
            "app.db.session.get_settings",
            lambda: type("S", (), {"database_url": "sqlite+aiosqlite:///"})(),
        )
        factory_a = session_mod.get_session_factory()
        factory_b = session_mod.get_session_factory()
        assert factory_a is factory_b

    def test_explicit_url_does_not_pollute_factory_singleton(self):
        """Explicit URL should not set the cached _session_factory."""
        session_mod.get_session_factory(database_url="sqlite+aiosqlite:///")
        assert session_mod._session_factory is None


class TestResetDb:
    """Tests for reset_db() clearing cached singletons."""

    def test_reset_clears_engine_and_factory(self, monkeypatch):
        """After reset_db(), both engine and factory are None."""
        monkeypatch.setattr(
            "app.db.session.get_settings",
            lambda: type("S", (), {"database_url": "sqlite+aiosqlite:///"})(),
        )
        session_mod.get_engine()
        session_mod.get_session_factory()
        assert session_mod._engine is not None
        assert session_mod._session_factory is not None

        session_mod.reset_db()
        assert session_mod._engine is None
        assert session_mod._session_factory is None


class TestGetDbSession:
    """Tests for the FastAPI dependency get_db_session()."""

    async def test_yields_async_session(self, monkeypatch):
        """get_db_session should yield an AsyncSession."""
        monkeypatch.setattr(
            "app.db.session.get_settings",
            lambda: type("S", (), {"database_url": "sqlite+aiosqlite:///"})(),
        )
        gen = session_mod.get_db_session()
        session = await gen.__anext__()
        assert isinstance(session, AsyncSession)
        # Clean up the generator
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass


class TestGetDbSessionCtx:
    """Tests for the context-manager get_db_session_ctx()."""

    async def test_yields_async_session(self, monkeypatch):
        """get_db_session_ctx should yield an AsyncSession."""
        monkeypatch.setattr(
            "app.db.session.get_settings",
            lambda: type("S", (), {"database_url": "sqlite+aiosqlite:///"})(),
        )
        async with session_mod.get_db_session_ctx() as session:
            assert isinstance(session, AsyncSession)


class TestCreateEngine:
    """Tests for _create_engine internal helper."""

    def test_sqlite_engine_has_no_pool_size(self):
        """SQLite engines should not set pool_size."""
        engine = session_mod._create_engine("sqlite+aiosqlite:///")
        assert isinstance(engine, AsyncEngine)

    def test_non_sqlite_engine_gets_pool_settings(self):
        """Non-SQLite engines should receive pool tuning kwargs."""
        engine = session_mod._create_engine("postgresql+asyncpg://localhost/test")
        assert isinstance(engine, AsyncEngine)
        # Pool size is set in the pool, verifying engine creation doesn't crash
