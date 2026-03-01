"""Tests for 51job (前程无忧) scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.job51 import Job51Scraper


MOCK_RESPONSE = {
    "resultbody": {
        "job": {
            "total_count": 2,
            "items": [
                {
                    "jobid": "J51001",
                    "job_name": "Python开发工程师",
                    "company_name": "华为技术有限公司",
                    "workarea_text": "深圳-龙岗区",
                    "providesalary_text": "20-30万/年",
                    "jobtype_text": "全职",
                    "degree_text": "本科",
                    "workyear_text": "3-5年经验",
                    "job_title_info": "负责公司Python后端系统开发",
                    "job_href": "https://jobs.51job.com/J51001.html",
                },
                {
                    "jobid": "J51002",
                    "job_name": "测试开发工程师",
                    "company_name": "中兴通讯",
                    "workarea_text": "南京",
                    "providesalary_text": "15-25万/年",
                    "jobtype_text": "全职",
                    "degree_text": "本科",
                    "workyear_text": "1-3年经验",
                    "job_title_info": "负责自动化测试框架开发",
                    "job_href": "https://jobs.51job.com/J51002.html",
                },
            ],
        }
    }
}


@pytest.fixture
def scraper():
    return Job51Scraper()


class TestJob51Scraper:

    async def test_scrape_returns_jobs(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_RESPONSE)
        result = await scraper.scrape("Python")
        await scraper.close()
        assert len(result.jobs) == 2

    async def test_normalize_maps_fields(self, scraper):
        raw = MOCK_RESPONSE["resultbody"]["job"]["items"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "Python开发工程师"
        assert posting.company == "华为技术有限公司"
        assert "深圳" in posting.location
        assert posting.source == "job51"

    async def test_empty_response(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"resultbody": {"job": {"items": [], "total_count": 0}}})
        result = await scraper.scrape()
        await scraper.close()
        assert len(result.jobs) == 0

    async def test_http_error_captured(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=500)
        result = await scraper.scrape("test")
        await scraper.close()
        assert len(result.errors) > 0

    def test_normalize_missing_title(self, scraper):
        assert scraper.normalize({"jobid": "x", "job_name": ""}) is None

    async def test_requirements_extracted(self, scraper):
        raw = MOCK_RESPONSE["resultbody"]["job"]["items"][0]
        posting = scraper.normalize(raw)
        assert "3-5年" in posting.requirements

    async def test_apply_url_preserved(self, scraper):
        raw = MOCK_RESPONSE["resultbody"]["job"]["items"][0]
        posting = scraper.normalize(raw)
        assert posting.apply_url == "https://jobs.51job.com/J51001.html"

    async def test_salary_currency_cny(self, scraper):
        raw = MOCK_RESPONSE["resultbody"]["job"]["items"][0]
        posting = scraper.normalize(raw)
        assert posting.salary_currency == "CNY"
