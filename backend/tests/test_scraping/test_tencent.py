"""Tests for Tencent Careers scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.tencent import TencentScraper


@pytest.fixture
def scraper():
    return TencentScraper(recruitment_type="social")


@pytest.fixture
def campus_scraper():
    return TencentScraper(recruitment_type="campus")


class TestTencentScraper:
    """Tests for the Tencent Careers API scraper."""

    async def test_scrape_returns_jobs(
        self, scraper: TencentScraper, httpx_mock: HTTPXMock, tencent_response
    ):
        httpx_mock.add_response(json=tencent_response)
        result = await scraper.scrape("软件工程师")
        await scraper.close()
        assert len(result.jobs) == 2
        assert result.total_found == 2

    async def test_normalize_maps_fields(self, scraper: TencentScraper, tencent_response):
        raw = tencent_response["Data"]["Posts"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "高级后端开发工程师"
        assert posting.company == "Tencent"
        assert posting.location == "深圳"
        assert posting.external_id == "1001"
        assert posting.source == "tencent"
        assert posting.salary_currency == "CNY"

    async def test_normalize_second_job(self, scraper: TencentScraper, tencent_response):
        raw = tencent_response["Data"]["Posts"][1]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "机器学习算法工程师"
        assert posting.location == "北京"

    async def test_empty_response(self, scraper: TencentScraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"Data": {"Posts": [], "Count": 0}})
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 0

    async def test_social_mode(self, scraper: TencentScraper):
        assert scraper._is_school == 0

    async def test_campus_mode(self, campus_scraper: TencentScraper):
        assert campus_scraper._is_school == 1

    async def test_http_error_captured(
        self, scraper: TencentScraper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(status_code=500)
        result = await scraper.scrape("test")
        await scraper.close()
        assert len(result.jobs) == 0
        assert len(result.errors) > 0

    async def test_apply_url_format(self, scraper: TencentScraper, tencent_response):
        raw = tencent_response["Data"]["Posts"][0]
        posting = scraper.normalize(raw)
        assert "careers.tencent.com" in posting.apply_url
        assert "1001" in posting.apply_url

    def test_normalize_missing_title(self, scraper: TencentScraper):
        raw = {"PostId": "999", "RecruitPostName": "", "LocationName": "深圳"}
        assert scraper.normalize(raw) is None

    def test_normalize_missing_post_id(self, scraper: TencentScraper):
        raw = {"RecruitPostName": "Test", "LocationName": "深圳"}
        assert scraper.normalize(raw) is None
