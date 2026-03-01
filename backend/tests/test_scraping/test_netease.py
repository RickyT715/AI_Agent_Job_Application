"""Tests for NetEase Careers scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.netease import NetEaseScraper


@pytest.fixture
def scraper():
    return NetEaseScraper(recruitment_type="social")


class TestNetEaseScraper:
    """Tests for the NetEase Careers API scraper."""

    async def test_scrape_returns_jobs(
        self, scraper: NetEaseScraper, httpx_mock: HTTPXMock, netease_response
    ):
        httpx_mock.add_response(json=netease_response)
        result = await scraper.scrape("游戏开发")
        await scraper.close()
        assert len(result.jobs) == 2
        assert result.total_found == 2

    async def test_normalize_maps_fields(self, scraper: NetEaseScraper, netease_response):
        raw = netease_response["data"]["records"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "游戏服务端开发工程师"
        assert posting.company == "NetEase"
        assert "广州" in posting.location
        assert posting.source == "netease"
        assert posting.salary_currency == "CNY"

    async def test_normalize_location_joined(self, scraper: NetEaseScraper, netease_response):
        raw = netease_response["data"]["records"][0]
        posting = scraper.normalize(raw)
        assert "广州" in posting.location
        assert "杭州" in posting.location

    async def test_empty_response(self, scraper: NetEaseScraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"data": {"records": [], "total": 0}})
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 0

    async def test_social_mode(self):
        scraper = NetEaseScraper(recruitment_type="social")
        assert scraper._work_type == 1

    async def test_campus_mode(self):
        scraper = NetEaseScraper(recruitment_type="campus")
        assert scraper._work_type == 2

    async def test_both_mode(self):
        scraper = NetEaseScraper(recruitment_type="both")
        assert scraper._work_type == 0

    async def test_http_error_captured(self, scraper: NetEaseScraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=500)
        result = await scraper.scrape("test")
        await scraper.close()
        assert len(result.errors) > 0
