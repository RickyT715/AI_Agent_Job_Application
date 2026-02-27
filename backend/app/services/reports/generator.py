"""PDF/HTML report generator.

Renders Jinja2 templates with match data. PDF conversion via WeasyPrint
when available, otherwise produces HTML that can be converted externally.
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _score_color(score: float) -> str:
    """Return CSS class for score color."""
    if score >= 8:
        return "score-green"
    if score >= 6:
        return "score-yellow"
    return "score-red"


class ReportGenerator:
    """Generates match reports as HTML (and optionally PDF)."""

    def __init__(self, template_dir: Path | None = None) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir or TEMPLATE_DIR)),
            autoescape=True,
        )

    def render_html(
        self,
        job_title: str,
        company: str,
        overall_score: float,
        breakdown: dict[str, float],
        reasoning: str,
        strengths: list[str],
        missing_skills: list[str],
        interview_talking_points: list[str] | None = None,
        salary_min: int | None = None,
        salary_max: int | None = None,
        salary_currency: str | None = None,
        cover_letter: str | None = None,
    ) -> str:
        """Render the report as HTML.

        Returns:
            HTML string of the rendered report.
        """
        template = self._env.get_template("report.html")
        return template.render(
            job_title=job_title,
            company=company,
            overall_score=f"{overall_score:.1f}",
            score_color=_score_color(overall_score),
            breakdown=breakdown,
            reasoning=reasoning,
            strengths=strengths,
            missing_skills=missing_skills,
            interview_talking_points=interview_talking_points or [],
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            cover_letter=cover_letter,
        )

    def generate_pdf(self, **kwargs: object) -> bytes:
        """Generate a PDF report.

        Requires WeasyPrint. Falls back to HTML-to-bytes if unavailable.

        Returns:
            PDF bytes.
        """
        html = self.render_html(**kwargs)  # type: ignore[arg-type]

        try:
            from weasyprint import HTML as WeasyHTML  # noqa: N811
            pdf_bytes = WeasyHTML(string=html).write_pdf()
            logger.info(f"Generated PDF report ({len(pdf_bytes)} bytes)")
            return pdf_bytes
        except (ImportError, OSError):
            logger.warning("WeasyPrint not available, returning HTML bytes as fallback")
            return html.encode("utf-8")
