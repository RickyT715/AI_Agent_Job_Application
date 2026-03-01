"""Alibaba Careers API scraper.

Uses the Alibaba talent platform API (requires free app_key registration):
    alibaba.recruit.website.jobs.search
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://talent.alibaba.com/off-campus/position-list"
API_URL = "https://talent.alibaba.com/pubapis/position/search"


class AlibabaScraper(BaseScraper):
    """Scraper for Alibaba Careers API."""

    SOURCE = "alibaba"

    def __init__(
        self,
        recruitment_type: str = "social",
        app_key: str = "",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)
        self._recruitment_type = recruitment_type
        self._app_key = app_key

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape jobs from Alibaba Careers.

        Args:
            query: Search keyword.
            **kwargs: Optional overrides — ``num_pages``, ``page_size``.
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()

        num_pages = kwargs.get("num_pages", 1)
        page_size = kwargs.get("page_size", 20)

        for page in range(1, num_pages + 1):
            try:
                payload = {
                    "keyword": query,
                    "pageIndex": page,
                    "pageSize": page_size,
                    "category": "technology" if not query else "",
                }
                if self._recruitment_type == "campus":
                    payload["channel"] = "campus"

                response = await client.post(
                    API_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

                records = data.get("data", {}).get("records", [])
                total = data.get("data", {}).get("total", len(records))
                result.total_found += total

                for raw in records:
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)

            except httpx.HTTPStatusError as e:
                logger.error(f"Alibaba API HTTP error: {e}")
                result.errors.append(f"HTTP {e.response.status_code}")
            except httpx.HTTPError as e:
                logger.error(f"Alibaba API request failed: {e}")
                result.errors.append(f"Request failed: {e}")

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert Alibaba API response to JobPosting."""
        try:
            name = raw_data.get("name", "")
            if not name:
                return None

            code = str(raw_data.get("code", raw_data.get("id", "")))
            locations = raw_data.get("workLocations", [])
            if isinstance(locations, list):
                location = ", ".join(str(loc) for loc in locations)
            else:
                location = str(locations) if locations else None

            category = raw_data.get("category", "")
            department = raw_data.get("deptName", "")
            description = raw_data.get("description", "")
            requirement = raw_data.get("requirement", "")

            full_description = description
            if department:
                full_description = f"Department: {department}\n{description}"
            if category:
                full_description = f"Category: {category}\n{full_description}"

            return JobPosting(
                external_id=code,
                source=self.SOURCE,
                title=name,
                company="Alibaba Group",
                location=location or None,
                description=full_description,
                requirements=requirement or None,
                salary_currency="CNY",
                apply_url=f"https://talent.alibaba.com/off-campus/position-detail?positionId={code}",
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize Alibaba job: {e}")
            return None
