"""Arbeitnow API scraper.

Public job board API — no authentication required.
API docs: https://www.arbeitnow.com/api/job-board-api
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowScraper(BaseScraper):
    """Scraper for the Arbeitnow public job board API."""

    SOURCE = "arbeitnow"

    async def scrape(self, query: str = "Software Engineer", **kwargs) -> ScrapingResult:
        """Search for jobs via Arbeitnow API.

        Args:
            query: Job search query (used for client-side filtering).
            **kwargs: Optional filters:
                - num_pages: Number of pages to fetch (default: 1).
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()
        num_pages = kwargs.get("num_pages", 1)
        query_lower = query.lower()

        for page in range(1, num_pages + 1):
            try:
                params: dict[str, int] = {"page": page}
                response = await client.get(BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                jobs_data = data.get("data", [])

                for raw in jobs_data:
                    # Client-side keyword filter since API doesn't support query
                    title = (raw.get("title") or "").lower()
                    description = (raw.get("description") or "").lower()
                    tags = " ".join(t.lower() for t in (raw.get("tags") or []))

                    if query_lower in title or query_lower in description or query_lower in tags:
                        posting = self.normalize(raw)
                        if posting:
                            result.jobs.append(posting)

                result.total_found += len(jobs_data)

                # Check pagination
                if not jobs_data or not data.get("links", {}).get("next"):
                    break

            except httpx.HTTPStatusError as e:
                logger.error(f"Arbeitnow API error (page {page}): {e}")
                result.errors.append(f"HTTP {e.response.status_code} on page {page}")
                break
            except httpx.HTTPError as e:
                logger.error(f"Arbeitnow request failed (page {page}): {e}")
                result.errors.append(f"Request failed on page {page}")
                break

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert Arbeitnow API response to JobPosting."""
        try:
            slug = raw_data.get("slug", "")
            if not slug:
                return None

            title = raw_data.get("title", "")
            if not title:
                return None

            company = raw_data.get("company_name", "Unknown")
            location = raw_data.get("location") or None
            description = raw_data.get("description", "")
            apply_url = raw_data.get("url", "")

            # Remote detection
            is_remote = raw_data.get("remote", False)
            workplace_type = "remote" if is_remote else None

            # Tags as requirements
            tags = raw_data.get("tags", [])
            requirements = ", ".join(tags) if tags else None

            return JobPosting(
                external_id=slug,
                source=self.SOURCE,
                title=title,
                company=company,
                location=location,
                workplace_type=workplace_type,
                description=description,
                requirements=requirements,
                apply_url=apply_url,
                raw_data=raw_data,
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to normalize Arbeitnow job: {e}")
            return None
