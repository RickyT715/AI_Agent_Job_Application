"""Adzuna API scraper.

Public job board API covering multiple countries.
API docs: https://developer.adzuna.com/docs/search

Requires ADZUNA_APP_ID and ADZUNA_APP_KEY in settings.
"""

import logging

import httpx

from app.config import get_settings
from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs"


class AdzunaScraper(BaseScraper):
    """Scraper for the Adzuna Jobs API."""

    SOURCE = "adzuna"

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        country: str = "us",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)
        self._app_id = app_id
        self._app_key = app_key
        self._country = country

    def _get_credentials(self) -> tuple[str, str]:
        settings = get_settings()
        app_id = self._app_id or getattr(settings, "adzuna_app_id", "")
        app_key = self._app_key or getattr(settings, "adzuna_app_key", "")
        return app_id, app_key

    async def scrape(self, query: str = "Software Engineer", **kwargs) -> ScrapingResult:
        """Search for jobs via Adzuna API.

        Args:
            query: Job search query.
            **kwargs: Optional filters:
                - location: Location string.
                - num_pages: Number of pages to fetch (default: 1).
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()
        app_id, app_key = self._get_credentials()

        if not app_id or not app_key:
            result.errors.append("Adzuna credentials not configured")
            return result

        num_pages = kwargs.get("num_pages", 1)
        location = kwargs.get("location", "")

        for page in range(1, num_pages + 1):
            try:
                url = f"{BASE_URL}/{self._country}/search/{page}"
                params: dict[str, str | int] = {
                    "app_id": app_id,
                    "app_key": app_key,
                    "what": query,
                    "results_per_page": 20,
                    "content-type": "application/json",
                }
                if location:
                    params["where"] = location

                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                jobs_data = data.get("results", [])
                for raw in jobs_data:
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)

                result.total_found += len(jobs_data)

                if not jobs_data:
                    break

            except httpx.HTTPStatusError as e:
                logger.error(f"Adzuna API error (page {page}): {e}")
                result.errors.append(f"HTTP {e.response.status_code} on page {page}")
                break
            except httpx.HTTPError as e:
                logger.error(f"Adzuna request failed (page {page}): {e}")
                result.errors.append(f"Request failed on page {page}")
                break

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert Adzuna API response to JobPosting."""
        try:
            job_id = str(raw_data.get("id", ""))
            if not job_id:
                return None

            title = raw_data.get("title", "")
            if not title:
                return None

            company_data = raw_data.get("company", {}) or {}
            company = company_data.get("display_name", "Unknown")

            location_data = raw_data.get("location", {}) or {}
            display_name = location_data.get("display_name")
            area = location_data.get("area", [])
            location = display_name or (", ".join(area) if area else None)

            description = raw_data.get("description", "")
            apply_url = raw_data.get("redirect_url", "")

            # Salary
            salary_min = raw_data.get("salary_min")
            salary_max = raw_data.get("salary_max")
            if salary_min is not None:
                salary_min = int(salary_min)
            if salary_max is not None:
                salary_max = int(salary_max)

            contract_type = raw_data.get("contract_type")
            contract_time = raw_data.get("contract_time")
            employment_type = None
            if contract_time == "full_time":
                employment_type = "FULLTIME"
            elif contract_time == "part_time":
                employment_type = "PARTTIME"
            elif contract_type == "contract":
                employment_type = "CONTRACT"

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=title,
                company=company,
                location=location,
                description=description,
                salary_min=salary_min,
                salary_max=salary_max,
                employment_type=employment_type,
                apply_url=apply_url,
                raw_data=raw_data,
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to normalize Adzuna job: {e}")
            return None
