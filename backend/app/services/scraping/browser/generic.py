"""Generic web scraper using JSON-LD extraction.

Falls back to this scraper when a page doesn't have a known API.
Extracts Schema.org JobPosting structured data from HTML pages.
"""

import json
import logging
import re

import httpx

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)


def extract_jsonld_jobs(html: str) -> list[dict]:
    """Extract Schema.org JobPosting objects from JSON-LD script tags.

    Args:
        html: Raw HTML page content.

    Returns:
        List of raw job posting dicts extracted from JSON-LD.
    """
    jobs: list[dict] = []
    # Find all JSON-LD script blocks
    pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

    for match in matches:
        try:
            data = json.loads(match.strip())
            _collect_job_postings(data, jobs)
        except json.JSONDecodeError:
            continue

    return jobs


def _collect_job_postings(data, jobs: list[dict]) -> None:
    """Recursively collect JobPosting objects from JSON-LD data."""
    if isinstance(data, dict):
        schema_type = data.get("@type", "")
        if schema_type == "JobPosting" or (
            isinstance(schema_type, list) and "JobPosting" in schema_type
        ):
            jobs.append(data)
        # Check @graph arrays
        if "@graph" in data:
            for item in data["@graph"]:
                _collect_job_postings(item, jobs)
    elif isinstance(data, list):
        for item in data:
            _collect_job_postings(item, jobs)


class GenericScraper(BaseScraper):
    """Generic scraper that extracts JSON-LD JobPosting from web pages."""

    SOURCE = "generic"

    def __init__(
        self,
        urls: list[str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(client)
        self._urls = urls or []

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape JSON-LD job postings from provided URLs.

        Args:
            query: Unused — this scraper targets specific URLs.
            **kwargs: Optional 'urls' to override configured list.
        """
        result = ScrapingResult(source=self.SOURCE)
        urls = kwargs.get("urls", self._urls)
        client = await self._get_client()

        for url in urls:
            try:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                raw_jobs = extract_jsonld_jobs(response.text)

                for raw in raw_jobs:
                    raw["_source_url"] = url
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)
                result.total_found += len(raw_jobs)

            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch {url}: {e}")
                result.errors.append(f"Failed: {url}")

        return result

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert Schema.org JobPosting JSON-LD to JobPosting."""
        try:
            title = raw_data.get("title", "")
            if not title:
                return None

            # Company from hiringOrganization
            org = raw_data.get("hiringOrganization", {})
            if isinstance(org, dict):
                company = org.get("name", "Unknown")
            else:
                company = str(org) if org else "Unknown"

            # Location
            location = _extract_location(raw_data)

            # Description
            description = raw_data.get("description", "")
            if "<" in description:
                description = _strip_html(description)

            # Salary
            salary_min, salary_max, salary_currency = _extract_salary(raw_data)

            # Employment type
            employment_type = raw_data.get("employmentType")
            if isinstance(employment_type, list):
                employment_type = employment_type[0] if employment_type else None

            # Apply URL
            source_url = raw_data.get("_source_url", "")
            apply_url = raw_data.get("url") or source_url

            # Generate ID from URL or title
            identifier = raw_data.get("identifier")
            if isinstance(identifier, dict):
                job_id = identifier.get("value", "")
            else:
                job_id = str(hash(f"{company}:{title}:{location}"))

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=title,
                company=company,
                location=location,
                description=description,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=salary_currency,
                employment_type=employment_type,
                apply_url=apply_url,
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize JSON-LD job: {e}")
            return None


def _extract_location(data: dict) -> str | None:
    """Extract location string from Schema.org JobPosting."""
    job_location = data.get("jobLocation")
    if not job_location:
        return None

    if isinstance(job_location, list):
        job_location = job_location[0] if job_location else {}

    if isinstance(job_location, dict):
        address = job_location.get("address", {})
        if isinstance(address, dict):
            parts = [
                address.get("addressLocality", ""),
                address.get("addressRegion", ""),
                address.get("addressCountry", ""),
            ]
            return ", ".join(p for p in parts if p) or None
        elif isinstance(address, str):
            return address

    return None


def _extract_salary(data: dict) -> tuple[int | None, int | None, str | None]:
    """Extract salary range from Schema.org baseSalary."""
    base_salary = data.get("baseSalary")
    if not base_salary or not isinstance(base_salary, dict):
        return None, None, None

    currency = base_salary.get("currency")
    value = base_salary.get("value", {})

    if isinstance(value, dict):
        min_val = value.get("minValue")
        max_val = value.get("maxValue")
        return (
            int(min_val) if min_val else None,
            int(max_val) if max_val else None,
            currency,
        )

    return None, None, currency


def _strip_html(html: str) -> str:
    """Strip HTML tags from text."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text
