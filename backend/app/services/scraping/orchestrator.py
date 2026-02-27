"""Scraping orchestrator that runs all configured scrapers and indexes results.

Coordinates multiple scrapers, deduplicates results, and feeds them into
the ChromaDB vector store for the matching pipeline.
"""

import logging
from dataclasses import dataclass, field

from app.schemas.matching import JobPosting
from app.services.matching.embedder import JobEmbedder
from app.services.scraping.base import BaseScraper
from app.services.scraping.deduplicator import JobDeduplicator

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """Aggregated result from running all scrapers."""

    total: int = 0
    new: int = 0
    duplicates: int = 0
    errors: list[str] = field(default_factory=list)
    jobs: list[JobPosting] = field(default_factory=list)
    per_source: dict[str, int] = field(default_factory=dict)


class ScrapingOrchestrator:
    """Runs all scrapers, deduplicates, and indexes results."""

    def __init__(
        self,
        scrapers: list[BaseScraper],
        deduplicator: JobDeduplicator | None = None,
        embedder: JobEmbedder | None = None,
    ) -> None:
        self._scrapers = scrapers
        self._deduplicator = deduplicator or JobDeduplicator()
        self._embedder = embedder

    async def run(self, query: str, **kwargs) -> OrchestrationResult:
        """Run all scrapers, deduplicate, and optionally index results.

        Args:
            query: Job search query.
            **kwargs: Passed through to each scraper.

        Returns:
            OrchestrationResult with aggregated stats.
        """
        result = OrchestrationResult()

        # Step 1: Run all scrapers and collect raw jobs
        all_jobs: list[JobPosting] = []

        for scraper in self._scrapers:
            try:
                scraping_result = await scraper.scrape(query, **kwargs)
                all_jobs.extend(scraping_result.jobs)
                result.per_source[scraper.SOURCE] = len(scraping_result.jobs)
                result.errors.extend(scraping_result.errors)
                logger.info(
                    f"{scraper.SOURCE}: found {scraping_result.total_found}, "
                    f"normalized {len(scraping_result.jobs)}"
                )
            except Exception as e:
                logger.error(f"Scraper {scraper.SOURCE} failed: {e}")
                result.errors.append(f"{scraper.SOURCE} failed: {e}")
                result.per_source[scraper.SOURCE] = 0

        result.total = len(all_jobs)

        # Step 2: Deduplicate across sources
        unique_jobs = self._deduplicator.deduplicate(all_jobs)
        result.duplicates = result.total - len(unique_jobs)
        result.new = len(unique_jobs)
        result.jobs = unique_jobs

        logger.info(
            f"Orchestration complete: {result.total} total, "
            f"{result.new} unique, {result.duplicates} duplicates"
        )

        # Step 3: Index into ChromaDB if embedder provided
        if self._embedder is not None:
            indexed = self._embedder.index_jobs(unique_jobs)
            logger.info(f"Indexed {indexed} new jobs into ChromaDB")

        # Step 4: Close scraper clients
        for scraper in self._scrapers:
            try:
                await scraper.close()
            except Exception:
                pass

        return result
