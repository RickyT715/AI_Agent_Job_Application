"""Tests for Lever scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.lever import LeverScraper


@pytest.fixture
def scraper():
    return LeverScraper(companies=["testcompany"])


class TestLeverScraper:
    """Tests for the Lever API scraper."""

    async def test_search_returns_postings(
        self, scraper: LeverScraper, httpx_mock: HTTPXMock, lever_response
    ):
        httpx_mock.add_response(
            url="https://api.lever.co/v0/postings/testcompany?mode=json",
            json=lever_response,
        )
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 2
        assert result.total_found == 2

    def test_normalize_extracts_location(self, scraper: LeverScraper, lever_response):
        raw = lever_response[0]
        raw["_company_slug"] = "testcompany"
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.location == "New York, NY"

    def test_normalize_extracts_apply_url(self, scraper: LeverScraper, lever_response):
        raw = lever_response[0]
        raw["_company_slug"] = "testcompany"
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.apply_url == "https://jobs.lever.co/testcompany/abc12345/apply"

    def test_normalize_extracts_employment_type(self, scraper: LeverScraper, lever_response):
        raw = lever_response[0]
        raw["_company_slug"] = "testcompany"
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.employment_type == "Full-time"

    async def test_empty_company_returns_empty(
        self, scraper: LeverScraper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            url="https://api.lever.co/v0/postings/testcompany?mode=json",
            json=[],
        )
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 0
