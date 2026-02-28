"""Tests for LLM-as-Judge scoring with Claude."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.matching import JobMatchScore
from app.services.matching.scorer import JobScorer
from tests.fixtures.mock_responses import (
    make_high_match_score,
    make_low_match_score,
)


def _make_mock_scorer(return_value: JobMatchScore) -> JobScorer:
    """Create a JobScorer with a mocked LLM that returns the given score."""
    llm = MagicMock()
    # with_structured_output returns a mock that has an async ainvoke
    structured_llm = AsyncMock()
    structured_llm.ainvoke.return_value = return_value
    llm.with_structured_output.return_value = structured_llm
    return JobScorer(llm)


def _make_mock_scorer_with_quick(
    structured_return: JobMatchScore,
    quick_return_text: str = '{"relevance": 7, "reason": "Good match"}',
) -> JobScorer:
    """Create a JobScorer with both structured and raw LLM mocks."""
    llm = MagicMock()
    structured_llm = AsyncMock()
    structured_llm.ainvoke.return_value = structured_return
    llm.with_structured_output.return_value = structured_llm
    # Raw LLM ainvoke for quick_score
    raw_response = MagicMock()
    raw_response.content = quick_return_text
    llm.ainvoke = AsyncMock(return_value=raw_response)
    return JobScorer(llm)


@pytest.fixture
def scorer_with_high_match():
    return _make_mock_scorer(make_high_match_score())


@pytest.fixture
def scorer_with_low_match():
    return _make_mock_scorer(make_low_match_score())


class TestJobScorer:
    """Tests for the JobScorer."""

    async def test_score_returns_valid_pydantic(self, scorer_with_high_match):
        result = await scorer_with_high_match.score(
            resume_text="Test resume",
            job_title="Backend Engineer",
            job_company="TestCo",
            job_description="Build APIs",
        )
        assert isinstance(result, JobMatchScore)

    async def test_scores_within_range(self, scorer_with_high_match):
        result = await scorer_with_high_match.score(
            resume_text="Test resume",
            job_title="Backend Engineer",
            job_company="TestCo",
            job_description="Build APIs",
        )
        assert 1.0 <= result.overall_score <= 10.0
        assert 1 <= result.breakdown.skills <= 10
        assert 1 <= result.breakdown.experience <= 10
        assert 1 <= result.breakdown.education <= 10
        assert 1 <= result.breakdown.location <= 10
        assert 1 <= result.breakdown.salary <= 10

    async def test_missing_skills_is_list(self, scorer_with_high_match):
        result = await scorer_with_high_match.score(
            resume_text="Test resume",
            job_title="Backend Engineer",
            job_company="TestCo",
            job_description="Build APIs",
        )
        assert isinstance(result.missing_skills, list)
        for skill in result.missing_skills:
            assert isinstance(skill, str)

    async def test_strengths_is_list(self, scorer_with_high_match):
        result = await scorer_with_high_match.score(
            resume_text="Test resume",
            job_title="Backend Engineer",
            job_company="TestCo",
            job_description="Build APIs",
        )
        assert isinstance(result.strengths, list)
        assert len(result.strengths) > 0

    async def test_reasoning_is_nonempty_string(self, scorer_with_high_match):
        result = await scorer_with_high_match.score(
            resume_text="Test resume",
            job_title="Backend Engineer",
            job_company="TestCo",
            job_description="Build APIs",
        )
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0

    async def test_high_match_scores_high(self, scorer_with_high_match):
        result = await scorer_with_high_match.score(
            resume_text="Test resume",
            job_title="Backend Engineer",
            job_company="TestCo",
            job_description="Build APIs",
        )
        assert result.overall_score >= 8.0

    async def test_low_match_scores_low(self, scorer_with_low_match):
        result = await scorer_with_low_match.score(
            resume_text="Test resume",
            job_title="Marketing Coordinator",
            job_company="TestCo",
            job_description="Manage social media campaigns",
        )
        assert result.overall_score <= 4.0

    async def test_interview_talking_points_is_list(self, scorer_with_high_match):
        result = await scorer_with_high_match.score(
            resume_text="Test resume",
            job_title="Backend Engineer",
            job_company="TestCo",
            job_description="Build APIs",
        )
        assert isinstance(result.interview_talking_points, list)

    async def test_score_accepts_new_kwargs(self, scorer_with_high_match):
        """Verify the enriched prompt kwargs are accepted without error."""
        result = await scorer_with_high_match.score(
            resume_text="Test resume",
            job_title="Backend Engineer",
            job_company="TestCo",
            job_description="Build APIs",
            target_role="AI Engineer",
            experience_level="senior",
            workplace_types="remote",
            weights={"skills": 40, "experience": 25, "education": 10, "location": 15, "salary": 10},
        )
        assert isinstance(result, JobMatchScore)
        assert result.overall_score >= 1.0


class TestQuickScore:
    """Tests for the quick_score() method."""

    async def test_quick_score_returns_tuple(self):
        scorer = _make_mock_scorer_with_quick(
            make_high_match_score(),
            '{"relevance": 8, "reason": "Strong skills match"}',
        )
        relevance, reason = await scorer.quick_score(
            resume_summary="Python, FastAPI, LangChain",
            job_title="Backend Engineer",
            job_company="TestCo",
            job_description="Build APIs with Python and FastAPI",
        )
        assert isinstance(relevance, int)
        assert 1 <= relevance <= 10
        assert relevance == 8
        assert "Strong skills match" in reason

    async def test_quick_score_low_relevance(self):
        scorer = _make_mock_scorer_with_quick(
            make_high_match_score(),
            '{"relevance": 2, "reason": "Unrelated field"}',
        )
        relevance, reason = await scorer.quick_score(
            resume_summary="Python, FastAPI, LangChain",
            job_title="Marketing Manager",
            job_company="AdCo",
            job_description="Lead marketing campaigns across digital channels",
        )
        assert relevance == 2
        assert "Unrelated" in reason

    async def test_quick_score_handles_bad_json(self):
        scorer = _make_mock_scorer_with_quick(
            make_high_match_score(),
            "This is not valid JSON at all",
        )
        relevance, reason = await scorer.quick_score(
            resume_summary="Python",
            job_title="Engineer",
            job_company="Co",
            job_description="Do things",
        )
        # Should default to 5 on parse failure
        assert relevance == 5
        assert "parse" in reason.lower()

    async def test_quick_score_clamps_to_range(self):
        scorer = _make_mock_scorer_with_quick(
            make_high_match_score(),
            '{"relevance": 15, "reason": "Over the top"}',
        )
        relevance, _ = await scorer.quick_score(
            resume_summary="Python",
            job_title="Engineer",
            job_company="Co",
            job_description="Do things",
        )
        assert relevance == 10

    async def test_quick_score_truncates_long_description(self):
        scorer = _make_mock_scorer_with_quick(
            make_high_match_score(),
            '{"relevance": 7, "reason": "OK match"}',
        )
        long_desc = "x" * 1000
        relevance, _ = await scorer.quick_score(
            resume_summary="Python",
            job_title="Engineer",
            job_company="Co",
            job_description=long_desc,
        )
        # Verify it didn't error — the truncation happens inside
        assert 1 <= relevance <= 10
