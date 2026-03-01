"""Tests for MokaHR scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.mokahrjob import MokaHRScraper


@pytest.fixture
def scraper():
    return MokaHRScraper(org_ids=["didi-test"])


class TestMokaHRScraper:
    """Tests for the MokaHR API scraper."""

    async def test_scrape_returns_jobs(
        self, scraper: MokaHRScraper, httpx_mock: HTTPXMock, mokahr_response
    ):
        httpx_mock.add_response(json=mokahr_response)
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 2
        assert result.total_found == 2

    async def test_normalize_maps_fields(self, scraper: MokaHRScraper, mokahr_response):
        raw = mokahr_response["data"][0]
        raw["_org_id"] = "didi-test"
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "全栈开发工程师"
        assert posting.company == "DiDi"
        assert posting.location == "上海"
        assert posting.source == "mokahr"

    async def test_multi_org_scrape(self, httpx_mock: HTTPXMock, mokahr_response):
        scraper = MokaHRScraper(org_ids=["org-a", "org-b"])
        httpx_mock.add_response(json=mokahr_response)
        httpx_mock.add_response(json=mokahr_response)
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 4  # 2 per org

    async def test_empty_org_ids(self, httpx_mock: HTTPXMock):
        scraper = MokaHRScraper(org_ids=[])
        result = await scraper.scrape()
        assert len(result.jobs) == 0

    async def test_social_mode(self):
        scraper = MokaHRScraper(org_ids=["test"], recruitment_type="social")
        assert scraper._mode == "social"

    async def test_campus_mode(self):
        scraper = MokaHRScraper(org_ids=["test"], recruitment_type="campus")
        assert scraper._mode == "campus"

    async def test_http_error_captured(self, scraper: MokaHRScraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=404)
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.errors) > 0

    def test_normalize_missing_title(self, scraper: MokaHRScraper):
        raw = {"id": "999", "title": "", "name": "", "_org_id": "test"}
        assert scraper.normalize(raw) is None
