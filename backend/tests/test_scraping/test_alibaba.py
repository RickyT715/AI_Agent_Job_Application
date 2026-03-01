"""Tests for Alibaba Careers scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.alibaba import AlibabaScraper


@pytest.fixture
def scraper():
    return AlibabaScraper(recruitment_type="social")


MOCK_RESPONSE = {
    "data": {
        "total": 2,
        "records": [
            {
                "code": "ALI001",
                "name": "高级Java开发工程师",
                "workLocations": ["杭州", "北京"],
                "category": "技术",
                "deptName": "蚂蚁金服",
                "description": "负责支付宝核心交易系统开发",
                "requirement": "5年以上Java开发经验",
            },
            {
                "code": "ALI002",
                "name": "数据工程师",
                "workLocations": ["杭州"],
                "category": "数据",
                "deptName": "阿里云",
                "description": "负责大数据平台建设",
                "requirement": "精通Spark和Flink",
            },
        ],
    }
}


class TestAlibabaScraper:
    """Tests for the Alibaba Careers API scraper."""

    async def test_scrape_returns_jobs(
        self, scraper: AlibabaScraper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(json=MOCK_RESPONSE)
        result = await scraper.scrape("Java")
        await scraper.close()
        assert len(result.jobs) == 2

    async def test_normalize_maps_fields(self, scraper: AlibabaScraper):
        raw = MOCK_RESPONSE["data"]["records"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "高级Java开发工程师"
        assert posting.company == "Alibaba Group"
        assert "杭州" in posting.location
        assert posting.source == "alibaba"

    async def test_normalize_locations_joined(self, scraper: AlibabaScraper):
        raw = MOCK_RESPONSE["data"]["records"][0]
        posting = scraper.normalize(raw)
        assert "杭州" in posting.location
        assert "北京" in posting.location

    async def test_empty_response(self, scraper: AlibabaScraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"data": {"records": [], "total": 0}})
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 0

    async def test_http_error_captured(self, scraper: AlibabaScraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=500)
        result = await scraper.scrape("test")
        await scraper.close()
        assert len(result.errors) > 0

    def test_normalize_missing_name(self, scraper: AlibabaScraper):
        assert scraper.normalize({"code": "x", "name": ""}) is None

    def test_apply_url_format(self, scraper: AlibabaScraper):
        raw = MOCK_RESPONSE["data"]["records"][0]
        posting = scraper.normalize(raw)
        assert "talent.alibaba.com" in posting.apply_url
        assert "ALI001" in posting.apply_url
