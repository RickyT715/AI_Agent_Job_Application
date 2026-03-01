"""Tests for WeWorkRemotely RSS scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.weworkremotely import CATEGORY_FEEDS, WeWorkRemotelyScraper


@pytest.fixture
def scraper():
    return WeWorkRemotelyScraper(categories=["programming"])


class TestWeWorkRemotelyScraper:
    """Tests for the WeWorkRemotely scraper."""

    async def test_scrape_returns_matching_jobs(
        self, scraper: WeWorkRemotelyScraper, httpx_mock: HTTPXMock, weworkremotely_feed
    ):
        httpx_mock.add_response(text=weworkremotely_feed)
        result = await scraper.scrape("software engineer")
        await scraper.close()
        assert len(result.jobs) >= 1
        assert result.source == "weworkremotely"

    async def test_scrape_filters_by_query(
        self, scraper: WeWorkRemotelyScraper, httpx_mock: HTTPXMock, weworkremotely_feed
    ):
        httpx_mock.add_response(text=weworkremotely_feed)
        result = await scraper.scrape("data engineer")
        await scraper.close()
        assert any("Data Engineer" in j.title for j in result.jobs)

    async def test_scrape_excludes_non_matching(
        self, scraper: WeWorkRemotelyScraper, httpx_mock: HTTPXMock, weworkremotely_feed
    ):
        httpx_mock.add_response(text=weworkremotely_feed)
        result = await scraper.scrape("rust developer")
        await scraper.close()
        assert len(result.jobs) == 0

    def test_normalize_splits_company_from_title(self, scraper: WeWorkRemotelyScraper):
        raw = {
            "title": "Acme Corp: Senior Software Engineer",
            "link": "https://example.com/job",
            "guid": "https://example.com/job",
            "description": "Build software",
        }
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.company == "Acme Corp"
        assert posting.title == "Senior Software Engineer"

    def test_normalize_all_jobs_are_remote(self, scraper: WeWorkRemotelyScraper):
        raw = {
            "title": "Test Job",
            "link": "https://example.com/job",
            "guid": "https://example.com/job",
            "description": "Test",
        }
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.workplace_type == "remote"
        assert posting.location == "Remote"

    async def test_handles_http_error(
        self, scraper: WeWorkRemotelyScraper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(status_code=500)
        result = await scraper.scrape("python")
        await scraper.close()
        assert len(result.errors) == 1

    def test_normalize_returns_none_for_empty_title(self, scraper: WeWorkRemotelyScraper):
        raw = {"title": "", "link": "url", "guid": "id", "description": "test"}
        assert scraper.normalize(raw) is None
