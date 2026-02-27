"""Tests for Jinja2 report templates."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent.parent.parent / "app" / "services" / "reports" / "templates"


@pytest.fixture
def jinja_env():
    """Create Jinja2 environment pointing to report templates."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )


class TestReportTemplate:
    """Tests for report.html Jinja2 template."""

    def test_template_renders_without_error(self, jinja_env, sample_report_data):
        template = jinja_env.get_template("report.html")
        html = template.render(
            job_title=sample_report_data["job_title"],
            company=sample_report_data["company"],
            overall_score="8.5",
            score_color="score-green",
            breakdown=sample_report_data["breakdown"],
            reasoning=sample_report_data["reasoning"],
            strengths=sample_report_data["strengths"],
            missing_skills=sample_report_data["missing_skills"],
            interview_talking_points=sample_report_data.get("interview_talking_points", []),
            salary_min=sample_report_data.get("salary_min"),
            salary_max=sample_report_data.get("salary_max"),
            salary_currency=sample_report_data.get("salary_currency"),
            cover_letter=None,
        )
        assert isinstance(html, str)
        assert len(html) > 100

    def test_template_renders_minimal_data(self, jinja_env, sample_report_data_minimal):
        template = jinja_env.get_template("report.html")
        html = template.render(
            job_title=sample_report_data_minimal["job_title"],
            company=sample_report_data_minimal["company"],
            overall_score="5.5",
            score_color="score-red",
            breakdown=sample_report_data_minimal["breakdown"],
            reasoning=sample_report_data_minimal["reasoning"],
            strengths=sample_report_data_minimal["strengths"],
            missing_skills=sample_report_data_minimal["missing_skills"],
            interview_talking_points=[],
            salary_min=None,
            salary_max=None,
            salary_currency=None,
            cover_letter=None,
        )
        assert "Data Analyst" in html
        assert "Analytics Co" in html

    def test_score_green_class_present(self, jinja_env, sample_report_data):
        template = jinja_env.get_template("report.html")
        html = template.render(
            job_title="Test",
            company="Test Co",
            overall_score="9.0",
            score_color="score-green",
            breakdown={"skills": 9},
            reasoning="Good",
            strengths=["Python"],
            missing_skills=[],
            interview_talking_points=[],
            salary_min=None,
            salary_max=None,
            salary_currency=None,
            cover_letter=None,
        )
        assert "score-green" in html

    def test_score_red_class_present(self, jinja_env):
        template = jinja_env.get_template("report.html")
        html = template.render(
            job_title="Test",
            company="Test Co",
            overall_score="3.0",
            score_color="score-red",
            breakdown={"skills": 3},
            reasoning="Poor match",
            strengths=[],
            missing_skills=["Everything"],
            interview_talking_points=[],
            salary_min=None,
            salary_max=None,
            salary_currency=None,
            cover_letter=None,
        )
        assert "score-red" in html

    def test_cover_letter_section_rendered(self, jinja_env):
        template = jinja_env.get_template("report.html")
        html = template.render(
            job_title="Test",
            company="Test Co",
            overall_score="7.0",
            score_color="score-yellow",
            breakdown={"skills": 7},
            reasoning="OK",
            strengths=["SQL"],
            missing_skills=[],
            interview_talking_points=[],
            salary_min=None,
            salary_max=None,
            salary_currency=None,
            cover_letter="Dear Hiring Manager, I am very excited to apply.",
        )
        assert "Dear Hiring Manager" in html

    def test_all_breakdown_categories_rendered(self, jinja_env, sample_report_data):
        template = jinja_env.get_template("report.html")
        html = template.render(
            job_title=sample_report_data["job_title"],
            company=sample_report_data["company"],
            overall_score="8.5",
            score_color="score-green",
            breakdown=sample_report_data["breakdown"],
            reasoning=sample_report_data["reasoning"],
            strengths=sample_report_data["strengths"],
            missing_skills=sample_report_data["missing_skills"],
            interview_talking_points=[],
            salary_min=None,
            salary_max=None,
            salary_currency=None,
            cover_letter=None,
        )
        for category in sample_report_data["breakdown"]:
            assert category in html.lower() or category.title() in html
