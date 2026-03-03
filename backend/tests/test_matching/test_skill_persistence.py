"""Tests for skill persistence (extract + store in DB)."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.services.matching.skill_persistence import (
    backfill_all_job_skills,
    extract_and_persist_skills,
)


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


async def _create_job(
    db: AsyncSession, ext_id: str = "ext-001", description: str = ""
) -> Job:
    job = Job(
        external_id=ext_id,
        source="test",
        title="Software Engineer",
        company="TestCo",
        description=description or "Looking for a Python and Docker developer with leadership skills.",
    )
    db.add(job)
    await db.flush()
    return job


class TestExtractAndPersistSkills:
    """Tests for extract_and_persist_skills()."""

    async def test_extracts_and_stores(self, db_session: AsyncSession):
        job = await _create_job(db_session)
        count = await extract_and_persist_skills(db_session, job)
        assert count > 0

        result = await db_session.execute(
            select(JobSkill).where(JobSkill.job_id == job.id)
        )
        skills = result.scalars().all()
        assert len(skills) == count
        skill_names = {s.skill_name for s in skills}
        assert "python" in skill_names
        assert "docker" in skill_names

    async def test_skip_existing(self, db_session: AsyncSession):
        job = await _create_job(db_session)
        count1 = await extract_and_persist_skills(db_session, job)
        assert count1 > 0

        # Second call should skip
        count2 = await extract_and_persist_skills(db_session, job)
        assert count2 == 0


class TestBackfillAllJobSkills:
    """Tests for backfill_all_job_skills()."""

    async def test_backfills_jobs_without_skills(self, db_session: AsyncSession):
        await _create_job(db_session, "ext-001", "Need Python and React developer")
        await _create_job(db_session, "ext-002", "Need Java and Spring Boot developer")

        result = await backfill_all_job_skills(db_session)
        assert result["jobs_processed"] == 2
        assert result["total_skills"] > 0

        # Second call should process 0 (all already have skills)
        result2 = await backfill_all_job_skills(db_session)
        assert result2["jobs_processed"] == 0
