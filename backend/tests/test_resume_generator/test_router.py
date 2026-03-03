"""Tests for the resumes router."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_db_session
from app.main import app
from app.models.base import Base
from app.models.generated_resume import GeneratedResume
from app.models.job import Job
from app.models.match import MatchResult
from app.models.user import User


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
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_session():
        async with factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db_session] = _override_session
    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=MagicMock(job_id="test"))
    app.state.arq_pool = mock_pool

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()
    app.state.arq_pool = None


@pytest.fixture
async def seeded_data(db_engine):
    """Seed user + job + match, return their IDs."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        user = User(email="test@example.com", full_name="Test User", resume_text="Python developer")
        session.add(user)
        await session.flush()

        job = Job(
            external_id="ext-001",
            source="test",
            title="Python Dev",
            company="TestCo",
            description="Build Python services",
        )
        session.add(job)
        await session.flush()

        match = MatchResult(
            user_id=user.id,
            job_id=job.id,
            overall_score=8.5,
            score_breakdown={"skills": 9},
            reasoning="Strong Python match",
            strengths=["Python"],
            missing_skills=["Go"],
        )
        session.add(match)
        await session.flush()
        await session.commit()

        return {"user_id": user.id, "job_id": job.id, "match_id": match.id}


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_not_configured(self, client):
        with patch("app.routers.resumes.get_settings") as mock_settings:
            mock_settings.return_value.resume_generator_url = ""
            resp = await client.get("/api/resumes/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is False

    @pytest.mark.asyncio
    async def test_service_healthy(self, client):
        with (
            patch("app.routers.resumes.get_settings") as mock_settings,
            patch("app.routers.resumes.ResumeGeneratorClient") as mock_cls,
        ):
            mock_settings.return_value.resume_generator_url = "http://fake:8000"
            mock_instance = AsyncMock()
            mock_instance.health_check.return_value = {"status": "healthy"}
            mock_cls.return_value = mock_instance
            resp = await client.get("/api/resumes/health")
        assert resp.status_code == 200
        assert resp.json()["available"] is True

    @pytest.mark.asyncio
    async def test_service_unreachable(self, client):
        with (
            patch("app.routers.resumes.get_settings") as mock_settings,
            patch("app.routers.resumes.ResumeGeneratorClient") as mock_cls,
        ):
            mock_settings.return_value.resume_generator_url = "http://fake:8000"
            mock_instance = AsyncMock()
            mock_instance.health_check.side_effect = Exception("Connection refused")
            mock_cls.return_value = mock_instance
            resp = await client.get("/api/resumes/health")
        assert resp.status_code == 200
        assert resp.json()["available"] is False


class TestGenerateEndpoint:
    @pytest.mark.asyncio
    async def test_match_not_found(self, client):
        with patch("app.routers.resumes.get_settings") as mock_settings:
            mock_settings.return_value.resume_generator_url = "http://fake:8000"
            resp = await client.post("/api/resumes/generate", json={"match_id": 9999})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_service_not_configured(self, client, seeded_data):
        with patch("app.routers.resumes.get_settings") as mock_settings:
            mock_settings.return_value.resume_generator_url = ""
            resp = await client.post(
                "/api/resumes/generate",
                json={"match_id": seeded_data["match_id"]},
            )
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_success(self, client, seeded_data):
        task_resp = {"id": "ext-task-1", "status": "running"}
        with (
            patch("app.routers.resumes.get_settings") as mock_settings,
            patch("app.routers.resumes.ResumeGeneratorClient") as mock_cls,
        ):
            mock_settings.return_value.resume_generator_url = "http://fake:8000"
            mock_instance = AsyncMock()
            mock_instance.sync_user_info.return_value = {"status": "ok"}
            mock_instance.create_and_start.return_value = task_resp
            mock_cls.return_value = mock_instance
            resp = await client.post(
                "/api/resumes/generate",
                json={"match_id": seeded_data["match_id"]},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["external_task_id"] == "ext-task-1"
        assert data["status"] == "running"
        assert data["match_id"] == seeded_data["match_id"]

    @pytest.mark.asyncio
    async def test_external_service_error_returns_502(self, client, seeded_data):
        from app.services.resume_generator.client import ResumeGeneratorError

        with (
            patch("app.routers.resumes.get_settings") as mock_settings,
            patch("app.routers.resumes.ResumeGeneratorClient") as mock_cls,
        ):
            mock_settings.return_value.resume_generator_url = "http://fake:8000"
            mock_instance = AsyncMock()
            mock_instance.sync_user_info.side_effect = ResumeGeneratorError(500, "Pipeline crash")
            mock_cls.return_value = mock_instance
            resp = await client.post(
                "/api/resumes/generate",
                json={"match_id": seeded_data["match_id"]},
            )
        assert resp.status_code == 502
        assert "Pipeline crash" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_success_with_optional_params(self, client, seeded_data):
        task_resp = {"id": "ext-task-2", "status": "running"}
        with (
            patch("app.routers.resumes.get_settings") as mock_settings,
            patch("app.routers.resumes.ResumeGeneratorClient") as mock_cls,
        ):
            mock_settings.return_value.resume_generator_url = "http://fake:8000"
            mock_instance = AsyncMock()
            mock_instance.sync_user_info.return_value = {"status": "ok"}
            mock_instance.create_and_start.return_value = task_resp
            mock_cls.return_value = mock_instance
            resp = await client.post(
                "/api/resumes/generate",
                json={
                    "match_id": seeded_data["match_id"],
                    "generate_cover_letter": False,
                    "language": "zh",
                    "provider": "openai",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["external_task_id"] == "ext-task-2"


class TestStatusEndpoint:
    @pytest.mark.asyncio
    async def test_not_found(self, client):
        resp = await client.get("/api/resumes/9999/status")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_completed_status(self, client, seeded_data, db_engine):
        """Completed records are returned without polling external service."""
        factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            record = GeneratedResume(
                user_id=seeded_data["user_id"],
                match_id=seeded_data["match_id"],
                external_task_id="ext-task-1",
                status="completed",
                resume_pdf_path="data/resumes/resume-1.pdf",
                language="en",
                provider="anthropic",
            )
            session.add(record)
            await session.commit()
            record_id = record.id

        resp = await client.get(f"/api/resumes/{record_id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["external_task_id"] == "ext-task-1"

    @pytest.mark.asyncio
    async def test_polls_running_task(self, client, seeded_data, db_engine):
        """Running records trigger a poll to the external service."""
        factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            record = GeneratedResume(
                user_id=seeded_data["user_id"],
                match_id=seeded_data["match_id"],
                external_task_id="ext-task-poll",
                status="running",
                language="en",
                provider="anthropic",
            )
            session.add(record)
            await session.commit()
            record_id = record.id

        with (
            patch("app.routers.resumes.get_settings") as mock_settings,
            patch("app.routers.resumes.ResumeGeneratorClient") as mock_cls,
        ):
            mock_settings.return_value.resume_generator_url = "http://fake:8000"
            mock_instance = AsyncMock()
            mock_instance.get_task_status.return_value = {"status": "running"}
            mock_cls.return_value = mock_instance
            resp = await client.get(f"/api/resumes/{record_id}/status")

        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

    @pytest.mark.asyncio
    async def test_polls_and_detects_failure(self, client, seeded_data, db_engine):
        """Failed external task sets error_message in the record."""
        factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            record = GeneratedResume(
                user_id=seeded_data["user_id"],
                match_id=seeded_data["match_id"],
                external_task_id="ext-task-fail",
                status="running",
                language="en",
                provider="anthropic",
            )
            session.add(record)
            await session.commit()
            record_id = record.id

        with (
            patch("app.routers.resumes.get_settings") as mock_settings,
            patch("app.routers.resumes.ResumeGeneratorClient") as mock_cls,
        ):
            mock_settings.return_value.resume_generator_url = "http://fake:8000"
            mock_instance = AsyncMock()
            mock_instance.get_task_status.return_value = {
                "status": "failed",
                "error": "LaTeX compilation failed",
            }
            mock_cls.return_value = mock_instance
            resp = await client.get(f"/api/resumes/{record_id}/status")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "LaTeX compilation failed"


class TestDownloadEndpoints:
    @pytest.mark.asyncio
    async def test_download_resume_pdf_success(self, client, seeded_data, db_engine, tmp_path):
        """Serve a resume PDF from disk."""
        pdf_content = b"%PDF-1.4 resume content"
        pdf_file = tmp_path / "resume-test.pdf"
        pdf_file.write_bytes(pdf_content)

        factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            record = GeneratedResume(
                user_id=seeded_data["user_id"],
                match_id=seeded_data["match_id"],
                external_task_id="ext-dl-1",
                status="completed",
                resume_pdf_path=str(pdf_file),
                language="en",
                provider="anthropic",
            )
            session.add(record)
            await session.commit()
            record_id = record.id

        resp = await client.get(f"/api/resumes/{record_id}/download/resume")
        assert resp.status_code == 200
        assert resp.content == pdf_content
        assert resp.headers["content-type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_download_resume_no_path(self, client, seeded_data, db_engine):
        """404 when no PDF path is set."""
        factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            record = GeneratedResume(
                user_id=seeded_data["user_id"],
                match_id=seeded_data["match_id"],
                external_task_id="ext-dl-2",
                status="completed",
                language="en",
                provider="anthropic",
            )
            session.add(record)
            await session.commit()
            record_id = record.id

        resp = await client.get(f"/api/resumes/{record_id}/download/resume")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_download_cover_letter_success(self, client, seeded_data, db_engine, tmp_path):
        """Serve a cover letter PDF from disk."""
        pdf_content = b"%PDF-1.4 cover letter"
        pdf_file = tmp_path / "cover-letter-test.pdf"
        pdf_file.write_bytes(pdf_content)

        factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            record = GeneratedResume(
                user_id=seeded_data["user_id"],
                match_id=seeded_data["match_id"],
                external_task_id="ext-dl-3",
                status="completed",
                cover_letter_pdf_path=str(pdf_file),
                language="en",
                provider="anthropic",
            )
            session.add(record)
            await session.commit()
            record_id = record.id

        resp = await client.get(f"/api/resumes/{record_id}/download/cover-letter")
        assert resp.status_code == 200
        assert resp.content == pdf_content

    @pytest.mark.asyncio
    async def test_download_cover_letter_no_path(self, client, seeded_data, db_engine):
        """404 when no cover letter PDF path is set."""
        factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            record = GeneratedResume(
                user_id=seeded_data["user_id"],
                match_id=seeded_data["match_id"],
                external_task_id="ext-dl-4",
                status="completed",
                language="en",
                provider="anthropic",
            )
            session.add(record)
            await session.commit()
            record_id = record.id

        resp = await client.get(f"/api/resumes/{record_id}/download/cover-letter")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_download_resume_file_missing_on_disk(self, client, seeded_data, db_engine):
        """404 when the path is set but the actual file doesn't exist."""
        factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            record = GeneratedResume(
                user_id=seeded_data["user_id"],
                match_id=seeded_data["match_id"],
                external_task_id="ext-dl-5",
                status="completed",
                resume_pdf_path="/nonexistent/path/resume.pdf",
                language="en",
                provider="anthropic",
            )
            session.add(record)
            await session.commit()
            record_id = record.id

        resp = await client.get(f"/api/resumes/{record_id}/download/resume")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_download_nonexistent_record(self, client):
        """404 for nonexistent record ID."""
        resp = await client.get("/api/resumes/9999/download/resume")
        assert resp.status_code == 404


class TestByMatchEndpoint:
    @pytest.mark.asyncio
    async def test_empty(self, client, seeded_data):
        resp = await client.get(f"/api/resumes/by-match/{seeded_data['match_id']}")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_records(self, client, seeded_data, db_engine):
        factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            for i in range(2):
                record = GeneratedResume(
                    user_id=seeded_data["user_id"],
                    match_id=seeded_data["match_id"],
                    external_task_id=f"ext-task-{i}",
                    status="completed",
                    language="en",
                    provider="anthropic",
                )
                session.add(record)
            await session.commit()

        resp = await client.get(f"/api/resumes/by-match/{seeded_data['match_id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
