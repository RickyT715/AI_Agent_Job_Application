"""Database session management with async SQLAlchemy.

Uses a singleton pattern for the engine and session factory to avoid
creating a new connection pool on every request.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(database_url: str | None = None) -> AsyncEngine:
    """Get or create the singleton async database engine.

    When ``database_url`` is supplied the cache is bypassed so that tests
    can point at a throwaway database without polluting the singleton.
    """
    global _engine
    if database_url is not None:
        # Explicit URL — create a fresh engine (typically for tests).
        return _create_engine(database_url)
    if _engine is None:
        _engine = _create_engine(get_settings().database_url)
    return _engine


def _create_engine(url: str) -> AsyncEngine:
    """Create an async engine with appropriate pool settings."""
    kwargs: dict = {"echo": False, "future": True}
    # Connection-pool tuning only applies to pool-capable backends
    # (e.g. asyncpg). SQLite / aiosqlite uses StaticPool internally.
    if "sqlite" not in url:
        kwargs.update(pool_size=10, max_overflow=20, pool_recycle=300)
    return create_async_engine(url, **kwargs)


def get_session_factory(
    database_url: str | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Get or create the singleton session factory.

    Passing ``database_url`` creates a one-off factory (for tests) without
    touching the cached singleton.
    """
    global _session_factory
    if database_url is not None:
        engine = get_engine(database_url)
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency that yields a database session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_session_ctx() -> AsyncGenerator[AsyncSession]:
    """Context manager for DB sessions outside of FastAPI dependency injection.

    Used by worker tasks and background jobs.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def reset_db() -> None:
    """Reset cached engine and session factory (for testing)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
