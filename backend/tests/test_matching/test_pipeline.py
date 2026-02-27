"""Tests for the matching pipeline orchestrator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.schemas.matching import JobPosting, ScoredMatch
from app.services.matching.pipeline import MatchingPipeline
from tests.fixtures.mock_responses import make_high_match_score, make_medium_match_score


def _make_job(idx: int, title: str = "Engineer", company: str = "Co") -> JobPosting:
    return JobPosting(
        external_id=f"job-{idx:03d}",
        source="test",
        title=title,
        company=company,
        description=f"Job description for {title} at {company}",
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

        mock_embedder.index_jobs.assert_called_once_with(jobs)

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
