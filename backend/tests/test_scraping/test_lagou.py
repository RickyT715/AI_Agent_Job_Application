"""Tests for Lagou (拉勾网) scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.lagou import LagouScraper


MOCK_RESPONSE = {
    "content": {
        "positionResult": {
            "totalCount": 2,
            "result": [
                {
                    "positionId": "LG001",
                    "positionName": "Go后端开发",
                    "companyFullName": "滴滴出行科技有限公司",
                    "companyShortName": "滴滴",
                    "city": "北京",
                    "district": "海淀区",
                    "salary": "25k-50k",
                    "education": "本科",
                    "workYear": "3-5年",
                    "firstType": "开发/测试/运维类",
                    "positionAdvantage": "股票期权, 弹性工作",
                    "skillLables": ["Go", "Kubernetes", "微服务"],
                },
                {
                    "positionId": "LG002",
                    "positionName": "产品经理",
                    "companyFullName": "美团科技有限公司",
                    "city": "上海",
                    "district": "",
                    "salary": "20k-40k",
                    "education": "本科",
                    "workYear": "1-3年",
                    "positionAdvantage": "六险一金",
                    "skillLables": ["产品设计", "数据分析"],
                },
            ],
        }
    }
}


@pytest.fixture
def scraper():
    return LagouScraper()


class TestLagouScraper:

    async def test_scrape_returns_jobs(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_RESPONSE)
        result = await scraper.scrape("Go")
        await scraper.close()
        assert len(result.jobs) == 2

    async def test_normalize_maps_fields(self, scraper):
        raw = MOCK_RESPONSE["content"]["positionResult"]["result"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "Go后端开发"
        assert "滴滴" in posting.company
        assert "北京" in posting.location
        assert posting.source == "lagou"

    async def test_empty_response(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"content": {"positionResult": {"result": [], "totalCount": 0}}})
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 0

    async def test_http_error_captured(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=403)
        result = await scraper.scrape("test")
        await scraper.close()
        assert len(result.errors) > 0

    def test_normalize_missing_title(self, scraper):
        assert scraper.normalize({"positionId": "x", "positionName": ""}) is None

    async def test_skills_in_description(self, scraper):
        raw = MOCK_RESPONSE["content"]["positionResult"]["result"][0]
        posting = scraper.normalize(raw)
        assert "Go" in posting.description
