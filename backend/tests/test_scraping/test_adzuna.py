"""Tests for Adzuna API scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.adzuna import AdzunaScraper


@pytest.fixture
def scraper():
    return AdzunaScraper(app_id="test-id", app_key="test-key")


class TestAdzunaScraper:
    """Tests for the Adzuna API scraper."""

    async def test_scrape_returns_jobs(
        self, scraper: AdzunaScraper, httpx_mock: HTTPXMock, adzuna_response
    ):
        httpx_mock.add_response(json=adzuna_response)
        result = await scraper.scrape("Python Developer")
        await scraper.close()
        assert len(result.jobs) == 3
        assert result.source == "adzuna"

    async def test_credentials_sent_in_params(
        self, scraper: AdzunaScraper, httpx_mock: HTTPXMock, adzuna_response
    ):
        httpx_mock.add_response(json=adzuna_response)
        await scraper.scrape("Python Developer")
        await scraper.close()
        request = httpx_mock.get_requests()[0]
        assert "app_id=test-id" in str(request.url)
        assert "app_key=test-key" in str(request.url)

    async def test_missing_credentials_returns_error(self, httpx_mock: HTTPXMock):
        scraper = AdzunaScraper(app_id="", app_key="")
        result = await scraper.scrape("Python Developer")
        await scraper.close()
        assert len(result.errors) == 1
        assert "not configured" in result.errors[0]

    def test_normalize_extracts_salary(self, scraper: AdzunaScraper, adzuna_response):
        raw = adzuna_response["results"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.salary_min == 140000
        assert posting.salary_max == 190000

    def test_normalize_handles_null_salary(self, scraper: AdzunaScraper, adzuna_response):
        raw = adzuna_response["results"][1]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.salary_min is None
        assert posting.salary_max is None

    def test_normalize_extracts_location(self, scraper: AdzunaScraper, adzuna_response):
        raw = adzuna_response["results"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert "San Francisco" in posting.location

    def test_normalize_extracts_employment_type(self, scraper: AdzunaScraper, adzuna_response):
        raw = adzuna_response["results"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.employment_type == "FULLTIME"

    def test_normalize_contract_type(self, scraper: AdzunaScraper, adzuna_response):
        raw = adzuna_response["results"][2]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.employment_type == "PARTTIME"

    async def test_pagination(
        self, scraper: AdzunaScraper, httpx_mock: HTTPXMock, adzuna_response
    ):
        httpx_mock.add_response(json=adzuna_response)
        httpx_mock.add_response(json={"results": []})

        result = await scraper.scrape("Python Developer", num_pages=2)
        await scraper.close()
        assert len(result.jobs) == 3
        assert len(httpx_mock.get_requests()) == 2

    async def test_location_filter(
        self, scraper: AdzunaScraper, httpx_mock: HTTPXMock, adzuna_response
    ):
        httpx_mock.add_response(json=adzuna_response)
        await scraper.scrape("Python Developer", location="San Francisco")
        await scraper.close()
        request = httpx_mock.get_requests()[0]
        assert "where=San+Francisco" in str(request.url) or "where=San%20Francisco" in str(request.url)
