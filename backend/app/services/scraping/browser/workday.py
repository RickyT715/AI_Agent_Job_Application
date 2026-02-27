"""Workday ATS scraper using XHR interception.

Workday sites use a SPA with XHR-based search. We intercept the JSON
responses from the search API rather than parsing the DOM.

This is best-effort — Workday layouts vary significantly between companies.
"""

import json
import logging
from typing import Any

from app.schemas.matching import JobPosting
from app.services.scraping.base import BaseScraper, ScrapingResult

logger = logging.getLogger(__name__)


class WorkdayScraper(BaseScraper):
    """Scraper for Workday job sites via XHR interception."""

    SOURCE = "workday"

    def __init__(self, base_urls: list[str] | None = None, **kwargs) -> None:
        super().__init__(client=None)
        self._base_urls = base_urls or []

    async def scrape(self, query: str = "", **kwargs) -> ScrapingResult:
        """Scrape Workday sites using Playwright XHR interception.

        Requires playwright to be installed. Falls back gracefully if unavailable.

        Args:
            query: Search query for jobs.
            **kwargs: Optional 'base_urls' override.
        """
        result = ScrapingResult(source=self.SOURCE)
        urls = kwargs.get("base_urls", self._base_urls)

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright not installed, skipping Workday scraping")
            result.errors.append("Playwright not installed")
            return result

        for base_url in urls:
            try:
                jobs = await self._scrape_url(base_url, query)
                for raw in jobs:
                    posting = self.normalize(raw)
                    if posting:
                        result.jobs.append(posting)
                result.total_found += len(jobs)
            except Exception as e:
                logger.error(f"Workday scrape failed for {base_url}: {e}")
                result.errors.append(f"Failed: {base_url} - {e}")

        return result

    async def _scrape_url(self, base_url: str, query: str) -> list[dict]:
        """Scrape a single Workday site by intercepting XHR search responses."""
        from playwright.async_api import async_playwright

        intercepted: list[dict] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            async def handle_response(response):
                url = response.url
                if "/jobs" in url and response.status == 200:
                    try:
                        content_type = response.headers.get("content-type", "")
                        if "json" in content_type:
                            body = await response.json()
                            jobs = self._extract_jobs_from_xhr(body)
                            intercepted.extend(jobs)
                    except Exception:
                        pass

            page.on("response", handle_response)

            try:
                await page.goto(base_url, wait_until="networkidle", timeout=30000)
                # Try to search if a search field exists
                if query:
                    search_input = page.locator('input[type="search"], input[aria-label*="search"]')
                    if await search_input.count() > 0:
                        await search_input.first.fill(query)
                        await page.keyboard.press("Enter")
                        await page.wait_for_timeout(3000)
            except Exception as e:
                logger.warning(f"Page interaction failed: {e}")
            finally:
                await browser.close()

        return intercepted

    def _extract_jobs_from_xhr(self, data: Any) -> list[dict]:
        """Extract job listings from Workday XHR response data."""
        jobs: list[dict] = []

        if isinstance(data, dict):
            # Common Workday patterns
            for key in ["jobPostings", "listItems", "body", "children"]:
                if key in data:
                    items = data[key]
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and ("title" in item or "text" in item):
                                jobs.append(item)
                    break

        return jobs

    def normalize(self, raw_data: dict) -> JobPosting | None:
        """Convert Workday XHR data to JobPosting."""
        try:
            title = raw_data.get("title") or raw_data.get("text", "")
            if not title:
                return None

            job_id = str(raw_data.get("id", raw_data.get("bulletFields", [{}])))
            company = raw_data.get("company", "Unknown")
            location = raw_data.get("locationsText") or raw_data.get("location", "")

            description = raw_data.get("description", "")
            if not description:
                # Some Workday sites put description in subtitles
                subtitles = raw_data.get("subtitles", [])
                if subtitles:
                    description = " ".join(
                        s.get("instances", [{}])[0].get("text", "")
                        for s in subtitles
                        if s.get("instances")
                    )

            apply_url = raw_data.get("externalPath", "")

            return JobPosting(
                external_id=job_id,
                source=self.SOURCE,
                title=title,
                company=company,
                location=location or None,
                description=description or title,
                apply_url=apply_url or None,
                raw_data=raw_data,
            )
        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to normalize Workday job: {e}")
            return None
