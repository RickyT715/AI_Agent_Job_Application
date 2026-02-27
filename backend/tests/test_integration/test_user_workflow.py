"""Comprehensive real-user workflow integration test.

Simulates the entire user journey through the system:
  1. Upload resume
  2. Configure preferences
  3. Scrape jobs (mocked external APIs, real orchestrator)
  4. View jobs in DB
  5. Run matching pipeline (mocked LLM scoring, real retrieval)
  6. View scored matches
  7. Generate report (HTML)
  8. Generate cover letter
  9. Start browser agent, review, approve
  10. Verify application recorded

All external services (LLMs, scraper APIs) are mocked.
All internal code paths (DB, routers, services, agent graph) are real.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_db_session
from app.main import app
from app.models.base import Base
from app.models.application import Application
from app.models.cover_letter import CoverLetter
from app.models.job import Job
from app.models.match import MatchResult
from app.models.user import User
from app.schemas.matching import JobPosting, JobMatchScore, ScoreBreakdown
from app.services.agent.graph import compile_agent_graph
from app.services.agent.state import make_initial_state
from app.services.matching.embedder import JobEmbedder
from app.services.matching.scorer import JobScorer
from app.services.reports.cover_letter import CoverLetterGenerator
from app.services.reports.evaluation import skill_match_f1, score_accuracy
from app.services.reports.generator import ReportGenerator
from app.services.scraping.base import ScrapingResult
from app.services.scraping.deduplicator import JobDeduplicator
from app.services.scraping.orchestrator import ScrapingOrchestrator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_RESUME = """
John Doe
Senior Software Engineer | San Francisco, CA
john.doe@email.com | (555) 123-4567 | linkedin.com/in/johndoe

SUMMARY
6+ years of experience building scalable backend systems with Python, FastAPI,
and PostgreSQL. Led migration to microservices at TechCo, reducing deploy time
by 70%. Passionate about AI/ML pipeline architecture and cloud deployment.

SKILLS
Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, AWS, CI/CD,
SQLAlchemy, Celery, REST APIs, GraphQL, Machine Learning, LangChain

EXPERIENCE
Senior Backend Engineer | TechCo | 2021-Present
- Architected microservices handling 10K+ RPM with FastAPI + PostgreSQL
- Built ML inference pipeline processing 1M predictions/day
- Led team of 4 engineers, introduced code review culture

Backend Engineer | StartupXYZ | 2018-2021
- Built core API from scratch using Python/Django, migrated to FastAPI
- Implemented real-time WebSocket messaging for 50K concurrent users
- Set up CI/CD with GitHub Actions + Docker + AWS ECS

