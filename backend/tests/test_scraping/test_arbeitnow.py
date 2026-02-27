"""Tests for Arbeitnow API scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.arbeitnow import ArbeitnowScraper


@pytest.fixture
def scraper():
    return ArbeitnowScraper()


class TestArbeitnowScraper:
    """Tests for the Arbeitnow API scraper."""

    async def test_scrape_returns_matching_jobs(
        self, scraper: ArbeitnowScraper, httpx_mock: HTTPXMock, arbeitnow_response
    ):
        httpx_mock.add_response(json=arbeitnow_response)
        result = await scraper.scrape("software engineer")
        await scraper.close()
        # Only "Senior Software Engineer" matches the query in title
        assert len(result.jobs) >= 1
        assert result.source == "arbeitnow"

    async def test_scrape_filters_by_query(
        self, scraper: ArbeitnowScraper, httpx_mock: HTTPXMock, arbeitnow_response
    ):
        httpx_mock.add_response(json=arbeitnow_response)
        result = await scraper.scrape("data engineer")
        await scraper.close()
        assert any("Data Engineer" in j.title for j in result.jobs)

    async def test_scrape_filters_by_tags(
        self, scraper: ArbeitnowScraper, httpx_mock: HTTPXMock, arbeitnow_response
    ):
        httpx_mock.add_response(json=arbeitnow_response)
        result = await scraper.scrape("python")
        await scraper.close()
        # Python tag exists in first and third jobs
        assert len(result.jobs) >= 2

    def test_normalize_extracts_fields(self, scraper: ArbeitnowScraper, arbeitnow_response):
        raw = arbeitnow_response["data"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "Senior Software Engineer"
        assert posting.company == "Acme Corp"
        assert posting.workplace_type == "remote"

    def test_normalize_non_remote(self, scraper: ArbeitnowScraper, arbeitnow_response):
        raw = arbeitnow_response["data"][1]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.workplace_type is None
        assert posting.location == "Berlin, Germany"

    def test_normalize_extracts_tags_as_requirements(
        self, scraper: ArbeitnowScraper, arbeitnow_response
    ):
        raw = arbeitnow_response["data"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert "python" in posting.requirements
        assert "typescript" in posting.requirements

    def test_normalize_uses_slug_as_id(self, scraper: ArbeitnowScraper, arbeitnow_response):
        raw = arbeitnow_response["data"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.external_id == "senior-software-engineer-acme-corp-12345"

    async def test_pagination_stops_when_no_next(
        self, scraper: ArbeitnowScraper, httpx_mock: HTTPXMock, arbeitnow_response
    ):
        # Remove next link to signal end
        page2 = {"data": [], "links": {}, "meta": {}}
        httpx_mock.add_response(json=arbeitnow_response)
        httpx_mock.add_response(json=page2)

        result = await scraper.scrape("python", num_pages=3)
        await scraper.close()
        # Only 2 pages fetched (page 2 has no data and no next link)
        assert len(httpx_mock.get_requests()) == 2

    async def test_handles_http_error(
        self, scraper: ArbeitnowScraper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(status_code=500)
        result = await scraper.scrape("python")
        await scraper.close()
        assert len(result.errors) == 1
