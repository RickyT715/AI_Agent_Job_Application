"""智联招聘 (Zhaopin) scraper via internal API.

Uses the front-end API endpoint with cookie-based session.
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://fe-api.zhaopin.com/c/i/sou"


class ZhaopinScraper(BaseScraper):
    """Scraper for 智联招聘 (Zhaopin)."""

    SOURCE = "zhaopin"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape jobs from Zhaopin.

        Args:
            query: Search keyword.
            **kwargs: Optional ``city_id``, ``num_pages``, ``page_size``.
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()

        num_pages = kwargs.get("num_pages", 1)
        page_size = kwargs.get("page_size", 30)
        city_id = kwargs.get("city_id", "")

        for page in range(1, num_pages + 1):
            try:
                params = {
                    "cityId": city_id,
                    "kw": query,
                    "pageSize": str(page_size),
                    "pageIndex": str(page),
                }
                response = await client.get(BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                results_data = data.get("data", {}).get("results", [])
                total = data.get("data", {}).get("numFound", len(results_data))
                result.total_found += total

                for raw in results_data:
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)

            except httpx.HTTPStatusError as e:
                logger.error(f"Zhaopin HTTP error: {e}")
                result.errors.append(f"HTTP {e.response.status_code}")
            except httpx.HTTPError as e:
                logger.error(f"Zhaopin request failed: {e}")
                result.errors.append(f"Request failed: {e}")

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert Zhaopin API response to JobPosting."""
        try:
            title = raw_data.get("jobName", "")
            if not title:
                return None

            job_id = str(raw_data.get("number", ""))
            company = raw_data.get("company", {}).get("name", "")
            city = raw_data.get("city", {}).get("display", "")
            salary = raw_data.get("salary", "")
            description = raw_data.get("jobSummary", "")
            job_type = raw_data.get("jobType", {}).get("display", "")
            education = raw_data.get("education", {}).get("display", "")
            experience = raw_data.get("workingExp", {}).get("display", "")
            apply_url = raw_data.get("positionURL", "")

            requirements = ""
            if experience:
                requirements += f"Experience: {experience}\n"
            if education:
                requirements += f"Education: {education}\n"
            if job_type:
                requirements += f"Type: {job_type}"

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=title,
                company=company,
                location=city or None,
                description=description or title,
                requirements=requirements or None,
                salary_currency="CNY",
                apply_url=apply_url or None,
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize Zhaopin job: {e}")
            return None
