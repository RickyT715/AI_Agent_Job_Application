"""Tests for BOSS直聘 scraper."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.scraping.api.boss_zhipin import BossZhipinScraper

MOCK_RESPONSE = {
    "zpData": {
        "jobList": [
            {
                "encryptJobId": "boss001",
                "jobName": "Python后端开发",
                "brandName": "字节跳动",
                "cityName": "北京",
                "areaDistrict": "海淀区",
                "salaryDesc": "25-50K",
                "jobLabels": ["Python", "微服务", "高并发"],
                "skills": ["Python", "Django", "Redis"],
                "jobExperience": "3-5年",
                "jobDegree": "本科",
            },
            {
                "encryptJobId": "boss002",
                "jobName": "前端开发工程师",
                "brandName": "美团",
                "cityName": "上海",
                "areaDistrict": "",
                "salaryDesc": "20-40K",
                "jobLabels": ["React", "TypeScript"],
                "skills": ["React", "TypeScript", "Node.js"],
                "jobExperience": "1-3年",
                "jobDegree": "本科",
            },
        ]
    }
}


@pytest.fixture
def scraper():
    return BossZhipinScraper(cookie="test_session_cookie")


class TestBossZhipinScraper:

    async def test_scrape_returns_jobs(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=MOCK_RESPONSE)
        result = await scraper.scrape("Python")
        await scraper.close()
        assert len(result.jobs) == 2

    async def test_normalize_maps_fields(self, scraper):
        raw = MOCK_RESPONSE["zpData"]["jobList"][0]
        posting = scraper.normalize(raw)
        assert posting is not None
        assert posting.title == "Python后端开发"
        assert posting.company == "字节跳动"
        assert "北京" in posting.location
        assert posting.source == "boss_zhipin"

    async def test_no_cookie_returns_error(self, httpx_mock: HTTPXMock):
        scraper = BossZhipinScraper(cookie="")
        result = await scraper.scrape("test")
        assert len(result.errors) > 0
        assert "cookie" in result.errors[0].lower()

    async def test_http_error_captured(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=403)
        result = await scraper.scrape("test")
        await scraper.close()
        assert len(result.errors) > 0

    def test_normalize_missing_title(self, scraper):
        assert scraper.normalize({"encryptJobId": "x", "jobName": ""}) is None

    async def test_skills_in_description(self, scraper):
        raw = MOCK_RESPONSE["zpData"]["jobList"][0]
        posting = scraper.normalize(raw)
        assert "Python" in posting.description
        assert "Django" in posting.description

    async def test_requirements_has_experience(self, scraper):
        raw = MOCK_RESPONSE["zpData"]["jobList"][0]
        posting = scraper.normalize(raw)
        assert "3-5年" in posting.requirements

    async def test_empty_response(self, scraper, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json={"zpData": {"jobList": []}})
        result = await scraper.scrape("test")
        await scraper.close()
        assert len(result.jobs) == 0
