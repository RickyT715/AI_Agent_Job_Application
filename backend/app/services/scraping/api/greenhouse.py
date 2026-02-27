"""Greenhouse public API scraper.

Greenhouse boards expose a public JSON API at:
    https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs

No authentication required. Well-structured JSON responses.
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseScraper(BaseScraper):
    """Scraper for Greenhouse public job boards."""

    SOURCE = "greenhouse"

    def __init__(
        self,
        board_tokens: list[str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)
        self._board_tokens = board_tokens or []

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape jobs from configured Greenhouse boards.

        Args:
            query: Not used for filtering (Greenhouse API doesn't support search).
                   All jobs from the board are returned.
            **kwargs: Optional 'board_tokens' to override configured boards.
        """
        tokens = kwargs.get("board_tokens", self._board_tokens)
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()

        for token in tokens:
            try:
                jobs = await self._fetch_board(client, token)
                for raw in jobs:
                    raw["_board_token"] = token
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)
                result.total_found += len(jobs)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limited on board {token}, skipping")
                    result.errors.append(f"Rate limited: {token}")
                else:
                    logger.error(f"HTTP error for board {token}: {e}")
                    result.errors.append(f"HTTP {e.response.status_code}: {token}")
            except httpx.HTTPError as e:
                logger.error(f"Request failed for board {token}: {e}")
                result.errors.append(f"Request failed: {token}")

        return result

    async def _fetch_board(
        self, client: httpx.AsyncClient, board_token: str
    ) -> list[dict]:
        """Fetch all jobs from a single Greenhouse board."""
        url = f"{BASE_URL}/{board_token}/jobs"
        response = await client.get(url, params={"content": "true"})
        response.raise_for_status()
        data = response.json()
        return data.get("jobs", [])

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert Greenhouse API response to JobPosting."""
        try:
            job_id = str(raw_data["id"])
            title = raw_data.get("title", "")
            if not title:
                return None

            # Location from first location object
            location = None
            locations = raw_data.get("location", {})
            if isinstance(locations, dict):
                location = locations.get("name")

            # Description from content field (HTML)
            content = raw_data.get("content", "")
            # Strip simple HTML tags for plain text
            description = _strip_html(content)

            # Apply URL
            board_token = raw_data.get("_board_token", "")
            apply_url = raw_data.get(
                "absolute_url",
                f"https://boards.greenhouse.io/{board_token}/jobs/{job_id}",
            )

            # Company from board metadata (if available) or board token
            company = raw_data.get("company_name", board_token)

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=title,
                company=company,
                location=location,
                description=description,
                apply_url=apply_url,
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize Greenhouse job: {e}")
            return None


def _strip_html(html: str) -> str:
    """Simple HTML tag stripping for descriptions."""
    import re

    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text
