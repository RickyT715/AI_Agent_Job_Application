"""Tests for RemoteOK API scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.remoteok import RemoteOKScraper


@pytest.fixture
def scraper():
    return RemoteOKScraper()


class TestRemoteOKScraper:
    """Tests for the RemoteOK scraper."""

    async def test_scrape_returns_matching_jobs(
        self, scraper: RemoteOKScraper, httpx_mock: HTTPXMock, remoteok_response
    ):
        httpx_mock.add_response(json=remoteok_response)
        result = await scraper.scrape("python")
        await scraper.close()
        assert len(result.jobs) >= 1
        assert result.source == "remoteok"

    async def test_scrape_filters_by_query(
        self, scraper: RemoteOKScraper, httpx_mock: HTTPXMock, remoteok_response
    ):
        httpx_mock.add_response(json=remoteok_response)
        result = await scraper.scrape("data engineer")
        await scraper.close()
        assert any("Data Engineer" in j.title for j in result.jobs)

    async def test_scrape_excludes_non_matching(
        self, scraper: RemoteOKScraper, httpx_mock: HTTPXMock, remoteok_response
    ):
        httpx_mock.add_response(json=remoteok_response)
        result = await scraper.scrape("kubernetes")
        await scraper.close()
        # No jobs mention kubernetes in title/desc/tags
        assert len(result.jobs) == 0

    def test_normalize_extracts_fields(self, scraper: RemoteOKScraper, remoteok_response):
        raw = remoteok_response[1]  # Skip metadata object at index 0
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "Senior Python Engineer"
        assert posting.company == "Acme Corp"
        assert posting.workplace_type == "remote"
        assert posting.source == "remoteok"

    def test_normalize_extracts_salary(self, scraper: RemoteOKScraper, remoteok_response):
        raw = remoteok_response[1]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.salary_min == 120000
        assert posting.salary_max == 180000

    def test_normalize_handles_null_salary(self, scraper: RemoteOKScraper, remoteok_response):
        raw = remoteok_response[2]  # DataFlow Inc - no salary
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.salary_min is None
        assert posting.salary_max is None

    def test_normalize_tags_as_requirements(self, scraper: RemoteOKScraper, remoteok_response):
        raw = remoteok_response[1]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert "python" in posting.requirements
        assert "fastapi" in posting.requirements

    async def test_handles_http_error(
        self, scraper: RemoteOKScraper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(status_code=429)
        result = await scraper.scrape("python")
        await scraper.close()
        assert len(result.errors) == 1
