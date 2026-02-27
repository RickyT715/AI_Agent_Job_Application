"""API test fixtures with mock DB session and test client."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_db_session
from app.main import app
from app.models.base import Base


@pytest.fixture
async def db_engine():
    """In-memory SQLite engine for API tests."""
    engine = create_async_engine("sqlite+aiosqlite:///", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    """Test DB session."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_engine) -> AsyncClient:
    """Async test client with DB session override and mock ARQ pool."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_session():
        async with factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db_session] = _override_session

    # Mock ARQ pool for endpoints that enqueue tasks
    mock_job = MagicMock()
    mock_job.job_id = "test-task-001"
    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=mock_job)
    app.state.arq_pool = mock_pool

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
    app.state.arq_pool = None


@pytest.fixture
async def seeded_client(client: AsyncClient, db_engine) -> AsyncClient:
    """Client with seed data (user, jobs, matches) pre-populated."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    from app.models.job import Job
    from app.models.match import MatchResult
    from app.models.user import User

    async with factory() as session:
        user = User(email="test@example.com", full_name="Test User", resume_text="Test resume")
        session.add(user)
        await session.flush()

        jobs = []
        for i in range(5):
            job = Job(
                external_id=f"seed-{i:03d}",
                source="test",
                title=f"Engineer {i}",
                company=f"Company{i}",
                description=f"Job description {i}",
                location="Remote" if i % 2 == 0 else "NYC",
                workplace_type="remote" if i % 2 == 0 else "onsite",
            )
            session.add(job)
            jobs.append(job)
        await session.flush()

        for i, job in enumerate(jobs):
            match = MatchResult(
                user_id=user.id,
                job_id=job.id,
                overall_score=10.0 - i,
                score_breakdown={"skills": 9 - i, "experience": 8, "education": 7, "location": 8, "salary": 7},
                reasoning=f"Match reasoning for job {i}",
                strengths=["Python"],
                missing_skills=["Go"],
                interview_talking_points=["Experience"],
            )
            session.add(match)
        await session.commit()

    return client
