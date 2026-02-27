"""Database session management with async SQLAlchemy."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings


def get_engine(database_url: str | None = None):
    """Create async database engine."""
    url = database_url or get_settings().database_url
    return create_async_engine(url, echo=False, future=True)


def get_session_factory(database_url: str | None = None) -> async_sessionmaker[AsyncSession]:
    """Create session factory."""
    engine = get_engine(database_url)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Dependency that yields a database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
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
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
