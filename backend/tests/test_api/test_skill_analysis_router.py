"""Tests for the skill-analysis API router."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.job import Job
from app.models.job_skill import JobSkill


@pytest.fixture
async def skill_seeded_client(client: AsyncClient, db_engine) -> AsyncClient:
    """Client with jobs + skills pre-populated."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        jobs = []
        for i in range(5):
            job = Job(
                external_id=f"sa-{i:03d}",
                source="test",
                title="Software Engineer",
                company=f"Co{i}",
                description=f"Python Docker description {i}",
            )
            session.add(job)
            jobs.append(job)
        await session.flush()

        for job in jobs:
            session.add(JobSkill(job_id=job.id, skill_name="python", category="technical"))
            session.add(JobSkill(job_id=job.id, skill_name="docker", category="technical"))
            session.add(JobSkill(job_id=job.id, skill_name="leadership", category="soft_skill"))
        # 3 jobs also have react
        for i in range(3):
            session.add(JobSkill(job_id=jobs[i].id, skill_name="react", category="technical"))
        await session.commit()

    return client


class TestTitleGroups:
    async def test_returns_groups(self, skill_seeded_client: AsyncClient):
        resp = await skill_seeded_client.get("/api/skill-analysis/title-groups?min_jobs=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["title"] == "software engineer"
        assert data[0]["job_count"] == 5


class TestSkillFrequencies:
    async def test_returns_frequencies(self, skill_seeded_client: AsyncClient):
        resp = await skill_seeded_client.post(
            "/api/skill-analysis/frequencies",
            json={"title_pattern": "Software Engineer", "top_n": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        skill_map = {s["skill_name"]: s for s in data}
        assert "python" in skill_map
        assert skill_map["python"]["count"] == 5

    async def test_404_for_no_match(self, skill_seeded_client: AsyncClient):
        resp = await skill_seeded_client.post(
            "/api/skill-analysis/frequencies",
            json={"title_pattern": "nonexistent-xyz-title"},
        )
        assert resp.status_code == 404


class TestSkillCoOccurrences:
    async def test_returns_co_occurrences(self, skill_seeded_client: AsyncClient):
        resp = await skill_seeded_client.post(
            "/api/skill-analysis/co-occurrences",
            json={"title_pattern": "Software Engineer", "skill_name": "python"},
        )
        assert resp.status_code == 200
        data = resp.json()
        skill_b_names = {c["skill_b"] for c in data}
        assert "docker" in skill_b_names


class TestSkillReport:
    async def test_full_report(self, skill_seeded_client: AsyncClient):
        resp = await skill_seeded_client.post(
            "/api/skill-analysis/report",
            json={"title_pattern": "Software Engineer"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_jobs"] == 5
        assert len(data["top_skills"]) > 0

    async def test_report_404(self, skill_seeded_client: AsyncClient):
        resp = await skill_seeded_client.post(
            "/api/skill-analysis/report",
            json={"title_pattern": "nonexistent-xyz-title"},
        )
        assert resp.status_code == 404


class TestBackfill:
    async def test_backfill_endpoint(self, client: AsyncClient, db_engine):
        """Backfill endpoint processes jobs that have no skills."""
        factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            job = Job(
                external_id="bf-001",
                source="test",
                title="Backend Developer",
                company="Co",
                description="Need Python and FastAPI developer with communication skills.",
            )
            session.add(job)
            await session.commit()

        resp = await client.post("/api/skill-analysis/backfill")
        assert resp.status_code == 200
        data = resp.json()
        assert data["jobs_processed"] >= 1
        assert data["total_skills"] > 0
