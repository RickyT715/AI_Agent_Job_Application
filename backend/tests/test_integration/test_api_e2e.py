"""End-to-end API integration test.

Tests the complete API workflow: upload resume → scrape → match → retrieve → generate resume.
Uses real DB (SQLite for testing) but mocked external services.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_db_session
from app.main import app
from app.models.base import Base
from app.models.job import Job
from app.models.match import MatchResult
from app.models.user import User


@pytest.fixture
async def e2e_engine():
    """Isolated SQLite engine for E2E tests."""
    engine = create_async_engine("sqlite+aiosqlite:///", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def e2e_client(e2e_engine) -> AsyncClient:
    """Client wired to E2E database."""
    factory = async_sessionmaker(e2e_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override():
        async with factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db_session] = _override

    # Mock ARQ pool
    mock_job = MagicMock()
    mock_job.job_id = "e2e-task-001"
    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=mock_job)
    app.state.arq_pool = mock_pool

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
    app.state.arq_pool = None


class TestAPIWorkflow:
    """Full API workflow E2E test."""

    async def test_upload_resume(self, e2e_client: AsyncClient):
        """Upload a resume and verify response."""
        resp = await e2e_client.post(
            "/api/config/resume",
            files={"file": ("resume.txt", b"John Doe\nPython Developer\n5 years experience")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Resume uploaded successfully"
        assert data["character_count"] > 0

    async def test_jobs_empty_initially(self, e2e_client: AsyncClient):
        """GET /api/jobs returns empty list before scraping."""
        resp = await e2e_client.get("/api/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_trigger_scraping_returns_task(self, e2e_client: AsyncClient):
        """POST /api/jobs/scrape returns a task ID."""
        resp = await e2e_client.post(
            "/api/jobs/scrape",
            json={"queries": ["Python Developer"]},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"

    async def test_full_workflow_with_seeded_data(self, e2e_client: AsyncClient, e2e_engine):
        """Seed jobs + matches, then verify API returns them correctly."""
        factory = async_sessionmaker(e2e_engine, class_=AsyncSession, expire_on_commit=False)

        # Seed data directly into the database
        async with factory() as session:
            user = User(email="test@e2e.com", full_name="E2E User", resume_text="Python developer")
            session.add(user)
            await session.flush()

            jobs = []
            for i in range(3):
                job = Job(
                    external_id=f"e2e-{i:03d}",
                    source="test",
                    title=f"Python Engineer {i}",
                    company=f"Company {i}",
                    description=f"Build Python services {i}",
                    location="Remote",
                    workplace_type="remote",
                )
                session.add(job)
                jobs.append(job)
            await session.flush()

            for i, job in enumerate(jobs):
                match = MatchResult(
                    user_id=user.id,
                    job_id=job.id,
                    overall_score=9.0 - i,
                    score_breakdown={"skills": 9 - i, "experience": 8},
                    reasoning=f"Good match {i}",
                    strengths=["Python"],
                    missing_skills=["Go"],
                )
                session.add(match)
            await session.commit()

        # Verify jobs endpoint
        resp = await e2e_client.get("/api/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3

        # Verify matches sorted by score
        resp = await e2e_client.get("/api/matches")
        assert resp.status_code == 200
        matches = resp.json()["items"]
        assert len(matches) == 3
        scores = [m["overall_score"] for m in matches]
        assert scores == sorted(scores, reverse=True)

        # Verify match detail
        match_id = matches[0]["id"]
        resp = await e2e_client.get(f"/api/matches/{match_id}")
        assert resp.status_code == 200
        detail = resp.json()
        assert "reasoning" in detail
        assert "missing_skills" in detail
        assert "strengths" in detail

    async def test_health_check(self, e2e_client: AsyncClient):
        """Health endpoint returns healthy."""
        resp = await e2e_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    async def test_preferences_round_trip(self, e2e_client: AsyncClient):
        """GET preferences returns valid config."""
        resp = await e2e_client.get("/api/config/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert "job_titles" in data
        assert "weights" in data


class TestResumeGenerationE2E:
    """E2E test for resume generation workflow."""

    async def test_full_resume_generation_flow(self, e2e_client: AsyncClient, e2e_engine):
        """Seed match → generate resume → poll status → list by match."""
        factory = async_sessionmaker(e2e_engine, class_=AsyncSession, expire_on_commit=False)

        # Seed data
        async with factory() as session:
            user = User(
                email="e2e-resume@test.com",
                full_name="E2E Resume User",
                resume_text="Python developer with 5 years experience",
            )
            session.add(user)
            await session.flush()

            job = Job(
                external_id="e2e-resume-job",
                source="test",
                title="Python Engineer",
                company="E2E Corp",
                description="Build Python services with FastAPI",
                location="Remote",
                workplace_type="remote",
            )
            session.add(job)
            await session.flush()

            match = MatchResult(
                user_id=user.id,
                job_id=job.id,
                overall_score=8.0,
                score_breakdown={"skills": 8, "experience": 7},
                reasoning="Good Python match",
                strengths=["Python", "FastAPI"],
                missing_skills=["Go"],
            )
            session.add(match)
            await session.commit()
            match_id = match.id

        # Step 1: Check health (not configured → unavailable)
        with patch("app.routers.resumes.get_settings") as mock_settings:
            mock_settings.return_value.resume_generator_url = ""
            resp = await e2e_client.get("/api/resumes/health")
        assert resp.status_code == 200
        assert resp.json()["available"] is False

        # Step 2: Generate resume (mocked external service)
        task_resp = {"id": "e2e-ext-1", "status": "running"}
        with (
            patch("app.routers.resumes.get_settings") as mock_settings,
            patch("app.routers.resumes.ResumeGeneratorClient") as mock_cls,
        ):
            mock_settings.return_value.resume_generator_url = "http://fake:8000"
            mock_instance = AsyncMock()
            mock_instance.sync_user_info.return_value = {"status": "ok"}
            mock_instance.create_and_start.return_value = task_resp
            mock_cls.return_value = mock_instance

            resp = await e2e_client.post(
                "/api/resumes/generate",
                json={"match_id": match_id},
            )
        assert resp.status_code == 200
        gen_data = resp.json()
        assert gen_data["status"] == "running"
        resume_id = gen_data["id"]

        # Step 3: Poll status (still running)
        with (
            patch("app.routers.resumes.get_settings") as mock_settings,
            patch("app.routers.resumes.ResumeGeneratorClient") as mock_cls,
        ):
            mock_settings.return_value.resume_generator_url = "http://fake:8000"
            mock_instance = AsyncMock()
            mock_instance.get_task_status.return_value = {"status": "running"}
            mock_cls.return_value = mock_instance

            resp = await e2e_client.get(f"/api/resumes/{resume_id}/status")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

        # Step 4: List by match
        resp = await e2e_client.get(f"/api/resumes/by-match/{match_id}")
        assert resp.status_code == 200
        records = resp.json()
        assert len(records) == 1
        assert records[0]["match_id"] == match_id

    async def test_resume_health_endpoint(self, e2e_client: AsyncClient):
        """Health endpoint works with mocked available service."""
        with (
            patch("app.routers.resumes.get_settings") as mock_settings,
            patch("app.routers.resumes.ResumeGeneratorClient") as mock_cls,
        ):
            mock_settings.return_value.resume_generator_url = "http://fake:8000"
            mock_instance = AsyncMock()
            mock_instance.health_check.return_value = {"status": "healthy"}
            mock_cls.return_value = mock_instance
            resp = await e2e_client.get("/api/resumes/health")
        assert resp.status_code == 200
        assert resp.json()["available"] is True
        assert resp.json()["detail"] == "Service healthy"

    async def test_resume_empty_by_match(self, e2e_client: AsyncClient):
        """by-match returns empty list for match with no generated resumes."""
        resp = await e2e_client.get("/api/resumes/by-match/9999")
        assert resp.status_code == 200
        assert resp.json() == []
