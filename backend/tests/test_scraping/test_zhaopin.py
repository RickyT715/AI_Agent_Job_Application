"""Tests for Zhaopin (智联招聘) scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.zhaopin import ZhaopinScraper

MOCK_RESPONSE = {
    "data": {
        "numFound": 2,
        "results": [
            {
                "number": "ZP001",
                "jobName": "高级Java开发",
                "company": {"name": "阿里巴巴"},
                "city": {"display": "杭州"},
                "salary": "30-50K",
                "jobSummary": "负责核心交易系统开发",
                "jobType": {"display": "全职"},
                "education": {"display": "本科"},
                "workingExp": {"display": "5-10年"},
                "positionURL": "https://zhaopin.com/job/ZP001",
            },
            {
                "number": "ZP002",
                "jobName": "运维工程师",
                "company": {"name": "腾讯"},
                "city": {"display": "深圳"},
                "salary": "20-35K",
                "jobSummary": "负责云平台运维",
                "jobType": {"display": "全职"},
                "education": {"display": "本科"},
                "workingExp": {"display": "3-5年"},
                "positionURL": "https://zhaopin.com/job/ZP002",
            },
        ],
    }
}


@pytest.fixture
def scraper():
    return ZhaopinScraper()


class TestZhaopinScraper:

    async def test_scrape_returns_jobs(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_RESPONSE)
        result = await scraper.scrape("Java")
        await scraper.close()
        assert len(result.jobs) == 2

    async def test_normalize_maps_fields(self, scraper):
        raw = MOCK_RESPONSE["data"]["results"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "高级Java开发"
        assert posting.company == "阿里巴巴"
        assert posting.location == "杭州"
        assert posting.source == "zhaopin"

    async def test_empty_response(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"data": {"results": [], "numFound": 0}})
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 0

    async def test_http_error_captured(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=500)
        result = await scraper.scrape("test")
        await scraper.close()
        assert len(result.errors) > 0

    def test_normalize_missing_title(self, scraper):
        assert scraper.normalize({"number": "x", "jobName": ""}) is None

    async def test_requirements_extracted(self, scraper):
        raw = MOCK_RESPONSE["data"]["results"][0]
        posting = scraper.normalize(raw)
        assert "5-10年" in posting.requirements

    async def test_apply_url_preserved(self, scraper):
        raw = MOCK_RESPONSE["data"]["results"][0]
        posting = scraper.normalize(raw)
        assert posting.apply_url == "https://zhaopin.com/job/ZP001"

    async def test_second_job_normalized(self, scraper):
        raw = MOCK_RESPONSE["data"]["results"][1]
        posting = scraper.normalize(raw)
        assert posting.title == "运维工程师"
        assert posting.company == "腾讯"
