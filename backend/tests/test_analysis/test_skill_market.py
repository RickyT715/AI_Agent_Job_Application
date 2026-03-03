"""Tests for skill market analysis queries."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analysis.skill_market import (
    build_skill_market_report,
    get_available_title_groups,
    get_skill_co_occurrences,
    get_skill_frequencies,
)


class TestGetAvailableTitleGroups:

    async def test_returns_groups_above_min(self, seeded_db: AsyncSession):
        groups = await get_available_title_groups(seeded_db, min_jobs=3)
        titles = [g["title"] for g in groups]
        assert "software engineer" in titles
        # Data Scientist only has 2, so it shouldn't appear at min_jobs=3
        assert "data scientist" not in titles

    async def test_returns_all_with_low_threshold(self, seeded_db: AsyncSession):
        groups = await get_available_title_groups(seeded_db, min_jobs=1)
        assert len(groups) >= 2


class TestGetSkillFrequencies:

    async def test_returns_frequencies(self, seeded_db: AsyncSession):
        freqs, total = await get_skill_frequencies(seeded_db, "Software Engineer")
        assert total == 5
        skill_map = {f.skill_name: f for f in freqs}
        assert "python" in skill_map
        assert skill_map["python"].count == 5
        assert skill_map["python"].percentage == 100.0

    async def test_category_filter(self, seeded_db: AsyncSession):
        freqs, total = await get_skill_frequencies(
            seeded_db, "Software Engineer", category="soft_skill"
        )
        assert total == 5
        assert all(f.category == "soft_skill" for f in freqs)

    async def test_no_match_returns_empty(self, seeded_db: AsyncSession):
        freqs, total = await get_skill_frequencies(seeded_db, "nonexistent title")
        assert total == 0
        assert freqs == []


class TestGetSkillCoOccurrences:

    async def test_co_occurrences_for_python(self, seeded_db: AsyncSession):
        co_occs = await get_skill_co_occurrences(
            seeded_db, "Software Engineer", "python"
        )
        skill_b_names = {c.skill_b for c in co_occs}
        assert "docker" in skill_b_names
        # python should not co-occur with itself
        assert "python" not in skill_b_names

    async def test_no_results_for_missing_skill(self, seeded_db: AsyncSession):
        co_occs = await get_skill_co_occurrences(
            seeded_db, "Software Engineer", "nonexistent"
        )
        assert co_occs == []


class TestBuildSkillMarketReport:

    async def test_full_report(self, seeded_db: AsyncSession):
        report = await build_skill_market_report(seeded_db, "Software Engineer")
        assert report.total_jobs == 5
        assert report.title_pattern == "Software Engineer"
        assert len(report.top_skills) > 0
        assert len(report.technical_skills) > 0
        assert len(report.soft_skills) > 0
        assert "technical" in report.category_breakdown

    async def test_empty_report(self, seeded_db: AsyncSession):
        report = await build_skill_market_report(seeded_db, "nonexistent")
        assert report.total_jobs == 0
        assert report.top_skills == []
