"""Abstract base scraper defining the interface for all job scrapers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

from app.schemas.matching import JobPosting


@dataclass
class ScrapingResult:
    """Result from a single scraper run."""

    source: str
    jobs: list[JobPosting] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total_found: int = 0


class BaseScraper(ABC):
    """Abstract base class for all job scrapers.

    Subclasses must implement `scrape()` and `normalize()`.
    """

    SOURCE: str = "unknown"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    async def scrape(self, query: str, **kwargs) -> ScrapingResult:
        """Scrape jobs matching the query.

        Args:
            query: Job search query (e.g. "Software Engineer").
            **kwargs: Source-specific parameters (location, page, etc.).

        Returns:
            ScrapingResult with normalized jobs and any errors.
        """
        ...

    @abstractmethod
    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Normalize a raw API/page response into a JobPosting.

        Args:
            raw_data: Raw job data from the source.

        Returns:
            Normalized JobPosting, or None if data is invalid.
        """
        ...