EDUCATION
B.S. Computer Science | UC Berkeley | 2018
"""

SAMPLE_JOBS = [
    JobPosting(
        external_id="job-001",
        source="jsearch",
        title="Senior Python Engineer",
        company="CloudScale Inc.",
        location="Remote",
        description=(
            "We're looking for a Senior Python Engineer to build scalable APIs. "
            "You'll work with FastAPI, PostgreSQL, Redis, and Docker. "
            "5+ years of Python experience required. Machine learning a plus."
        ),
        requirements="Python 5+ years, FastAPI, PostgreSQL, Docker",
        salary_min=140000,
        salary_max=190000,
        salary_currency="USD",
        employment_type="full-time",
        apply_url="https://boards.greenhouse.io/cloudscale/jobs/001",
    ),
    JobPosting(
        external_id="job-002",
        source="jsearch",
        title="Full-Stack Developer",
        company="WebAgency",
        location="New York, NY",
        description=(
            "Full-stack role building React + Node.js applications. "
            "Experience with TypeScript, Next.js, and MongoDB required. "
            "2+ years experience."
        ),
        requirements="React, Node.js, TypeScript, MongoDB",
        employment_type="full-time",
        apply_url="https://jobs.lever.co/webagency/002",
    ),
    JobPosting(
        external_id="job-003",
        source="jsearch",
        title="ML Platform Engineer",
        company="AIStartup",
        location="Remote",
        description=(
            "Build ML infrastructure with Python, Kubernetes, and MLflow. "
            "Strong backend skills required. Experience with LangChain and "
            "vector databases a huge plus. 4+ years."
        ),
        requirements="Python, Kubernetes, MLflow, Docker, AWS",
        salary_min=160000,
        salary_max=210000,
        salary_currency="USD",
        employment_type="full-time",
        apply_url="https://aistartup.com/careers/003",
    ),
    JobPosting(
        external_id="job-004",
        source="greenhouse",
        title="Junior Data Analyst",
        company="Analytics Corp",
        location="Chicago, IL",
        description=(
            "Entry-level data analyst position. Excel, SQL, Tableau. "
            "No programming required. Fresh graduates welcome."
        ),
        requirements="Excel, SQL, Tableau",
        employment_type="full-time",
        apply_url="https://boards.greenhouse.io/analyticscorp/jobs/004",
    ),
    JobPosting(
        external_id="job-005",
        source="lever",
        title="DevOps Engineer",
        company="InfraTeam",
        location="Remote",
        description=(
            "Manage CI/CD pipelines, Kubernetes clusters, and cloud infra. "
            "Terraform, AWS, Docker, Python scripting. 3+ years."
        ),
        requirements="Kubernetes, Terraform, AWS, Docker, Python",
        salary_min=130000,
        salary_max=170000,
        salary_currency="USD",
        employment_type="full-time",
        apply_url="https://jobs.lever.co/infrateam/005",
    ),
]


@pytest.fixture
async def db_engine():
    """Isolated in-memory SQLite for the workflow test."""
    engine = create_async_engine("sqlite+aiosqlite:///", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_factory(db_engine):
    """Session factory for the workflow test."""
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def api_client(db_engine, db_factory) -> AsyncClient:
    """HTTP client connected to test database."""
    async def _override():
        async with db_factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db_session] = _override

    # Mock ARQ pool
    mock_job = MagicMock()
    mock_job.job_id = "wf-task-001"
    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=mock_job)
    app.state.arq_pool = mock_pool

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
    app.state.arq_pool = None


# ---------------------------------------------------------------------------
# Phase 1: Resume upload & preferences
# ---------------------------------------------------------------------------

class TestStep1_ResumeAndConfig:
    """Step 1: User uploads resume and configures preferences."""

    async def test_upload_resume(self, api_client: AsyncClient):
        resp = await api_client.post(
            "/api/config/resume",
            files={"file": ("resume.txt", SAMPLE_RESUME.encode())},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Resume uploaded successfully"
        assert data["character_count"] > 500  # Real resume content

    async def test_get_default_preferences(self, api_client: AsyncClient):
        resp = await api_client.get("/api/config/preferences")
        assert resp.status_code == 200
        prefs = resp.json()
        assert "job_titles" in prefs
        assert "weights" in prefs
        assert isinstance(prefs["weights"], dict)

    async def test_health_check(self, api_client: AsyncClient):
        resp = await api_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


# ---------------------------------------------------------------------------
# Phase 2: Job scraping (mocked external, real orchestrator)
# ---------------------------------------------------------------------------

class TestStep2_JobScraping:
    """Step 2: Scrape jobs using mocked APIs but real orchestrator/dedup."""

    async def test_scraping_orchestrator_processes_jobs(self):
        """Run the real orchestrator with a mocked scraper."""
        mock_scraper = MagicMock()
        mock_scraper.SOURCE = "jsearch"
        mock_scraper.scrape = AsyncMock(return_value=ScrapingResult(
            source="jsearch",
            jobs=SAMPLE_JOBS,
            errors=[],
            total_found=5,
        ))
        mock_scraper.close = AsyncMock()

        dedup = JobDeduplicator()
        orchestrator = ScrapingOrchestrator(
            scrapers=[mock_scraper],
            deduplicator=dedup,
        )

        result = await orchestrator.run("Software Engineer", location="Remote")

        assert result.total == 5
        assert result.new == 5
        assert result.duplicates == 0
        assert len(result.jobs) == 5

    async def test_deduplicator_catches_duplicates(self):
        """Verify dedup across sources works."""
        dedup = JobDeduplicator()
        jobs_with_dup = SAMPLE_JOBS + [
            JobPosting(
                external_id="job-001-dup",
                source="greenhouse",
                title="Senior Python Engineer",
                company="CloudScale Inc.",  # Same company+title+location
                location="Remote",
                description="Duplicate posting on another board",
            ),
        ]
        unique = dedup.deduplicate(jobs_with_dup)
        assert len(unique) == 5  # 6 input, 1 duplicate removed

    async def test_trigger_scraping_via_api(self, api_client: AsyncClient):
        """POST /api/jobs/scrape returns task status."""
        resp = await api_client.post(
            "/api/jobs/scrape",
            json={"queries": ["Python Engineer"], "location": "Remote"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"


# ---------------------------------------------------------------------------
# Phase 3: Store jobs in DB and verify retrieval
# ---------------------------------------------------------------------------

class TestStep3_JobStorage:
    """Step 3: Seed jobs into DB and verify API retrieval."""

    async def test_seed_and_list_jobs(self, api_client: AsyncClient, db_factory):
        """Seed 5 jobs, verify GET /api/jobs returns them."""
        async with db_factory() as session:
            for jp in SAMPLE_JOBS:
                job = Job(
                    external_id=jp.external_id,
                    source=jp.source,
                    title=jp.title,
                    company=jp.company,
                    location=jp.location,
                    description=jp.description,
                    requirements=jp.requirements,
                    salary_min=jp.salary_min,
                    salary_max=jp.salary_max,
                    salary_currency=jp.salary_currency,
                    employment_type=jp.employment_type,
                    apply_url=jp.apply_url,
                    workplace_type="remote" if jp.location == "Remote" else "onsite",
                )
                session.add(job)
            await session.commit()

        resp = await api_client.get("/api/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5

        # Verify pagination
        resp2 = await api_client.get("/api/jobs", params={"limit": 2})
        assert len(resp2.json()["items"]) == 2

    async def test_get_single_job(self, api_client: AsyncClient, db_factory):
        """Seed job, GET /api/jobs/{id} returns full details."""
        async with db_factory() as session:
            job = Job(
                external_id="single-test",
                source="test",
                title="Test Engineer",
                company="TestCo",
                description="Test description",
            )
            session.add(job)
            await session.commit()
            job_id = job.id

        resp = await api_client.get(f"/api/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test Engineer"

    async def test_get_nonexistent_job_returns_404(self, api_client: AsyncClient):
        resp = await api_client.get("/api/jobs/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Phase 4: Matching pipeline (mocked LLM, real scorer logic)
# ---------------------------------------------------------------------------

class TestStep4_MatchingPipeline:
    """Step 4: Score jobs against the resume."""

    async def test_scorer_with_mocked_llm(self):
        """Real scorer logic with a mock LLM that returns structured output."""
        mock_score = JobMatchScore(
            overall_score=8.5,
            breakdown=ScoreBreakdown(skills=9, experience=8, education=7, location=9, salary=8),
            reasoning="Strong match for Python and FastAPI skills.",
            strengths=["Python expertise", "FastAPI experience", "Cloud deployment"],
            missing_skills=["Kubernetes"],
            interview_talking_points=["Discuss ML pipeline architecture"],
        )

        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_structured.ainvoke = AsyncMock(return_value=mock_score)
        mock_llm.with_structured_output = MagicMock(return_value=mock_structured)

        scorer = JobScorer(llm=mock_llm)
        result = await scorer.score(
            resume_text=SAMPLE_RESUME,
            job_title="Senior Python Engineer",
            job_company="CloudScale Inc.",
            job_description="Build scalable APIs with FastAPI, PostgreSQL.",
            job_location="Remote",
            job_requirements="Python 5+ years, FastAPI",
            job_salary="$140,000 - $190,000",
            preferred_locations="Remote",
            salary_range="$120,000 - $180,000",
        )

        assert result.overall_score == 8.5
        assert result.breakdown.skills == 9
        assert "Python expertise" in result.strengths
        assert "Kubernetes" in result.missing_skills

    async def test_seed_matches_and_verify_api(self, api_client: AsyncClient, db_factory):
        """Seed scored matches, verify API returns them sorted."""
        async with db_factory() as session:
            user = User(email="test@workflow.com", full_name="John Doe", resume_text=SAMPLE_RESUME)
            session.add(user)
            await session.flush()

            # Create jobs and corresponding matches with realistic scores
            scores_data = [
                ("Senior Python Engineer", "CloudScale Inc.", 8.5),
                ("ML Platform Engineer", "AIStartup", 7.8),
                ("DevOps Engineer", "InfraTeam", 6.5),
                ("Full-Stack Developer", "WebAgency", 4.2),
                ("Junior Data Analyst", "Analytics Corp", 2.1),
            ]

            for i, (title, company, score) in enumerate(scores_data):
                job = Job(
                    external_id=f"wf-{i:03d}",
                    source="test",
                    title=title,
                    company=company,
                    description=f"Job description for {title}",
                    location="Remote",
                )
                session.add(job)
                await session.flush()

                match = MatchResult(
                    user_id=user.id,
                    job_id=job.id,
                    overall_score=score,
                    score_breakdown={
                        "skills": int(score),
                        "experience": int(score) - 1,
                        "education": 7,
                        "location": 8,
                        "salary": 7,
                    },
                    reasoning=f"{'Strong' if score >= 7 else 'Weak'} match for {title}",
                    strengths=["Python"] if score >= 7 else [],
                    missing_skills=["Kubernetes"] if score < 9 else [],
                    interview_talking_points=["Talk about ML"] if score >= 7 else [],
                )
                session.add(match)
            await session.commit()

        # Verify matches sorted by score DESC
        resp = await api_client.get("/api/matches")
        assert resp.status_code == 200
        matches = resp.json()["items"]
        assert len(matches) == 5
        scores = [m["overall_score"] for m in matches]
        assert scores == sorted(scores, reverse=True), f"Not sorted: {scores}"

        # Top match should be CloudScale
        assert matches[0]["overall_score"] == 8.5

        # Verify min_score filter
        resp2 = await api_client.get("/api/matches", params={"min_score": 7.0})
        filtered = resp2.json()["items"]
        assert all(m["overall_score"] >= 7.0 for m in filtered)
        assert len(filtered) == 2  # 8.5 and 7.8

        # Verify match detail
        match_id = matches[0]["id"]
        resp3 = await api_client.get(f"/api/matches/{match_id}")
        assert resp3.status_code == 200
        detail = resp3.json()
        assert "reasoning" in detail
        assert "strengths" in detail
        assert "missing_skills" in detail
        assert detail["reasoning"].startswith("Strong")


# ---------------------------------------------------------------------------
# Phase 5: Report generation
# ---------------------------------------------------------------------------

class TestStep5_ReportGeneration:
    """Step 5: Generate HTML report and cover letter."""

    def test_html_report_for_top_match(self):
        """Generate a full HTML report for the top-scored job."""
        gen = ReportGenerator()
        html = gen.render_html(
            job_title="Senior Python Engineer",
            company="CloudScale Inc.",
            overall_score=8.5,
            breakdown={"skills": 9, "experience": 8, "education": 7, "location": 9, "salary": 8},
            reasoning="Strong match due to extensive Python and FastAPI experience.",
            strengths=["Python expertise", "FastAPI experience", "Cloud deployment"],
            missing_skills=["Kubernetes"],
            interview_talking_points=["Discuss ML pipeline architecture"],
            salary_min=140000,
            salary_max=190000,
            salary_currency="USD",
        )

        # Verify all sections present
        assert "Senior Python Engineer" in html
        assert "CloudScale Inc." in html
        assert "8.5" in html
        assert "Python expertise" in html
        assert "Kubernetes" in html
        assert "Discuss ML pipeline" in html
        assert "140000" in html or "140,000" in html
        assert "score-green" in html  # Score >= 8

    def test_html_report_for_low_match(self):
        """Low-score report renders with red styling."""
        gen = ReportGenerator()
        html = gen.render_html(
            job_title="Junior Data Analyst",
            company="Analytics Corp",
            overall_score=2.1,
            breakdown={"skills": 2, "experience": 1},
            reasoning="Poor match — completely different skill set.",
            strengths=[],
            missing_skills=["Excel", "Tableau", "SQL reporting"],
        )

        assert "Junior Data Analyst" in html
        assert "score-red" in html  # Score < 6

    def test_pdf_generation_returns_bytes(self):
        """generate_pdf returns bytes (PDF or HTML fallback)."""
        gen = ReportGenerator()
        pdf_bytes = gen.generate_pdf(
            job_title="Test",
            company="Test Co",
            overall_score=7.0,
            breakdown={"skills": 7},
            reasoning="OK match.",
            strengths=["Python"],
            missing_skills=[],
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100

    async def test_cover_letter_chain_with_mock_llm(self):
        """Full cover letter generation with mocked Claude."""
        expected_letter = (
            "Dear Hiring Manager,\n\n"
            "I am writing to express my enthusiastic interest in the Senior Python "
            "Engineer position at CloudScale Inc. With over 6 years of experience "
            "building scalable backend systems with Python and FastAPI, I am confident "
            "that my skills align well with your requirements.\n\n"
            "Best regards,\nJohn Doe"
        )

        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=expected_letter)

        gen = CoverLetterGenerator()
        with patch.object(gen, "_build_chain", return_value=mock_chain):
            letter = await gen.generate(
                job_title="Senior Python Engineer",
                company="CloudScale Inc.",
                job_description="Build scalable APIs with FastAPI, PostgreSQL.",
                resume_text=SAMPLE_RESUME,
                strengths=["Python expertise", "FastAPI experience"],
                missing_skills=["Kubernetes"],
            )

        assert "Senior Python Engineer" in letter or "CloudScale" in letter
        assert len(letter) > 100

    async def test_report_api_endpoint(self, api_client: AsyncClient, db_factory):
        """POST /api/reports/generate with a seeded match."""
        async with db_factory() as session:
            user = User(email="report@test.com", full_name="Report User", resume_text="test")
            session.add(user)
            await session.flush()

            job = Job(
                external_id="report-job",
                source="test",
                title="Test Job",
                company="Test Co",
                description="desc",
            )
            session.add(job)
            await session.flush()

            match = MatchResult(
                user_id=user.id,
                job_id=job.id,
                overall_score=8.0,
                score_breakdown={"skills": 8},
                reasoning="Good",
                strengths=["Python"],
                missing_skills=[],
            )
            session.add(match)
            await session.commit()
            match_id = match.id

        resp = await api_client.post(
            "/api/reports/generate",
            json={"match_id": match_id},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "complete"

    async def test_cover_letter_api_endpoint(self, api_client: AsyncClient, db_factory):
        """POST /api/reports/cover-letter stores a cover letter."""
        async with db_factory() as session:
            user = User(email="cl@test.com", full_name="CL User", resume_text="test")
            session.add(user)
            await session.flush()

            job = Job(
                external_id="cl-job",
                source="test",
                title="CL Job",
                company="CL Co",
                description="desc",
            )
            session.add(job)
            await session.flush()

            match = MatchResult(
                user_id=user.id,
                job_id=job.id,
                overall_score=7.5,
                score_breakdown={"skills": 7},
                reasoning="OK match",
                strengths=["SQL"],
                missing_skills=[],
            )
            session.add(match)
            await session.commit()
            match_id = match.id

        # Mock the cover letter generator to avoid calling real LLM
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value="Dear Hiring Manager, I am a great fit.")

        with patch("app.routers.reports.CoverLetterGenerator") as mock_gen_cls:
            mock_gen = MagicMock()
            mock_gen.generate = AsyncMock(return_value="Dear Hiring Manager, I am a great fit.")
            mock_gen_cls.return_value = mock_gen

            resp = await api_client.post(
                "/api/reports/cover-letter",
                json={"match_id": match_id},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["match_id"] == match_id
        assert "content" in data


# ---------------------------------------------------------------------------
# Phase 6: Evaluation metrics
# ---------------------------------------------------------------------------

class TestStep6_EvaluationMetrics:
    """Step 6: Validate quality metrics against our sample data."""

    def test_skill_match_for_top_job(self):
        """Our resume's skills vs top job's requirements."""
        predicted = ["python", "fastapi", "postgresql", "docker", "redis"]
        expected = ["python", "fastapi", "postgresql", "docker"]
        f1 = skill_match_f1(predicted, expected)
        assert f1 > 0.85  # Almost perfect match

    def test_skill_match_for_weak_job(self):
        """Our resume's skills vs data analyst requirements."""
        predicted = ["python", "fastapi", "postgresql"]
        expected = ["excel", "sql", "tableau"]
        f1 = skill_match_f1(predicted, expected)
        assert f1 == 0.0  # No overlap

    def test_score_accuracy_top_match(self):
        """Score of 8.5 is within tolerance of expected 8.0."""
        assert score_accuracy(8.5, 8.0, tolerance=1.0) == 1.0

    def test_score_accuracy_bad_prediction(self):
        """Score of 8.5 for a 2.1-expected job is way off."""
        assert score_accuracy(8.5, 2.1, tolerance=1.0) == 0.0


