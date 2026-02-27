"""JSearch (RapidAPI) scraper.

Primary discovery channel — covers LinkedIn, Indeed, Glassdoor via Google for Jobs.
API docs: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch

Requires JSEARCH_API_KEY (X-RapidAPI-Key header).
"""

import logging

import httpx

from app.config import get_settings
from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)

BASE_URL = "https://jsearch.p.rapidapi.com/search"


class JSearchScraper(BaseScraper):
    """Scraper for JSearch API (RapidAPI)."""

    SOURCE = "jsearch"

    def __init__(
        self,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)
        self._api_key = api_key

    def _get_api_key(self) -> str:
        if self._api_key:
            return self._api_key
        return get_settings().jsearch_api_key.get_secret_value()

    def _get_headers(self) -> dict[str, str]:
        return {
            "X-RapidAPI-Key": self._get_api_key(),
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }

    async def scrape(self, query: str = "Software Engineer", **kwargs) -> ScrapingResult:
        """Search for jobs via JSearch API.

        Args:
            query: Job search query.
            **kwargs: Optional filters:
                - location: Location string (default: "").
                - remote_only: Whether to filter for remote jobs (default: False).
                - employment_type: "FULLTIME", "PARTTIME", "CONTRACTOR", etc.
                - num_pages: Number of pages to fetch (default: 1).
        """
        result = ScrapingResult(source=self.SOURCE)
        client = await self._get_client()
        headers = self._get_headers()

        location = kwargs.get("location", "")
        remote_only = kwargs.get("remote_only", False)
        employment_type = kwargs.get("employment_type")
        num_pages = kwargs.get("num_pages", 1)

        full_query = f"{query} in {location}" if location else query

        for page in range(1, num_pages + 1):
            try:
                params: dict[str, str | int | bool] = {
                    "query": full_query,
                    "page": page,
                    "num_pages": 1,
                }
                if remote_only:
                    params["remote_jobs_only"] = True
                if employment_type:
                    params["employment_types"] = employment_type

                response = await client.get(BASE_URL, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                jobs_data = data.get("data", [])
                for raw in jobs_data:
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)

                result.total_found += len(jobs_data)

                # Stop pagination if no more results
                if not jobs_data:
                    break

            except httpx.HTTPStatusError as e:
                logger.error(f"JSearch API error (page {page}): {e}")
                result.errors.append(f"HTTP {e.response.status_code} on page {page}")
                break
            except httpx.HTTPError as e:
                logger.error(f"JSearch request failed (page {page}): {e}")
                result.errors.append(f"Request failed on page {page}")
                break

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert JSearch API response to JobPosting."""
        try:
            job_id = raw_data.get("job_id", "")
            if not job_id:
                return None

            title = raw_data.get("job_title", "")
            if not title:
                return None

            company = raw_data.get("employer_name", "Unknown")
            city = raw_data.get("job_city", "")
            state = raw_data.get("job_state", "")
            country = raw_data.get("job_country", "")
            location_parts = [p for p in [city, state, country] if p]
            location = ", ".join(location_parts) if location_parts else None

            # Remote detection
            is_remote = raw_data.get("job_is_remote", False)
            workplace_type = "remote" if is_remote else None

            description = raw_data.get("job_description", "")

            # Salary
            salary_min = raw_data.get("job_min_salary")
            salary_max = raw_data.get("job_max_salary")
            salary_currency = raw_data.get("job_salary_currency")
            if salary_min is not None:
                salary_min = int(salary_min)
            if salary_max is not None:
                salary_max = int(salary_max)

            # Employment type
            employment_type = raw_data.get("job_employment_type")

            # Apply URL
            apply_url = raw_data.get("job_apply_link", "")

            # Experience
            required_experience = raw_data.get("job_required_experience", {}) or {}
            experience_level = required_experience.get("experience_level") if isinstance(
                required_experience, dict
            ) else None

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=title,
                company=company,
                location=location,
                workplace_type=workplace_type,
                description=description,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=salary_currency,
                employment_type=employment_type,
                experience_level=experience_level,
                apply_url=apply_url,
                raw_data=raw_data,
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to normalize JSearch job: {e}")
            return None
