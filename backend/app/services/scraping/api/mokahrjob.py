"""MokaHR public API scraper.

MokaHR is China's equivalent of Greenhouse — used by DiDi, ByteDance subsidiaries,
and many Chinese companies. Public GET API, no auth required.

    GET https://api.mokahr.com/api-platform/v1/jobs/{orgId}
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://api.mokahr.com/api-platform/v1/jobs"


class MokaHRScraper(BaseScraper):
    """Scraper for MokaHR public job API."""

    SOURCE = "mokahr"

    def __init__(
        self,
        org_ids: list[str] | None = None,
        recruitment_type: str = "social",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)
        self._org_ids = org_ids or []
        # mode=social for 社招, mode=campus for 校招
        self._mode = "campus" if recruitment_type == "campus" else "social"

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape jobs from configured MokaHR organizations.

        Args:
            query: Search keyword (optional).
            **kwargs: Optional overrides — ``org_ids``, ``page_size``.
        """
        org_ids = kwargs.get("org_ids", self._org_ids)
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()
        page_size = kwargs.get("page_size", 30)

        for org_id in org_ids:
            try:
                jobs = await self._fetch_org(client, org_id, query, page_size)
                for raw in jobs:
                    raw["_org_id"] = org_id
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)
                result.total_found += len(jobs)
            except httpx.HTTPStatusError as e:
                logger.error(f"MokaHR HTTP error for org {org_id}: {e}")
                result.errors.append(f"HTTP {e.response.status_code}: {org_id}")
            except httpx.HTTPError as e:
                logger.error(f"MokaHR request failed for org {org_id}: {e}")
                result.errors.append(f"Request failed: {org_id}")

        return result

    async def _fetch_org(
        self,
        client: httpx.AsyncClient,
        org_id: str,
        keyword: str = "",
        limit: int = 30,
    ) -> list[dict]:
        """Fetch jobs from a single MokaHR organization."""
        url = f"{BASE_URL}/{org_id}"
        params = {
            "mode": self._mode,
            "keyword": keyword,
            "limit": str(limit),
            "offset": "0",
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", []) if isinstance(data, dict) else data

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert MokaHR API response to JobPosting."""
        try:
            title = raw_data.get("title", "") or raw_data.get("name", "")
            if not title:
                return None

            job_id = str(raw_data.get("id", ""))
            org_id = raw_data.get("_org_id", "")
            description = raw_data.get("description", "")
            requirement = raw_data.get("requirement", "")
            department = raw_data.get("department", "")
            location = raw_data.get("city", "") or raw_data.get("location", "")
            company = raw_data.get("company", org_id)

            full_description = description
            if department:
                full_description = f"Department: {department}\n{description}"

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=title,
                company=company,
                location=location or None,
                description=full_description,
                requirements=requirement or None,
                salary_currency="CNY",
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize MokaHR job: {e}")
            return None
