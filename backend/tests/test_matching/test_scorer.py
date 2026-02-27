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
