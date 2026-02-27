"""Tests for SQLAlchemy ORM models using SQLite."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.cover_letter import CoverLetter
from app.models.job import Job
from app.models.match import MatchResult
from app.models.user import User


async def _create_user(db: AsyncSession, email: str = "test@example.com") -> User:
    user = User(email=email, full_name="Test User")
    db.add(user)
    await db.flush()
    return user


async def _create_job(db: AsyncSession, ext_id: str = "ext-001", source: str = "test") -> Job:
    job = Job(
        external_id=ext_id,
        source=source,
        title="Software Engineer",
        company="TestCo",
        description="Build things.",
    )
    db.add(job)
    await db.flush()
    return job


async def _create_match(
    db: AsyncSession, user: User, job: Job, score: float = 8.0
) -> MatchResult:
    match = MatchResult(
        user_id=user.id,
        job_id=job.id,
        overall_score=score,
        score_breakdown={"skills": 9, "experience": 8, "education": 7, "location": 8, "salary": 8},
        reasoning="Strong match.",
        strengths=["Python expertise"],
        missing_skills=["Kubernetes"],
        interview_talking_points=["ML experience"],
    )
    db.add(match)
    await db.flush()
    return match


class TestJobModel:
    """Tests for the Job ORM model."""

    async def test_create_job(self, db_session: AsyncSession):
        job = await _create_job(db_session)
        result = await db_session.execute(select(Job).where(Job.id == job.id))
        loaded = result.scalar_one()
        assert loaded.title == "Software Engineer"
        assert loaded.company == "TestCo"

    async def test_job_unique_constraint(self, db_session: AsyncSession):
        """Duplicate (external_id, source) raises IntegrityError."""
        await _create_job(db_session, "ext-001", "greenhouse")
        with pytest.raises(IntegrityError):
            await _create_job(db_session, "ext-001", "greenhouse")

    async def test_job_different_source_allowed(self, db_session: AsyncSession):
        """Same external_id with different source is allowed."""
        await _create_job(db_session, "ext-001", "greenhouse")
        job2 = await _create_job(db_session, "ext-001", "lever")
        assert job2.id is not None

    async def test_jsonb_fields_round_trip(self, db_session: AsyncSession):
        """JSONB raw_data stores and retrieves correctly."""
        job = Job(
            external_id="json-test",
            source="test",
            title="Test",
            company="Co",
            description="Desc",
            raw_data={"key": "value", "nested": {"a": 1}},
        )
        db_session.add(job)
        await db_session.flush()

        result = await db_session.execute(select(Job).where(Job.id == job.id))
        loaded = result.scalar_one()
        assert loaded.raw_data == {"key": "value", "nested": {"a": 1}}


class TestMatchResultModel:
    """Tests for the MatchResult ORM model."""

    async def test_create_match_result(self, db_session: AsyncSession):
        user = await _create_user(db_session)
        job = await _create_job(db_session)
        match = await _create_match(db_session, user, job)
        assert match.id is not None
        assert match.overall_score == 8.0

    async def test_match_unique_per_user_job(self, db_session: AsyncSession):
        """Same user+job pair rejects duplicate."""
        user = await _create_user(db_session)
        job = await _create_job(db_session)
        await _create_match(db_session, user, job)
        with pytest.raises(IntegrityError):
            await _create_match(db_session, user, job, score=9.0)

    async def test_score_breakdown_is_dict(self, db_session: AsyncSession):
        user = await _create_user(db_session)
        job = await _create_job(db_session)
        match = await _create_match(db_session, user, job)
        result = await db_session.execute(
            select(MatchResult).where(MatchResult.id == match.id)
        )
        loaded = result.scalar_one()
        assert isinstance(loaded.score_breakdown, dict)
        assert loaded.score_breakdown["skills"] == 9


class TestApplicationModel:
    """Tests for the Application ORM model."""

    async def test_create_application(self, db_session: AsyncSession):
        user = await _create_user(db_session)
        job = await _create_job(db_session)
        app = Application(
            user_id=user.id,
            job_id=job.id,
            status="pending",
        )
        db_session.add(app)
        await db_session.flush()
        assert app.id is not None
        assert app.status == "pending"

    async def test_application_status_update(self, db_session: AsyncSession):
        user = await _create_user(db_session)
        job = await _create_job(db_session)
        app = Application(user_id=user.id, job_id=job.id, status="pending")
        db_session.add(app)
        await db_session.flush()
        app.status = "submitted"
        await db_session.flush()
        result = await db_session.execute(
            select(Application).where(Application.id == app.id)
        )
        assert result.scalar_one().status == "submitted"


class TestRelationships:
    """Tests for model relationships and cascades."""

    async def test_job_to_match_relationship(self, db_session: AsyncSession):
        user = await _create_user(db_session)
        job = await _create_job(db_session)
        await _create_match(db_session, user, job)
        result = await db_session.execute(select(Job).where(Job.id == job.id))
        loaded_job = result.scalar_one()
        # Access relationship
        await db_session.refresh(loaded_job, ["match_results"])
        assert len(loaded_job.match_results) == 1

    async def test_cascade_delete_job_removes_matches(self, db_session: AsyncSession):
        user = await _create_user(db_session)
        job = await _create_job(db_session)
        await _create_match(db_session, user, job)
        # Delete the job
        await db_session.delete(job)
        await db_session.flush()
        # Match should be gone
        result = await db_session.execute(select(MatchResult))
        assert result.scalars().all() == []

    async def test_user_relationships(self, db_session: AsyncSession):
        user = await _create_user(db_session)
        job = await _create_job(db_session)
        await _create_match(db_session, user, job)
        await db_session.refresh(user, ["match_results"])
        assert len(user.match_results) == 1
