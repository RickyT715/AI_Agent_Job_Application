"""Tests for PDF/HTML report generator."""

import pytest

from app.services.reports.generator import ReportGenerator, _score_color


class TestScoreColor:
    """Tests for _score_color helper."""

    def test_high_score_returns_green(self):
        assert _score_color(8.0) == "score-green"
        assert _score_color(9.5) == "score-green"
        assert _score_color(10.0) == "score-green"

    def test_mid_score_returns_yellow(self):
        assert _score_color(6.0) == "score-yellow"
        assert _score_color(7.0) == "score-yellow"
        assert _score_color(7.9) == "score-yellow"

    def test_low_score_returns_red(self):
        assert _score_color(5.9) == "score-red"
        assert _score_color(3.0) == "score-red"
        assert _score_color(0.0) == "score-red"


class TestReportGenerator:
    """Tests for ReportGenerator."""

    def test_render_html_returns_string(self, sample_report_data):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_html_contains_company_name(self, sample_report_data):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data)
        assert "TechCorp Inc." in html

    def test_html_contains_job_title(self, sample_report_data):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data)
        assert "Senior Software Engineer" in html

    def test_html_contains_overall_score(self, sample_report_data):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data)
        assert "8.5" in html

    def test_html_contains_strengths(self, sample_report_data):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data)
        assert "Python expertise" in html
        assert "FastAPI experience" in html

    def test_html_contains_missing_skills(self, sample_report_data):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data)
        assert "Kubernetes" in html
        assert "Go programming" in html

    def test_html_contains_reasoning(self, sample_report_data):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data)
        assert "Strong match due to extensive Python" in html

    def test_html_contains_talking_points(self, sample_report_data):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data)
        assert "Discuss ML pipeline architecture" in html

    def test_html_contains_salary(self, sample_report_data):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data)
        assert "120000" in html or "120,000" in html
        assert "180000" in html or "180,000" in html
        assert "USD" in html

    def test_handles_missing_salary(self, sample_report_data_minimal):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data_minimal)
        assert isinstance(html, str)
        assert "Data Analyst" in html

    def test_handles_missing_talking_points(self, sample_report_data_minimal):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data_minimal)
        assert isinstance(html, str)
        assert "Analytics Co" in html

    def test_html_contains_breakdown_categories(self, sample_report_data):
        gen = ReportGenerator()
        html = gen.render_html(**sample_report_data)
        assert "skills" in html.lower()
        assert "experience" in html.lower()

    def test_generate_pdf_without_weasyprint_returns_bytes(self, sample_report_data):
        """When WeasyPrint is not installed, falls back to HTML bytes."""
        gen = ReportGenerator()
        result = gen.generate_pdf(**sample_report_data)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_render_html_with_cover_letter(self, sample_report_data):
        gen = ReportGenerator()
        data = {**sample_report_data, "cover_letter": "Dear Hiring Manager, I am excited..."}
        html = gen.render_html(**data)
        assert "Dear Hiring Manager" in html
