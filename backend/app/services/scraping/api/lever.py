"""Lever public API scraper.

Lever postings are available at:
    https://api.lever.co/v0/postings/{company}?mode=json

No authentication required. Returns JSON array of postings.
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://api.lever.co/v0/postings"


class LeverScraper(BaseScraper):
    """Scraper for Lever public job postings."""

    SOURCE = "lever"

    def __init__(
        self,
        companies: list[str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)
        self._companies = companies or []

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape jobs from configured Lever company pages.

        Args:
            query: Not used for filtering (Lever API lists all postings).
            **kwargs: Optional 'companies' to override configured list.
        """
        companies = kwargs.get("companies", self._companies)
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()

        for company in companies:
            try:
                postings = await self._fetch_company(client, company)
                for raw in postings:
                    raw["_company_slug"] = company
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)
                result.total_found += len(postings)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limited on company {company}")
                    result.errors.append(f"Rate limited: {company}")
                else:
                    logger.error(f"HTTP error for company {company}: {e}")
                    result.errors.append(f"HTTP {e.response.status_code}: {company}")
            except httpx.HTTPError as e:
                logger.error(f"Request failed for company {company}: {e}")
                result.errors.append(f"Request failed: {company}")

        return result

    async def _fetch_company(
        self, client: httpx.AsyncClient, company: str
    ) -> list[dict]:
        """Fetch all postings for a single Lever company."""
        url = f"{BASE_URL}/{company}"
        response = await client.get(url, params={"mode": "json"})
        response.raise_for_status()
        return response.json()

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert Lever API response to JobPosting."""
        try:
            job_id = raw_data.get("id", "")
            if not job_id:
                return None

            title = raw_data.get("text", "")
            if not title:
                return None

            # Location from categories
            categories = raw_data.get("categories", {})
            location = categories.get("location")

            # Workplace type from categories
            commitment = categories.get("commitment")  # e.g., "Full-time"
            team = categories.get("team")

            # Description from lists
            description_parts = []
            lists = raw_data.get("lists", [])
            for lst in lists:
                list_text = lst.get("text", "")
                content = lst.get("content", "")
                if list_text:
                    description_parts.append(f"{list_text}: {content}")
            description = raw_data.get("descriptionPlain", "") or "\n".join(description_parts)

            # Apply URL
            apply_url = raw_data.get("applyUrl") or raw_data.get("hostedUrl", "")

            # Company from slug
            company = raw_data.get("_company_slug", "")

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=title,
                company=company,
                location=location,
                description=description,
                employment_type=commitment,
                apply_url=apply_url,
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize Lever posting: {e}")
            return None
