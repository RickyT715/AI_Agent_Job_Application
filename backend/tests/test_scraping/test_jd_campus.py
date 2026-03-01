"""Tests for JD.com Campus Recruitment scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.jd_campus import JDCampusScraper


@pytest.fixture
def scraper():
    return JDCampusScraper()


MOCK_RESPONSE = {
    "data": [
        {
            "id": "JD001",
            "name": "后端开发实习生",
            "workCity": "北京",
            "deptName": "京东物流",
            "description": "参与京东物流系统后端开发",
            "requirement": "计算机相关专业在读",
        },
        {
            "id": "JD002",
            "title": "算法实习生",
            "city": "上海",
            "department": "京东AI研究院",
            "content": "参与推荐算法研发",
            "requirement": "机器学习方向在读研究生",
        },
    ]
}


class TestJDCampusScraper:
    """Tests for the JD Campus API scraper."""

    async def test_scrape_returns_jobs(
        self, scraper: JDCampusScraper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(json=MOCK_RESPONSE)
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 2

    async def test_normalize_maps_primary_fields(self, scraper: JDCampusScraper):
        raw = MOCK_RESPONSE["data"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "后端开发实习生"
        assert posting.company == "JD.com"
        assert posting.location == "北京"
        assert posting.source == "jd_campus"
        assert posting.employment_type == "INTERNSHIP"

    async def test_normalize_fallback_fields(self, scraper: JDCampusScraper):
        raw = MOCK_RESPONSE["data"][1]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "算法实习生"
        assert posting.location == "上海"

    async def test_empty_response(self, scraper: JDCampusScraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"data": []})
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 0

    async def test_http_error_captured(self, scraper: JDCampusScraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=500)
        result = await scraper.scrape("test")
        await scraper.close()
        assert len(result.errors) > 0

    def test_normalize_missing_name(self, scraper: JDCampusScraper):
        assert scraper.normalize({"id": "x"}) is None