# ---------------------------------------------------------------------------
# Phase 7: Browser agent (mocked browser, real graph)
# ---------------------------------------------------------------------------

class TestStep7_BrowserAgent:
    """Step 7: Run agent graph through detect → fill → review → submit."""

    async def test_agent_full_cycle_approve(self):
        """Full agent flow: detect ATS → api_submit for Greenhouse."""
        graph = compile_agent_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "workflow-approve"}}

        state = make_initial_state(
            job_id=1,
            apply_url="https://boards.greenhouse.io/cloudscale/jobs/001",
            job_title="Senior Python Engineer",
            company="CloudScale Inc.",
            user_profile={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@email.com",
                "phone": "(555) 123-4567",
                "linkedin_url": "linkedin.com/in/johndoe",
            },
            resume_text=SAMPLE_RESUME,
        )

        # Mock the GreenhouseSubmitter for api_submit
        mock_submitter = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.message = "OK"
        mock_submitter.submit = AsyncMock(return_value=mock_result)

        with patch("app.services.agent.nodes.GreenhouseSubmitter", return_value=mock_submitter):
            result = await graph.ainvoke(state, config)

        assert result["ats_platform"] == "greenhouse"
        assert result["status"] == "submitted"

    async def test_agent_generic_site_with_review(self):
        """Generic site flow requires browser → fills → pauses for review."""
        from langgraph.types import Command

        graph = compile_agent_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "workflow-generic"}}

        state = make_initial_state(
            job_id=3,
            apply_url="https://aistartup.com/careers/003",
            job_title="ML Platform Engineer",
            company="AIStartup",
            user_profile={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@email.com",
            },
            resume_text=SAMPLE_RESUME,
        )

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=None)
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()

        with (
            patch("app.services.agent.nodes.Agent", return_value=mock_agent),
            patch("app.services.agent.nodes.Browser", return_value=mock_browser),
            patch("app.services.agent.nodes.get_llm", return_value=MagicMock()),
        ):
            result = await graph.ainvoke(state, config)
            assert result["ats_platform"] == "generic"
            assert result["status"] == "filling"

            final = await graph.ainvoke(
                Command(resume={"action": "approve"}), config
            )
            assert final["status"] == "submitted"

    async def test_agent_reject_aborts(self):
        """User rejects → agent aborts gracefully."""
        from langgraph.types import Command

        graph = compile_agent_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "workflow-reject"}}

        state = make_initial_state(
            job_id=3,
            apply_url="https://aistartup.com/careers/003",
            job_title="ML Platform Engineer",
            company="AIStartup",
            user_profile={"first_name": "John", "email": "john@test.com"},
        )

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=None)
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()

        with (
            patch("app.services.agent.nodes.Agent", return_value=mock_agent),
            patch("app.services.agent.nodes.Browser", return_value=mock_browser),
            patch("app.services.agent.nodes.get_llm", return_value=MagicMock()),
        ):
            await graph.ainvoke(state, config)

            final = await graph.ainvoke(
                Command(resume={"action": "reject"}), config
            )
            assert final["status"] == "aborted"

    async def test_agent_api_endpoints(self, api_client: AsyncClient):
        """POST /api/agent/start and /resume endpoints work."""
        resp = await api_client.post(
            "/api/agent/start",
            json={"job_id": 1},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        task_id = data["task_id"]

        resp2 = await api_client.post(
            f"/api/agent/resume/{task_id}",
            json={"action": "approve"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "running"


# ---------------------------------------------------------------------------
# Phase 8: MCP server tools
# ---------------------------------------------------------------------------

class TestStep8_MCPServer:
    """Step 8: Verify MCP tools work end-to-end."""

    async def test_mcp_tools_list(self):
        """All 5 MCP tools are registered."""
        from app.mcp.server import mcp

        tools = await mcp.list_tools()
        names = [t.name for t in tools]
        assert len(names) == 5
        assert "search_jobs" in names
        assert "generate_report" in names
        assert "fill_application" in names

    async def test_mcp_generate_report_tool(self):
        """MCP generate_report produces HTML."""
        from app.mcp.server import mcp

        result = await mcp.call_tool("generate_report", {
            "job_title": "Senior Python Engineer",
            "company": "CloudScale Inc.",
            "overall_score": 8.5,
            "breakdown": {"skills": 9, "experience": 8, "education": 7},
            "reasoning": "Strong Python match.",
            "strengths": ["Python", "FastAPI"],
            "missing_skills": ["Kubernetes"],
        })
        text = result.content[0].text
        assert "html" in text.lower()
        assert "CloudScale" in text

    async def test_mcp_resources(self):
        """MCP resources return content."""
        from app.mcp.server import mcp

        resources = await mcp.list_resources()
        assert len(resources) == 2

        prefs = await mcp.read_resource("preferences://job-search")
        content = prefs.contents[0].content
        assert "job_titles" in content

    async def test_mcp_fill_application_dry_run(self):
        """MCP fill_application in dry_run mode detects ATS."""
        from app.mcp.server import mcp

        with (
            patch("app.mcp.server._load_resume_text", return_value=SAMPLE_RESUME),
            patch("app.mcp.server._load_user_config"),
        ):
            result = await mcp.call_tool("fill_application", {
                "apply_url": "https://boards.greenhouse.io/cloudscale/jobs/001",
            })
        text = result.content[0].text
        assert "greenhouse" in text.lower()
        assert "preview" in text.lower() or "dry_run" in text.lower()


# ---------------------------------------------------------------------------
# Phase 9: Docker Compose validation
# ---------------------------------------------------------------------------

class TestStep9_DockerConfig:
    """Step 9: Validate deployment configuration."""

    def test_docker_compose_valid(self):
        """docker-compose.yml has all required services."""
        import yaml
        from pathlib import Path

        compose_path = Path(__file__).parent.parent.parent.parent / "docker-compose.yml"
        assert compose_path.exists(), f"docker-compose.yml not found at {compose_path}"

        with open(compose_path) as f:
            config = yaml.safe_load(f)

        services = config["services"]
        assert "backend" in services
        assert "worker" in services
        assert "frontend" in services
        assert "db" in services
        assert "redis" in services

        # Backend depends on healthy DB
        assert services["backend"]["depends_on"]["db"]["condition"] == "service_healthy"

    def test_github_actions_workflow_exists(self):
        """CI workflow file exists."""
        from pathlib import Path

        ci_path = Path(__file__).parent.parent.parent.parent / ".github" / "workflows" / "ci.yml"
        assert ci_path.exists()

        with open(ci_path) as f:
            import yaml
            config = yaml.safe_load(f)

        assert "jobs" in config
        assert "backend" in config["jobs"]
        assert "frontend" in config["jobs"]
        assert "docker" in config["jobs"]
