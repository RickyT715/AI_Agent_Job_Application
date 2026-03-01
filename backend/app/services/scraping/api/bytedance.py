"""ByteDance (字节跳动) Careers API scraper.

Uses the public job search endpoint:
    POST https://jobs.bytedance.com/api/v1/search/job/posts
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

API_URL = "https://jobs.bytedance.com/api/v1/search/job/posts"


class ByteDanceScraper(BaseScraper):
    """Scraper for ByteDance Careers."""

    SOURCE = "bytedance"

    def __init__(
        self,
        recruitment_type: str = "social",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)
        # portal_type: 1=校招, 2=社招
        self._portal_type = 1 if recruitment_type == "campus" else 2

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape jobs from ByteDance Careers.

        Args:
            query: Search keyword.
            **kwargs: Optional ``num_pages``, ``page_size``.
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()

        num_pages = kwargs.get("num_pages", 1)
        page_size = kwargs.get("page_size", 20)

        for page in range(1, num_pages + 1):
            try:
                payload = {
                    "keyword": query,
                    "limit": page_size,
                    "offset": (page - 1) * page_size,
                    "portal_type": self._portal_type,
                }
                response = await client.post(
                    API_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

                posts = data.get("data", {}).get("posts", [])
                total = data.get("data", {}).get("total", len(posts))
                result.total_found += total

                for raw in posts:
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)

            except httpx.HTTPStatusError as e:
                logger.error(f"ByteDance HTTP error: {e}")
                result.errors.append(f"HTTP {e.response.status_code}")
            except httpx.HTTPError as e:
                logger.error(f"ByteDance request failed: {e}")
                result.errors.append(f"Request failed: {e}")

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert ByteDance API response to JobPosting."""
        try:
            title = raw_data.get("title", "")
            if not title:
                return None

            job_id = str(raw_data.get("id", ""))
            description = raw_data.get("description", "")
            requirement = raw_data.get("requirement", "")
            city = raw_data.get("city_info", {}).get("name", "")
            if isinstance(raw_data.get("city_info"), str):
                city = raw_data["city_info"]

            category = raw_data.get("job_category", {}).get("name", "")
            raw_data.get("recruit_type", {}).get("name", "")

            full_description = description
            if category:
                full_description = f"Category: {category}\n{description}"

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=title,
                company="ByteDance",
                location=city or None,
                description=full_description,
                requirements=requirement or None,
                salary_currency="CNY",
                apply_url=f"https://jobs.bytedance.com/experienced/position/{job_id}",
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize ByteDance job: {e}")
            return None
