"""Tests for ByteDance (字节跳动) Careers scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.bytedance import ByteDanceScraper

MOCK_RESPONSE = {
    "data": {
        "total": 2,
        "posts": [
            {
                "id": "BD001",
                "title": "后端研发工程师",
                "description": "负责抖音推荐系统后端开发",
                "requirement": "精通Go或Python，3年以上后端经验",
                "city_info": {"name": "北京"},
                "job_category": {"name": "研发"},
                "recruit_type": {"name": "社招"},
            },
            {
                "id": "BD002",
                "title": "iOS开发工程师",
                "description": "负责TikTok iOS客户端开发",
                "requirement": "精通Swift/Objective-C",
                "city_info": {"name": "上海"},
                "job_category": {"name": "研发"},
                "recruit_type": {"name": "社招"},
            },
        ],
    }
}


@pytest.fixture
def scraper():
    return ByteDanceScraper(recruitment_type="social")


class TestByteDanceScraper:

    async def test_scrape_returns_jobs(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_RESPONSE)
        result = await scraper.scrape("后端")
        await scraper.close()
        assert len(result.jobs) == 2

    async def test_normalize_maps_fields(self, scraper):
        raw = MOCK_RESPONSE["data"]["posts"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "后端研发工程师"
        assert posting.company == "ByteDance"
        assert posting.location == "北京"
        assert posting.source == "bytedance"

    async def test_social_mode(self):
        s = ByteDanceScraper(recruitment_type="social")
        assert s._portal_type == 2

    async def test_campus_mode(self):
        s = ByteDanceScraper(recruitment_type="campus")
        assert s._portal_type == 1

    async def test_empty_response(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"data": {"posts": [], "total": 0}})
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 0

    async def test_http_error_captured(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=500)
        result = await scraper.scrape("test")
        await scraper.close()
        assert len(result.errors) > 0

    def test_normalize_missing_title(self, scraper):
        assert scraper.normalize({"id": "x", "title": ""}) is None

    async def test_apply_url_format(self, scraper):
        raw = MOCK_RESPONSE["data"]["posts"][0]
        posting = scraper.normalize(raw)
        assert "jobs.bytedance.com" in posting.apply_url
        assert "BD001" in posting.apply_url
