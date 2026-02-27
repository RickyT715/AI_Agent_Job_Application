"""Tests for Greenhouse scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.greenhouse import GreenhouseScraper


@pytest.fixture
def scraper():
    return GreenhouseScraper(board_tokens=["testcompany"])


class TestGreenhouseScraper:
    """Tests for the Greenhouse API scraper."""

    async def test_search_returns_jobs(
        self, scraper: GreenhouseScraper, httpx_mock: HTTPXMock, greenhouse_response
    ):
        httpx_mock.add_response(
            url="https://boards-api.greenhouse.io/v1/boards/testcompany/jobs?content=true",
            json=greenhouse_response,
        )
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 2
        assert result.total_found == 2

    async def test_normalize_maps_fields(
        self, scraper: GreenhouseScraper, greenhouse_response
    ):
        raw = greenhouse_response["jobs"][0]
        raw["_board_token"] = "testcompany"
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "Senior Software Engineer"
        assert posting.location == "San Francisco, CA"
        assert posting.external_id == "4012345"
        assert posting.source == "greenhouse"
        assert "boards.greenhouse.io" in posting.apply_url

    async def test_rate_limit_retry(
        self, scraper: GreenhouseScraper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            url="https://boards-api.greenhouse.io/v1/boards/testcompany/jobs?content=true",
            status_code=429,
        )
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 0
        assert any("Rate limited" in e for e in result.errors)

    async def test_empty_board_returns_empty(
        self, scraper: GreenhouseScraper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            url="https://boards-api.greenhouse.io/v1/boards/testcompany/jobs?content=true",
            json={"jobs": []},
        )
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 0
        assert result.total_found == 0

    def test_normalize_strips_html(self, scraper: GreenhouseScraper, greenhouse_response):
        raw = greenhouse_response["jobs"][0]
        raw["_board_token"] = "testcompany"
        posting = scraper.normalize(raw)
        assert posting is not None
        # HTML tags should be stripped
        assert "<p>" not in posting.description
        assert "<strong>" not in posting.description
        assert "Senior Software Engineer" in posting.description
