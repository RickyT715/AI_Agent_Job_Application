"""RemoteOK API scraper.

Public JSON API — no authentication required.
API: https://remoteok.com/api
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

API_URL = "https://remoteok.com/api"


class RemoteOKScraper(BaseScraper):
    """Scraper for the RemoteOK public job API."""

    SOURCE = "remoteok"

    async def scrape(self, query: str = "Software Engineer", **kwargs) -> ScrapingResult:
        """Search for jobs via RemoteOK API.

        Args:
            query: Job search query (used for client-side filtering).
            **kwargs: Optional filters (unused — RemoteOK has no query params).
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()
        query_lower = query.lower()

        try:
            response = await client.get(
                API_URL,
                headers={"User-Agent": "JobApplicationAgent/1.0"},
            )
            response.raise_for_status()
            data = response.json()

            # First item is a metadata object (legal notice), skip it
            jobs_data = data[1:] if isinstance(data, list) and len(data) > 1 else []
            result.total_found = len(jobs_data)

            for raw in jobs_data:
                # Client-side keyword filter
                title = (raw.get("position") or "").lower()
                description = (raw.get("description") or "").lower()
                tags = " ".join(t.lower() for t in (raw.get("tags") or []))
                company = (raw.get("company") or "").lower()

                if (
                    query_lower in title
                    or query_lower in description
                    or query_lower in tags
                    or query_lower in company
                ):
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)

        except httpx.HTTPStatusError as e:
            logger.error(f"RemoteOK API error: {e}")
            result.errors.append(f"HTTP {e.response.status_code}")
        except httpx.HTTPError as e:
            logger.error(f"RemoteOK request failed: {e}")
            result.errors.append(f"Request failed: {e}")

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert RemoteOK API response to JobPosting."""
        try:
            job_id = raw_data.get("id")
            if not job_id:
                return None

            title = raw_data.get("position", "")
            if not title:
                return None

            company = raw_data.get("company", "Unknown")
            location = raw_data.get("location") or "Remote"
            description = raw_data.get("description", "")

            # Tags as requirements
            tags = raw_data.get("tags", [])
            requirements = ", ".join(tags) if tags else None

            # Salary
            salary_min = raw_data.get("salary_min")
            salary_max = raw_data.get("salary_max")

            # Apply URL
            slug = raw_data.get("slug", "")
            apply_url = f"https://remoteok.com/remote-jobs/{slug}" if slug else raw_data.get("url", "")

            return JobPosting(
                external_id=str(job_id),
                source=self.SOURCE,
                title=title,
                company=company,
                location=location,
                workplace_type="remote",  # All RemoteOK jobs are remote
                description=description,
                requirements=requirements,
                salary_min=int(salary_min) if salary_min else None,
                salary_max=int(salary_max) if salary_max else None,
                apply_url=apply_url,
                raw_data=raw_data,
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to normalize RemoteOK job: {e}")
            return None
