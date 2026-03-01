"""BOSS直聘 scraper via cookie-based session.

Requires a session cookie obtained from browser DevTools after logging in.
The scraper uses internal API endpoints that return JSON.
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"


class BossZhipinScraper(BaseScraper):
    """Scraper for BOSS直聘 using cookie-based authentication."""

    SOURCE = "boss_zhipin"

    def __init__(
        self,
        cookie: str = "",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)
        self._cookie = cookie

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape jobs from BOSS直聘.

        Args:
            query: Search keyword.
            **kwargs: Optional ``city`` (city code), ``num_pages``.
        """
        result = ScrapingResult(source=self.SOURCE)

        if not self._cookie:
            result.errors.append("No session cookie configured for BOSS直聘")
            return result

        client = await self._get_client()
        num_pages = kwargs.get("num_pages", 1)
        city = kwargs.get("city", "101010100")  # Default: Beijing

        headers = {
            "Cookie": self._cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.zhipin.com/",
        }

        for page in range(1, num_pages + 1):
            try:
                params = {
                    "query": query,
                    "city": city,
                    "page": str(page),
                    "pageSize": "30",
                }
                response = await client.get(BASE_URL, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                job_list = data.get("zpData", {}).get("jobList", [])
                result.total_found += len(job_list)

                for raw in job_list:
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)

            except httpx.HTTPStatusError as e:
                logger.error(f"BOSS直聘 HTTP error: {e}")
                result.errors.append(f"HTTP {e.response.status_code}")
            except httpx.HTTPError as e:
                logger.error(f"BOSS直聘 request failed: {e}")
                result.errors.append(f"Request failed: {e}")

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert BOSS直聘 API response to JobPosting."""
        try:
            title = raw_data.get("jobName", "")
            if not title:
                return None

            job_id = str(raw_data.get("encryptJobId", raw_data.get("jobId", "")))
            company = raw_data.get("brandName", "")
            location = raw_data.get("cityName", "")
            area = raw_data.get("areaDistrict", "")
            if area:
                location = f"{location} {area}"

            salary = raw_data.get("salaryDesc", "")
            description = raw_data.get("jobLabels", [])
            desc_text = ", ".join(description) if isinstance(description, list) else str(description)

            skills = raw_data.get("skills", [])
            if skills:
                desc_text += f"\nSkills: {', '.join(skills)}"

            experience = raw_data.get("jobExperience", "")
            education = raw_data.get("jobDegree", "")
            requirements = ""
            if experience:
                requirements += f"Experience: {experience}\n"
            if education:
                requirements += f"Education: {education}"

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=title,
                company=company,
                location=location or None,
                description=desc_text or title,
                requirements=requirements or None,
                salary_currency="CNY",
                apply_url=f"https://www.zhipin.com/job_detail/{job_id}.html",
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize BOSS直聘 job: {e}")
            return None
