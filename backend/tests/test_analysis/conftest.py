"""Fixtures for skill analysis tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.job import Job
from app.models.job_skill import JobSkill


@pytest.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def seeded_db(db_session: AsyncSession) -> AsyncSession:
    """DB session with jobs and skills pre-populated."""
    # Create 5 "Software Engineer" jobs and 2 "Data Scientist" jobs
    jobs = []
    for i in range(5):
        job = Job(
            external_id=f"se-{i:03d}",
            source="test",
            title="Software Engineer",
            company=f"Company{i}",
            description=f"Build software with Python and Docker. {i}",
        )
        db_session.add(job)
        jobs.append(job)

    for i in range(2):
        job = Job(
            external_id=f"ds-{i:03d}",
            source="test",
            title="Data Scientist",
            company=f"DataCo{i}",
            description=f"Machine learning with Python. {i}",
        )
        db_session.add(job)
        jobs.append(job)

    await db_session.flush()

    # Add skills to SE jobs
    for i in range(5):
        db_session.add(JobSkill(job_id=jobs[i].id, skill_name="python", category="technical"))
        db_session.add(JobSkill(job_id=jobs[i].id, skill_name="docker", category="technical"))
        db_session.add(JobSkill(job_id=jobs[i].id, skill_name="leadership", category="soft_skill"))
    # Only 3 SE jobs have react
    for i in range(3):
        db_session.add(JobSkill(job_id=jobs[i].id, skill_name="react", category="technical"))

    # Add skills to DS jobs
    for i in range(2):
        j = jobs[5 + i]
        db_session.add(JobSkill(job_id=j.id, skill_name="python", category="technical"))
        db_session.add(JobSkill(job_id=j.id, skill_name="machine learning", category="technical"))

    await db_session.flush()
    return db_session
