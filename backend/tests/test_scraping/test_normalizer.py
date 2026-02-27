"""Tests for the job normalizer (JSON-LD + LLM fallback)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.matching import JobPosting
from app.services.scraping.normalizer import JobNormalizer


@pytest.fixture
def mock_llm():
    """Create a mock LLM for normalizer tests."""
    llm = MagicMock()
    structured_llm = AsyncMock()
    llm.with_structured_output.return_value = structured_llm
    return llm, structured_llm


class TestJobNormalizer:
    """Tests for the JobNormalizer."""

    async def test_jsonld_extraction_first(self, page_with_jsonld, mock_llm):
        """Page with JSON-LD should use parser, not LLM."""
        llm, structured_llm = mock_llm
        normalizer = JobNormalizer(llm=llm)
        result = await normalizer.normalize_html(page_with_jsonld, "https://example.com")
        assert result is not None
        assert result.title == "Machine Learning Engineer"
        assert result.company == "AI Corp"
        # LLM should NOT have been called
        structured_llm.ainvoke.assert_not_called()

    async def test_llm_fallback_for_messy_html(self, page_without_jsonld, mock_llm):
        """Page without JSON-LD should fall back to LLM extraction."""
        llm, structured_llm = mock_llm
        structured_llm.ainvoke.return_value = JobPosting(
            external_id="llm-extracted-001",
            source="generic",
            title="Software Engineer",
            company="Startup Inc",
            description="We are looking for a Software Engineer to join our team.",
        )
        normalizer = JobNormalizer(llm=llm)
        result = await normalizer.normalize_html(page_without_jsonld, "https://startup.com")
        assert result is not None
        assert result.title == "Software Engineer"
        # LLM should have been called
        structured_llm.ainvoke.assert_called_once()

    async def test_llm_returns_valid_job_posting(self, page_without_jsonld, mock_llm):
        """LLM extraction should return a valid JobPosting."""
        llm, structured_llm = mock_llm
        structured_llm.ainvoke.return_value = JobPosting(
            external_id="llm-001",
            source="generic",
            title="Test Engineer",
            company="TestCo",
            description="Test job description.",
            apply_url="https://startup.com",
        )
        normalizer = JobNormalizer(llm=llm)
        result = await normalizer.normalize_html(page_without_jsonld, "https://startup.com")
        assert result is not None
        assert isinstance(result, JobPosting)
        assert result.apply_url == "https://startup.com"

    async def test_handles_partial_data(self, mock_llm):
        """HTML with minimal JSON-LD should still extract what it can."""
        html = '''<html><head><script type="application/ld+json">
        {"@type": "JobPosting", "title": "Junior Dev", "description": "Entry level role.",
         "hiringOrganization": {"name": "SmallCo"}}
        </script></head><body></body></html>'''
        llm, structured_llm = mock_llm
        normalizer = JobNormalizer(llm=llm)
        result = await normalizer.normalize_html(html)
        assert result is not None
        assert result.title == "Junior Dev"
        assert result.company == "SmallCo"
        # Missing fields should be None, not errors
        assert result.location is None
        assert result.salary_min is None
