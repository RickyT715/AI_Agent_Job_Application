"""Tests for pre-filter Chinese language support."""

from app.config import UserConfig
from app.schemas.matching import JobPosting
from app.services.matching.pre_filter import (
    JobPreFilter,
    _detect_seniority,
    _location_matches,
    _normalize_employment_type,
)


def _make_job(
    title: str = "Software Engineer",
    location: str | None = None,
    employment_type: str | None = None,
) -> JobPosting:
    return JobPosting(
        external_id="test-001",
        source="test",
        title=title,
        company="TestCo",
        description="A test job posting.",
        location=location,
        employment_type=employment_type,
    )


class TestChineseSeniority:
    """Tests for Chinese seniority detection."""

    def test_detects_intern_zh(self):
        assert _detect_seniority("软件开发实习生") == 0

    def test_detects_junior_zh(self):
        assert _detect_seniority("初级Java开发工程师") == 1

    def test_detects_senior_zh(self):
        assert _detect_seniority("高级后端开发工程师") == 3

    def test_detects_senior_zishen(self):
        assert _detect_seniority("资深前端工程师") == 3

    def test_detects_expert_zh(self):
        assert _detect_seniority("技术专家") == 3

    def test_detects_manager_zh(self):
        assert _detect_seniority("研发经理") == 6

    def test_detects_director_zh(self):
        assert _detect_seniority("技术总监") == 6

    def test_detects_lead_zh(self):
        assert _detect_seniority("开发主管") == 4


class TestChineseRemoteKeywords:
    """Tests for Chinese remote location matching."""

    def test_remote_zh(self):
        assert _location_matches("远程", ["United States"]) is True

    def test_work_from_home_zh(self):
        assert _location_matches("居家办公", ["Remote"]) is True

    def test_online_work_zh(self):
        assert _location_matches("线上办公", ["Any"]) is True

    def test_remote_office_zh(self):
        assert _location_matches("远程办公", ["Germany"]) is True


class TestChineseEmploymentType:
    """Tests for Chinese employment type aliases."""

    def test_fulltime_zh(self):
        assert _normalize_employment_type("全职") == "FULLTIME"

    def test_parttime_zh(self):
        assert _normalize_employment_type("兼职") == "PARTTIME"

    def test_contract_zh(self):
        assert _normalize_employment_type("合同") == "CONTRACT"

    def test_internship_zh(self):
        assert _normalize_employment_type("实习") == "INTERNSHIP"

    def test_temporary_zh(self):
        assert _normalize_employment_type("临时") == "TEMPORARY"


class TestChinesePreFilter:
    """Integration tests for Chinese pre-filtering."""

    def test_filters_senior_roles_for_entry_zh(self):
        config = UserConfig(experience_level="entry")
        pf = JobPreFilter(config)
        jobs = [
            _make_job("初级Java开发"),           # junior → passes
            _make_job("高级后端工程师"),           # senior → drops
            _make_job("技术总监"),                # director → drops
            _make_job("Python开发工程师"),         # no seniority → passes
        ]
        result = pf.filter(jobs)
        titles = [j.title for j in result]
        assert "初级Java开发" in titles
        assert "Python开发工程师" in titles
        assert "高级后端工程师" not in titles

    def test_chinese_employment_filter(self):
        config = UserConfig(employment_types=["FULLTIME"])
        pf = JobPreFilter(config)
        jobs = [
            _make_job(employment_type="全职"),
            _make_job(employment_type="兼职"),
            _make_job(employment_type=None),
        ]
        result = pf.filter(jobs)
        assert len(result) == 2  # 全职 + None
