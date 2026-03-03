"""Tests for the skill market report HTML/PDF generator."""

from app.services.analysis.skill_market import (
    SkillCoOccurrence,
    SkillFrequency,
    SkillMarketReport,
)
from app.services.reports.skill_report_generator import SkillReportGenerator


def _sample_report() -> SkillMarketReport:
    return SkillMarketReport(
        title_pattern="Software Engineer",
        total_jobs=50,
        top_skills=[
            SkillFrequency("python", "technical", 45, 90.0),
            SkillFrequency("docker", "technical", 30, 60.0),
            SkillFrequency("leadership", "soft_skill", 20, 40.0),
        ],
        technical_skills=[
            SkillFrequency("python", "technical", 45, 90.0),
            SkillFrequency("docker", "technical", 30, 60.0),
        ],
        soft_skills=[
            SkillFrequency("leadership", "soft_skill", 20, 40.0),
        ],
        co_occurrences=[
            SkillCoOccurrence("python", "docker", 28, 62.2),
            SkillCoOccurrence("python", "aws", 22, 48.9),
        ],
        category_breakdown={"technical": 15, "soft_skill": 5},
    )


class TestSkillReportGenerator:

    def test_render_html_contains_title(self):
        gen = SkillReportGenerator()
        html = gen.render_html(_sample_report())
        assert "Software Engineer" in html

    def test_render_html_contains_total_jobs(self):
        gen = SkillReportGenerator()
        html = gen.render_html(_sample_report())
        assert "50" in html

    def test_render_html_contains_skills(self):
        gen = SkillReportGenerator()
        html = gen.render_html(_sample_report())
        assert "python" in html
        assert "docker" in html
        assert "leadership" in html

    def test_render_html_contains_percentages(self):
        gen = SkillReportGenerator()
        html = gen.render_html(_sample_report())
        assert "90.0%" in html
        assert "60.0%" in html

    def test_render_html_contains_co_occurrences(self):
        gen = SkillReportGenerator()
        html = gen.render_html(_sample_report())
        assert "docker" in html
        assert "62.2%" in html

    def test_generate_pdf_returns_bytes(self):
        gen = SkillReportGenerator()
        result = gen.generate_pdf(_sample_report())
        assert isinstance(result, bytes)
        assert len(result) > 0
