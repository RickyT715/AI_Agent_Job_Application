"""NetEase (163) Careers public API scraper.

Public POST endpoint, no authentication required:
    POST https://hr.163.com/api/hr163/position/queryPage
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://hr.163.com/api/hr163/position/queryPage"


class NetEaseScraper(BaseScraper):
    """Scraper for NetEase Careers public API."""

    SOURCE = "netease"

    def __init__(
        self,
        recruitment_type: str = "social",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)
        # workType: 0=all, 1=社招, 2=校招
        if recruitment_type == "campus":
            self._work_type = 2
        elif recruitment_type == "both":
            self._work_type = 0
        else:
            self._work_type = 1

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape jobs from NetEase Careers API.

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
                    "currentPage": page,
                    "pageSize": page_size,
                    "keyword": query,
                    "workType": self._work_type,
                }
                response = await client.post(
                    BASE_URL,
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
                logger.error(f"NetEase API HTTP error: {e}")
                result.errors.append(f"HTTP {e.response.status_code}")
            except httpx.HTTPError as e:
                logger.error(f"NetEase API request failed: {e}")
                result.errors.append(f"Request failed: {e}")

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert NetEase API response to JobPosting."""
        try:
            name = raw_data.get("name", "")
            if not name:
                return None

            post_id = str(raw_data.get("id", ""))
            raw_data.get("postTypeFullName", "")
            description = raw_data.get("description", "")
            requirement = raw_data.get("requirement", "")
            department = raw_data.get("firstDepName", "")
            locations = raw_data.get("workPlaceNameList", [])
            location = ", ".join(locations) if locations else None

            full_description = description
            if department:
                full_description = f"Department: {department}\n{description}"

            return JobPosting(
                external_id=post_id,
                source=self.SOURCE,
                title=name,
                company="NetEase",
                location=location,
                description=full_description,
                requirements=requirement or None,
                salary_currency="CNY",
                apply_url=f"https://hr.163.com/job-detail.html?id={post_id}",
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize NetEase job: {e}")
            return None
