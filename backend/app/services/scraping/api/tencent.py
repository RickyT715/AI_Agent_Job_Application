"""Tencent Careers public API scraper.

Fully public GET endpoint, no authentication required:
    https://careers.tencent.com/tencentcareer/api/post/Query
"""

import logging
import time

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://careers.tencent.com/tencentcareer/api/post/Query"


class TencentScraper(BaseScraper):
    """Scraper for Tencent Careers public API."""

    SOURCE = "tencent"

    def __init__(
        self,
        recruitment_type: str = "social",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)
        # isSchool=0 for 社招, isSchool=1 for 校招
        self._is_school = 1 if recruitment_type == "campus" else 0

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape jobs from Tencent Careers API.

        Args:
            query: Search keyword (e.g. "软件工程师").
            **kwargs: Optional overrides — ``num_pages``, ``page_size``.
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()

        num_pages = kwargs.get("num_pages", 1)
        page_size = kwargs.get("page_size", 20)

        for page in range(1, num_pages + 1):
            try:
                params = {
                    "timestamp": str(int(time.time() * 1000)),
                    "countryId": "",
                    "cityId": "",
                    "bgIds": "",
                    "productId": "",
                    "categoryId": "",
                    "isPart": "",
                    "isSchool": str(self._is_school),
                    "searchValue": query,
                    "pageIndex": str(page),
                    "pageSize": str(page_size),
                    "language": "zh-cn",
                    "area": "cn",
                }
                response = await client.get(BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                posts = data.get("Data", {}).get("Posts", [])
                result.total_found += data.get("Data", {}).get("Count", len(posts))

                for raw in posts:
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)

            except httpx.HTTPStatusError as e:
                logger.error(f"Tencent API HTTP error: {e}")
                result.errors.append(f"HTTP {e.response.status_code}")
            except httpx.HTTPError as e:
                logger.error(f"Tencent API request failed: {e}")
                result.errors.append(f"Request failed: {e}")

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert Tencent API response to JobPosting."""
        try:
            post_id = str(raw_data.get("PostId", ""))
            title = raw_data.get("RecruitPostName", "")
            if not title or not post_id:
                return None

            location = raw_data.get("LocationName", "")
            bg_name = raw_data.get("BGName", "")
            category = raw_data.get("CategoryName", "")
            description = raw_data.get("Responsibility", "")
            last_update = raw_data.get("LastUpdateTime", "")

            # Build requirements from category and BG
            requirements = ""
            if category:
                requirements = f"Category: {category}"
            if bg_name:
                requirements += f"\nBusiness Group: {bg_name}"

            return JobPosting(
                external_id=post_id,
                source=self.SOURCE,
                title=title,
                company="Tencent",
                location=location or None,
                description=description,
                requirements=requirements or None,
                salary_currency="CNY",
                apply_url=f"https://careers.tencent.com/jobdesc.html?postId={post_id}",
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize Tencent job: {e}")
            return None
