"""拉勾网 (Lagou) scraper.

Uses the AJAX endpoint. Lagou has aggressive anti-scraping measures;
this scraper requires proper session management.
"""

import logging

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

API_URL = "https://www.lagou.com/jobs/positionAjax.json"


class LagouScraper(BaseScraper):
    """Scraper for 拉勾网 (Lagou)."""

    SOURCE = "lagou"

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape jobs from Lagou.

        Args:
            query: Search keyword.
            **kwargs: Optional ``city``, ``num_pages``.
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()

        num_pages = kwargs.get("num_pages", 1)
        city = kwargs.get("city", "全国")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": f"https://www.lagou.com/jobs/list_{query}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        for page in range(1, num_pages + 1):
            try:
                data = {
                    "first": "true" if page == 1 else "false",
                    "pn": str(page),
                    "kd": query,
                }
                params = {"city": city, "needAddtionalResult": "false"}
                response = await client.post(
                    API_URL, data=data, params=params, headers=headers
                )
                response.raise_for_status()
                resp_data = response.json()

                content = resp_data.get("content", {}).get("positionResult", {})
                positions = content.get("result", [])
                total = content.get("totalCount", len(positions))
                result.total_found += total

                for raw in positions:
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)

            except httpx.HTTPStatusError as e:
                logger.error(f"Lagou HTTP error: {e}")
                result.errors.append(f"HTTP {e.response.status_code}")
            except httpx.HTTPError as e:
                logger.error(f"Lagou request failed: {e}")
                result.errors.append(f"Request failed: {e}")

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert Lagou API response to JobPosting."""
        try:
            title = raw_data.get("positionName", "")
            if not title:
                return None

            job_id = str(raw_data.get("positionId", ""))
            company = raw_data.get("companyFullName", "") or raw_data.get("companyShortName", "")
            city = raw_data.get("city", "")
            district = raw_data.get("district", "")
            location = f"{city} {district}".strip() if city else None

            salary = raw_data.get("salary", "")
            education = raw_data.get("education", "")
            experience = raw_data.get("workYear", "")
            job_type = raw_data.get("firstType", "")
            description = raw_data.get("positionAdvantage", "")
            skills = raw_data.get("skillLables", []) or raw_data.get("skillLabels", [])

            if skills:
                description += f"\nSkills: {', '.join(skills)}"

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
                location=location,
                description=description or title,
                requirements=requirements or None,
                salary_currency="CNY",
                apply_url=f"https://www.lagou.com/jobs/{job_id}.html",
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize Lagou job: {e}")
            return None
