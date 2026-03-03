"""Tests for the JobSkill ORM model."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.job_skill import JobSkill


async def _create_job(db: AsyncSession, ext_id: str = "ext-001") -> Job:
    job = Job(
        external_id=ext_id,
        source="test",
        title="Software Engineer",
        company="TestCo",
        description="Build things with Python and Docker.",
    )
    db.add(job)
    await db.flush()
    return job


class TestJobSkillModel:
    """Tests for the JobSkill ORM model."""

    async def test_create_job_skill(self, db_session: AsyncSession):
        job = await _create_job(db_session)
        skill = JobSkill(job_id=job.id, skill_name="python", category="technical")
        db_session.add(skill)
        await db_session.flush()

        result = await db_session.execute(
            select(JobSkill).where(JobSkill.id == skill.id)
        )
        loaded = result.scalar_one()
        assert loaded.skill_name == "python"
        assert loaded.category == "technical"
        assert loaded.job_id == job.id

    async def test_unique_constraint(self, db_session: AsyncSession):
        job = await _create_job(db_session)
        db_session.add(JobSkill(job_id=job.id, skill_name="python", category="technical"))
        await db_session.flush()
        db_session.add(JobSkill(job_id=job.id, skill_name="python", category="technical"))
        with pytest.raises(IntegrityError):
            await db_session.flush()

    async def test_cascade_delete(self, db_session: AsyncSession):
        job = await _create_job(db_session)
        db_session.add(JobSkill(job_id=job.id, skill_name="python", category="technical"))
        db_session.add(JobSkill(job_id=job.id, skill_name="leadership", category="soft_skill"))
        await db_session.flush()

        await db_session.delete(job)
        await db_session.flush()

        result = await db_session.execute(select(JobSkill))
        remaining = result.scalars().all()
        assert len(remaining) == 0

    async def test_job_relationship(self, db_session: AsyncSession):
        job = await _create_job(db_session)
        db_session.add(JobSkill(job_id=job.id, skill_name="python", category="technical"))
        db_session.add(JobSkill(job_id=job.id, skill_name="docker", category="technical"))
        await db_session.flush()

        # Refresh to load relationships
        await db_session.refresh(job, ["skills"])
        assert len(job.skills) == 2
        skill_names = {s.skill_name for s in job.skills}
        assert skill_names == {"python", "docker"}
