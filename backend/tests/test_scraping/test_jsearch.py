"""Tests for JSearch (RapidAPI) scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.jsearch import JSearchScraper


@pytest.fixture
def scraper():
    return JSearchScraper(api_key="test-api-key")


class TestJSearchScraper:
    """Tests for the JSearch API scraper."""

    async def test_search_with_filters(
        self, scraper: JSearchScraper, httpx_mock: HTTPXMock, jsearch_response
    ):
        httpx_mock.add_response(json=jsearch_response)
        result = await scraper.scrape(
            "Python Developer",
            location="Austin",
            remote_only=False,
        )
        await scraper.close()
        assert len(result.jobs) == 3

    async def test_api_key_sent_in_headers(
        self, scraper: JSearchScraper, httpx_mock: HTTPXMock, jsearch_response
    ):
        httpx_mock.add_response(json=jsearch_response)
        await scraper.scrape("Python Developer")
        await scraper.close()
        request = httpx_mock.get_requests()[0]
        assert request.headers["X-RapidAPI-Key"] == "test-api-key"
        assert request.headers["X-RapidAPI-Host"] == "jsearch.p.rapidapi.com"

    def test_normalize_handles_missing_salary(self, scraper: JSearchScraper, jsearch_response):
        # Second job has null salary fields
        raw = jsearch_response["data"][1]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.salary_min is None
        assert posting.salary_max is None

    def test_normalize_extracts_salary(self, scraper: JSearchScraper, jsearch_response):
        raw = jsearch_response["data"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.salary_min == 120000
        assert posting.salary_max == 160000
        assert posting.salary_currency == "USD"

    def test_normalize_extracts_remote(self, scraper: JSearchScraper, jsearch_response):
        # Second job is remote
        raw = jsearch_response["data"][1]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.workplace_type == "remote"

    def test_normalize_extracts_location(self, scraper: JSearchScraper, jsearch_response):
        raw = jsearch_response["data"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert "Austin" in posting.location
        assert "TX" in posting.location

    async def test_pagination_fetches_all_pages(
        self, scraper: JSearchScraper, httpx_mock: HTTPXMock, jsearch_response
    ):
        # Page 1 has data, page 2 is empty (signals end)
        httpx_mock.add_response(json=jsearch_response)
        httpx_mock.add_response(json={"status": "OK", "data": []})

        result = await scraper.scrape("Python Developer", num_pages=2)
        await scraper.close()
        assert len(result.jobs) == 3  # All from page 1
        assert len(httpx_mock.get_requests()) == 2

    def test_normalize_handles_null_experience(self, scraper: JSearchScraper, jsearch_response):
        raw = jsearch_response["data"][2]  # Has null required_experience
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.experience_level is None
