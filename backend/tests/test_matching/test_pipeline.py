"""Tests for the matching pipeline orchestrator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.config import UserConfig
from app.schemas.matching import JobPosting, ScoredMatch
from app.services.matching.pipeline import (
    MatchingPipeline,
    _compute_integrated_score,
    _extract_skills_section,
)
from tests.fixtures.mock_responses import make_high_match_score, make_medium_match_score


def _make_job(
    idx: int,
    title: str = "Engineer",
    company: str = "Co",
    salary_min: int | None = None,
    salary_max: int | None = None,
    **kwargs,
) -> JobPosting:
    return JobPosting(
        external_id=f"job-{idx:03d}",
        source="test",
        title=title,
        company=company,
        description=f"Job description for {title} at {company}",
        salary_min=salary_min,
        salary_max=salary_max,
        **kwargs,
    )


def _make_doc(job: JobPosting) -> Document:
    return Document(
        page_content=f"Title: {job.title}\nCompany: {job.company}\nDescription: {job.description}",
        metadata={
            "job_id": job.external_id,
            "source": job.source,
            "company": job.company,
            "title": job.title,
            "location": "",
        },
    )


@pytest.fixture
def mock_embedder():
    embedder = MagicMock()
    embedder.get_collection_count.return_value = 10
    embedder.index_jobs.return_value = 5
    embedder.vectorstore = MagicMock()
    return embedder


@pytest.fixture
def mock_scorer():
    scorer = MagicMock()
    scorer.score = AsyncMock()
    scorer.quick_score = AsyncMock(return_value=(7, "Relevant"))
    return scorer


class TestMatchingPipeline:
    """Tests for MatchingPipeline orchestration."""

    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_pipeline_returns_sorted_results(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        jobs = [_make_job(1, "Senior Engineer", "BigCo"), _make_job(2, "Junior Dev", "SmallCo")]
        docs = [_make_doc(j) for j in jobs]

        # Retriever returns 2 docs
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = docs
        mock_retriever_cls.return_value = mock_retriever_instance

        # Scorer returns different scores
        high_score = make_high_match_score()  # 8.5
        med_score = make_medium_match_score()  # 6.5
        mock_scorer.score.side_effect = [med_score, high_score]

        pipeline = MatchingPipeline(embedder=mock_embedder, scorer=mock_scorer)
        results = await pipeline.match("Resume text", jobs=jobs)

        # Results sorted descending by score
        assert len(results) == 2
        assert results[0].score.overall_score >= results[1].score.overall_score

    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_pipeline_returns_scored_matches(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        jobs = [_make_job(1)]
        docs = [_make_doc(jobs[0])]

        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = docs
        mock_retriever_cls.return_value = mock_retriever_instance

        mock_scorer.score.return_value = make_high_match_score()

        pipeline = MatchingPipeline(embedder=mock_embedder, scorer=mock_scorer)
        results = await pipeline.match("Resume text", jobs=jobs)

        assert len(results) == 1
        assert isinstance(results[0], ScoredMatch)
        assert results[0].job.external_id == "job-001"
        assert results[0].score.overall_score == 8.5

    async def test_empty_vectorstore_returns_empty(self, mock_embedder, mock_scorer):
        mock_embedder.get_collection_count.return_value = 0

        pipeline = MatchingPipeline(embedder=mock_embedder, scorer=mock_scorer)
        results = await pipeline.match("Resume text")

        assert results == []

    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_pipeline_indexes_new_jobs(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        jobs = [_make_job(1)]
        docs = [_make_doc(jobs[0])]

        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = docs
        mock_retriever_cls.return_value = mock_retriever_instance
        mock_scorer.score.return_value = make_high_match_score()

        pipeline = MatchingPipeline(embedder=mock_embedder, scorer=mock_scorer)
        await pipeline.match("Resume text", jobs=jobs)

        mock_embedder.index_jobs.assert_called_once()

    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_pipeline_handles_doc_without_job_lookup(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        """When a retrieved doc doesn't match any provided job, reconstruct from metadata."""
        orphan_doc = Document(
            page_content="Title: Unknown Job\nDescription: Some description",
            metadata={
                "job_id": "orphan-999",
                "source": "external",
                "company": "MysteryInc",
                "title": "Mystery Role",
                "location": "Remote",
            },
        )

        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = [orphan_doc]
        mock_retriever_cls.return_value = mock_retriever_instance
        mock_scorer.score.return_value = make_medium_match_score()

        pipeline = MatchingPipeline(embedder=mock_embedder, scorer=mock_scorer)
        results = await pipeline.match("Resume text")

        assert len(results) == 1
        assert results[0].job.company == "MysteryInc"

    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_pre_filter_runs_with_user_config(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        """Pre-filter should drop VP-level jobs for mid-level user."""
        user_config = UserConfig(
            experience_level="mid",
            locations=["United States"],
            employment_types=["FULLTIME"],
        )

        jobs = [
            _make_job(1, "Software Engineer", "GoodCo", location="Remote", employment_type="Full-time"),
            _make_job(2, "VP of Engineering", "BigCo", location="Remote", employment_type="Full-time"),
        ]

        # Only 1 job should survive pre-filter → only 1 doc
        filtered_doc = _make_doc(jobs[0])
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = [filtered_doc]
        mock_retriever_cls.return_value = mock_retriever_instance
        mock_scorer.score.return_value = make_high_match_score()

        pipeline = MatchingPipeline(
            embedder=mock_embedder, scorer=mock_scorer, user_config=user_config
        )
        results = await pipeline.match("Resume text", jobs=jobs, target_title="Software Engineer")

        # VP job was pre-filtered, so only 1 job was indexed
        indexed_jobs = mock_embedder.index_jobs.call_args[0][0]
        assert len(indexed_jobs) == 1
        assert indexed_jobs[0].title == "Software Engineer"

    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_target_title_passed_through(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        """target_title should influence the retrieval query."""
        jobs = [_make_job(1, "AI Engineer")]
        docs = [_make_doc(jobs[0])]

        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = docs
        mock_retriever_cls.return_value = mock_retriever_instance
        mock_scorer.score.return_value = make_high_match_score()

        pipeline = MatchingPipeline(embedder=mock_embedder, scorer=mock_scorer)
        await pipeline.match("Resume text", jobs=jobs, target_title="AI Engineer")

        # Verify retriever was called with a query containing the target title
        retrieve_call = mock_retriever_instance.retrieve.call_args[0][0]
        assert "AI Engineer" in retrieve_call

    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_quick_score_filters_low_relevance(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        """Jobs with quick_score < 4 should be skipped from full scoring."""
        jobs = [_make_job(1, "Good Job"), _make_job(2, "Bad Job")]
        docs = [_make_doc(j) for j in jobs]

        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = docs
        mock_retriever_cls.return_value = mock_retriever_instance

        # First job: high relevance, second: low
        mock_scorer.quick_score.side_effect = [(8, "Great fit"), (2, "Unrelated")]
        mock_scorer.score.return_value = make_high_match_score()

        pipeline = MatchingPipeline(embedder=mock_embedder, scorer=mock_scorer)
        results = await pipeline.match("Resume text", jobs=jobs)

        # Only 1 job should be fully scored
        assert mock_scorer.score.call_count == 1
        assert len(results) == 1


    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_ats_score_computed(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        """ATS score should be computed for each scored match."""
        jobs = [_make_job(1, "Python Developer", "TechCo")]
        jobs[0] = JobPosting(
            external_id="job-001",
            source="test",
            title="Python Developer",
            company="TechCo",
            description="We need Python, Docker, and AWS experience",
        )
        docs = [_make_doc(jobs[0])]

        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = docs
        mock_retriever_cls.return_value = mock_retriever_instance
        mock_scorer.score.return_value = make_high_match_score()

        pipeline = MatchingPipeline(embedder=mock_embedder, scorer=mock_scorer)
        results = await pipeline.match(
            "Python developer with Docker and Kubernetes experience",
            jobs=jobs,
        )

        assert len(results) == 1
        assert results[0].ats_score is not None
        assert results[0].ats_score.score >= 0.0

    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_integrated_score_computed(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        """Integrated score should be computed after ATS scoring."""
        jobs = [_make_job(1, "Engineer")]
        docs = [_make_doc(jobs[0])]

        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = docs
        mock_retriever_cls.return_value = mock_retriever_instance
        mock_scorer.score.return_value = make_high_match_score()

        pipeline = MatchingPipeline(embedder=mock_embedder, scorer=mock_scorer)
        results = await pipeline.match("Resume text", jobs=jobs)

        assert len(results) == 1
        assert results[0].integrated_score is not None
        assert 1.0 <= results[0].integrated_score <= 10.0

    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_sort_by_integrated_score(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        """Results should be sorted by integrated_score descending."""
        jobs = [_make_job(1, "Job A"), _make_job(2, "Job B")]
        docs = [_make_doc(j) for j in jobs]

        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = docs
        mock_retriever_cls.return_value = mock_retriever_instance

        high_score = make_high_match_score()
        med_score = make_medium_match_score()
        mock_scorer.score.side_effect = [med_score, high_score]

        pipeline = MatchingPipeline(embedder=mock_embedder, scorer=mock_scorer)
        results = await pipeline.match("Resume text", jobs=jobs)

        assert len(results) == 2
        assert results[0].integrated_score >= results[1].integrated_score

    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_salary_prefilter_drops_underpaying_jobs(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        """Jobs with salary_max below user's salary_min should be pre-filtered."""
        user_config = UserConfig(salary_min=150000, salary_max=250000)

        jobs = [
            _make_job(1, "Good Job", salary_min=160000, salary_max=200000),
            _make_job(2, "Bad Pay", salary_min=50000, salary_max=80000),
        ]

        filtered_doc = _make_doc(jobs[0])
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = [filtered_doc]
        mock_retriever_cls.return_value = mock_retriever_instance
        mock_scorer.score.return_value = make_high_match_score()

        pipeline = MatchingPipeline(
            embedder=mock_embedder, scorer=mock_scorer, user_config=user_config
        )
        results = await pipeline.match("Resume text", jobs=jobs)

        indexed_jobs = mock_embedder.index_jobs.call_args[0][0]
        titles = [j.title for j in indexed_jobs]
        assert "Good Job" in titles
        assert "Bad Pay" not in titles

    @patch("app.services.matching.pipeline.TwoStageRetriever")
    async def test_location_exclusion_prefilter(
        self, mock_retriever_cls, mock_embedder, mock_scorer
    ):
        """Jobs in excluded locations should be pre-filtered."""
        user_config = UserConfig(excluded_locations=["China"])

        jobs = [
            _make_job(1, "Remote Job", location="Remote"),
            _make_job(2, "China Job", location="Beijing, China"),
        ]

        filtered_doc = _make_doc(jobs[0])
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = [filtered_doc]
        mock_retriever_cls.return_value = mock_retriever_instance
        mock_scorer.score.return_value = make_high_match_score()

        pipeline = MatchingPipeline(
            embedder=mock_embedder, scorer=mock_scorer, user_config=user_config
        )
        results = await pipeline.match("Resume text", jobs=jobs)

        indexed_jobs = mock_embedder.index_jobs.call_args[0][0]
        titles = [j.title for j in indexed_jobs]
        assert "Remote Job" in titles
        assert "China Job" not in titles


class TestComputeIntegratedScore:
    """Tests for the integrated score computation helper."""

    def test_all_components(self):
        score = _compute_integrated_score(
            llm_score=8.0, ats_score=80.0, requirements_met_ratio=0.9
        )
        assert 1.0 <= score <= 10.0

    def test_no_requirements_ratio(self):
        score = _compute_integrated_score(
            llm_score=8.0, ats_score=80.0, requirements_met_ratio=None
        )
        assert 1.0 <= score <= 10.0

    def test_higher_ats_increases_score(self):
        low_ats = _compute_integrated_score(llm_score=7.0, ats_score=20.0)
        high_ats = _compute_integrated_score(llm_score=7.0, ats_score=90.0)
        assert high_ats > low_ats

    def test_higher_llm_dominates(self):
        """LLM weight (60%) should dominate."""
        low_llm = _compute_integrated_score(llm_score=3.0, ats_score=90.0)
        high_llm = _compute_integrated_score(llm_score=9.0, ats_score=20.0)
        assert high_llm > low_llm


class TestExtractSkillsSection:
    """Tests for the skills extraction helper."""

    def test_extracts_skills_from_resume(self):
        resume = """EDUCATION
University of Waterloo

SKILLS
Languages: Python, JavaScript, C++
Technologies: AWS, Docker, React

EXPERIENCE
Software Engineer at TestCo"""
        skills = _extract_skills_section(resume)
        assert "Python" in skills
        assert "JavaScript" in skills

    def test_returns_empty_for_no_skills(self):
        resume = "Just a plain paragraph with no sections."
        skills = _extract_skills_section(resume)
        assert skills == ""
