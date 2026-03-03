"""Skill market analysis report generator (HTML / PDF)."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.services.analysis.skill_market import SkillMarketReport

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"


class SkillReportGenerator:
    """Renders a skill market analysis report as HTML (and optionally PDF)."""

    def __init__(self, template_dir: Path | None = None) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir or TEMPLATE_DIR)),
            autoescape=True,
        )

    def render_html(self, report: SkillMarketReport) -> str:
        """Render the skill report as HTML."""
        template = self._env.get_template("skill_report.html")
        return template.render(
            title_pattern=report.title_pattern,
            total_jobs=report.total_jobs,
            top_skills=report.top_skills,
            technical_skills=report.technical_skills,
            soft_skills=report.soft_skills,
            co_occurrences=report.co_occurrences,
            category_breakdown=report.category_breakdown,
        )

    def generate_pdf(self, report: SkillMarketReport) -> bytes:
        """Generate a PDF report. Falls back to HTML bytes if WeasyPrint unavailable."""
        html = self.render_html(report)

        try:
            from weasyprint import HTML as WeasyHTML  # noqa: N811
            pdf_bytes = WeasyHTML(string=html).write_pdf()
            logger.info("Generated skill report PDF (%d bytes)", len(pdf_bytes))
            return pdf_bytes
        except (ImportError, OSError):
            logger.warning("WeasyPrint not available, returning HTML bytes as fallback")
            return html.encode("utf-8")
