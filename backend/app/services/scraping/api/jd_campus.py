"""JD.com Campus Recruitment API scraper.

Public GET endpoint (campus/intern positions only):
    GET https://campus.jd.com/api/wx/position/index
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://campus.jd.com/api/wx/position/index"


class JDCampusScraper(BaseScraper):
    """Scraper for JD.com Campus Recruitment API."""

    SOURCE = "jd_campus"

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape campus jobs from JD.com.

        Args:
            query: Search keyword (optional).
            **kwargs: Optional overrides.
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()

        try:
            params = {"type": "present"}
            if query:
                params["keyword"] = query

            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            positions = data.get("data", [])
            if isinstance(positions, dict):
                positions = positions.get("list", [])
            result.total_found = len(positions)

            for raw in positions:
                posting = self.normalize(raw)
                if posting:
                    result.jobs.append(posting)

        except httpx.HTTPStatusError as e:
            logger.error(f"JD Campus API HTTP error: {e}")
            result.errors.append(f"HTTP {e.response.status_code}")
        except httpx.HTTPError as e:
            logger.error(f"JD Campus API request failed: {e}")
            result.errors.append(f"Request failed: {e}")

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert JD Campus API response to JobPosting."""
        try:
            name = raw_data.get("name", "") or raw_data.get("title", "")
            if not name:
                return None

            job_id = str(raw_data.get("id", ""))
            location = raw_data.get("workCity", "") or raw_data.get("city", "")
            department = raw_data.get("deptName", "") or raw_data.get("department", "")
            description = raw_data.get("description", "") or raw_data.get("content", "")
            requirement = raw_data.get("requirement", "")

            full_description = description
            if department:
                full_description = f"Department: {department}\n{description}"

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=name,
                company="JD.com",
                location=location or None,
                description=full_description,
                requirements=requirement or None,
                salary_currency="CNY",
                employment_type="INTERNSHIP",
                apply_url=f"https://campus.jd.com/#/job/{job_id}",
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize JD Campus job: {e}")
            return None
