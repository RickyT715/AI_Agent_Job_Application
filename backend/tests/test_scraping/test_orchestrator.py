"""Tests for the scraping orchestrator."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.matching import JobPosting
from app.services.scraping.base import ScrapingResult
from app.services.scraping.orchestrator import ScrapingOrchestrator


def _make_job(
    title: str, company: str, source: str, ext_id: str
) -> JobPosting:
    return JobPosting(
        external_id=ext_id,
        source=source,
        title=title,
        company=company,
        description=f"{title} at {company}",
    )


def _make_mock_scraper(source: str, jobs: list[JobPosting]) -> MagicMock:
    scraper = MagicMock()
    scraper.SOURCE = source
    scraper.scrape = AsyncMock(
        return_value=ScrapingResult(
            source=source,
            jobs=jobs,
            total_found=len(jobs),
        )
    )
    scraper.close = AsyncMock()
    return scraper


class TestScrapingOrchestrator:
    """Tests for the ScrapingOrchestrator."""

    async def test_runs_all_scrapers(self):
        scraper1 = _make_mock_scraper("source1", [_make_job("E1", "C1", "source1", "j1")])
        scraper2 = _make_mock_scraper("source2", [_make_job("E2", "C2", "source2", "j2")])

        orchestrator = ScrapingOrchestrator(scrapers=[scraper1, scraper2])
        result = await orchestrator.run("test query")

        scraper1.scrape.assert_called_once()
        scraper2.scrape.assert_called_once()
        assert result.total == 2

    async def test_deduplicates_across_sources(self):
        """Same job from two sources should be counted once."""
        job_from_source1 = _make_job("Engineer", "Google", "jsearch", "j1")
        job_from_source2 = _make_job("Engineer", "Google", "greenhouse", "j2")

        scraper1 = _make_mock_scraper("jsearch", [job_from_source1])
        scraper2 = _make_mock_scraper("greenhouse", [job_from_source2])

        orchestrator = ScrapingOrchestrator(scrapers=[scraper1, scraper2])
        result = await orchestrator.run("Engineer")

        assert result.total == 2
        assert result.new == 1  # Deduplicated
        assert result.duplicates == 1

    async def test_indexes_to_chromadb(self):
        """Verified embedder.index_jobs called with deduped list."""
        jobs = [_make_job("E1", "C1", "test", "j1")]
        scraper = _make_mock_scraper("test", jobs)
        mock_embedder = MagicMock()
        mock_embedder.index_jobs.return_value = 1

        orchestrator = ScrapingOrchestrator(
            scrapers=[scraper], embedder=mock_embedder
        )
        result = await orchestrator.run("query")

        mock_embedder.index_jobs.assert_called_once_with(jobs)

    async def test_returns_scraping_stats(self):
        jobs1 = [_make_job("E1", "C1", "s1", "j1"), _make_job("E2", "C2", "s1", "j2")]
        jobs2 = [_make_job("E3", "C3", "s2", "j3")]

        scraper1 = _make_mock_scraper("jsearch", jobs1)
        scraper2 = _make_mock_scraper("greenhouse", jobs2)

        orchestrator = ScrapingOrchestrator(scrapers=[scraper1, scraper2])
        result = await orchestrator.run("query")

        assert result.total == 3
        assert result.new == 3
        assert result.duplicates == 0
        assert result.per_source == {"jsearch": 2, "greenhouse": 1}

    async def test_handles_scraper_failure(self):
        """A failing scraper shouldn't break the entire orchestration."""
        good_scraper = _make_mock_scraper("good", [_make_job("E1", "C1", "good", "j1")])
        bad_scraper = MagicMock()
        bad_scraper.SOURCE = "bad"
        bad_scraper.scrape = AsyncMock(side_effect=RuntimeError("Connection failed"))
        bad_scraper.close = AsyncMock()

        orchestrator = ScrapingOrchestrator(scrapers=[good_scraper, bad_scraper])
        result = await orchestrator.run("query")

        assert len(result.jobs) == 1
        assert len(result.errors) == 1
        assert "bad failed" in result.errors[0]

    async def test_no_embedder_skips_indexing(self):
        """When no embedder provided, indexing is skipped."""
        scraper = _make_mock_scraper("test", [_make_job("E1", "C1", "test", "j1")])

        orchestrator = ScrapingOrchestrator(scrapers=[scraper], embedder=None)
        result = await orchestrator.run("query")

        assert result.new == 1

    async def test_closes_scrapers(self):
        scraper = _make_mock_scraper("test", [])

        orchestrator = ScrapingOrchestrator(scrapers=[scraper])
        await orchestrator.run("query")

        scraper.close.assert_called_once()
