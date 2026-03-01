"""前程无忧 (51job) scraper.

Uses HTML scraping for job listings. Note: salary data may use font obfuscation
which requires fonttools to decode.
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

SEARCH_URL = "https://search.51job.com/list/{city},000000,0000,00,9,99,{keyword},2,{page}.html"
API_URL = "https://we.51job.com/api/job/search-pc"


class Job51Scraper(BaseScraper):
    """Scraper for 前程无忧 (51job)."""

    SOURCE = "job51"

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape jobs from 51job.

        Args:
            query: Search keyword.
            **kwargs: Optional ``city`` (code), ``num_pages``, ``page_size``.
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()

        num_pages = kwargs.get("num_pages", 1)
        page_size = kwargs.get("page_size", 20)

        for page in range(1, num_pages + 1):
            try:
                params = {
                    "keyword": query,
                    "pageNum": str(page),
                    "pageSize": str(page_size),
                    "searchType": "2",
                }
                response = await client.get(API_URL, params=params)
                response.raise_for_status()
                data = response.json()

                engine_list = data.get("resultbody", {}).get("job", {}).get("items", [])
                total = data.get("resultbody", {}).get("job", {}).get("total_count", 0)
                result.total_found += total

                for raw in engine_list:
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)

            except httpx.HTTPStatusError as e:
                logger.error(f"51job HTTP error: {e}")
                result.errors.append(f"HTTP {e.response.status_code}")
            except httpx.HTTPError as e:
                logger.error(f"51job request failed: {e}")
                result.errors.append(f"Request failed: {e}")

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert 51job API response to JobPosting."""
        try:
            title = raw_data.get("job_name", "")
            if not title:
                return None

            job_id = str(raw_data.get("jobid", ""))
            company = raw_data.get("company_name", "")
            location = raw_data.get("workarea_text", "")
            salary = raw_data.get("providesalary_text", "")
            job_type = raw_data.get("jobtype_text", "")
            education = raw_data.get("degree_text", "")
            experience = raw_data.get("workyear_text", "")
            description = raw_data.get("job_title_info", "") or title
            apply_url = raw_data.get("job_href", "")

            requirements = ""
            if experience:
                requirements += f"Experience: {experience}\n"
            if education:
                requirements += f"Education: {education}\n"
            if salary:
                requirements += f"Salary: {salary}"

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=title,
                company=company,
                location=location or None,
                description=description,
                requirements=requirements or None,
                salary_currency="CNY",
                employment_type=job_type or None,
                apply_url=apply_url or None,
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize 51job posting: {e}")
            return None
