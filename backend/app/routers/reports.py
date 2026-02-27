"""Report generation API endpoints."""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models.cover_letter import CoverLetter
from app.models.job import Job
from app.models.match import MatchResult
from app.models.user import User
from app.schemas.api import (
    CoverLetterRequest,
    CoverLetterResponse,
    ReportGenerateRequest,
    TaskStatusResponse,
)
from app.services.reports.cover_letter import CoverLetterGenerator
from app.services.reports.generator import ReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])

REPORTS_DIR = Path("data/reports")


@router.post("/generate", response_model=TaskStatusResponse)
async def generate_report(
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Generate a PDF/HTML report for a match result."""
    result = await db.execute(
        select(MatchResult)
        .options(selectinload(MatchResult.job))
        .where(MatchResult.id == request.match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    job: Job = match.job
    report_id = f"report-{match.id}"

    generator = ReportGenerator()
    html = generator.render_html(
        job_title=job.title,
        company=job.company,
        overall_score=match.overall_score,
        breakdown=match.score_breakdown,
        reasoning=match.reasoning,
        strengths=match.strengths,
        missing_skills=match.missing_skills,
        interview_talking_points=match.interview_talking_points or [],
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
    )

    # Try PDF generation, fall back to HTML
    try:
        content = generator.generate_pdf(
            job_title=job.title,
            company=job.company,
            overall_score=match.overall_score,
            breakdown=match.score_breakdown,
            reasoning=match.reasoning,
            strengths=match.strengths,
            missing_skills=match.missing_skills,
            interview_talking_points=match.interview_talking_points or [],
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
        )
        ext = ".pdf"
    except Exception:
        content = html.encode("utf-8")
        ext = ".html"

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{report_id}{ext}"
    report_path.write_bytes(content)

    return TaskStatusResponse(
        task_id=report_id,
        status="complete",
        result={"download_path": f"/api/reports/{report_id}/download"},
    )


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """Download a generated PDF/HTML report."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Try PDF first, then HTML
    pdf_path = REPORTS_DIR / f"{report_id}.pdf"
    html_path = REPORTS_DIR / f"{report_id}.html"

    if pdf_path.exists():
        return Response(
            content=pdf_path.read_bytes(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{report_id}.pdf"'},
        )
    elif html_path.exists():
        return Response(
            content=html_path.read_bytes(),
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{report_id}.html"'},
        )

    raise HTTPException(status_code=404, detail="Report not found")


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(
    request: CoverLetterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Generate a cover letter for a match result."""
    result = await db.execute(
        select(MatchResult)
        .options(selectinload(MatchResult.job), selectinload(MatchResult.user))
        .where(MatchResult.id == request.match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    job: Job = match.job
    user: User = match.user
    resume_text = user.resume_text or ""

    generator = CoverLetterGenerator()
    content = await generator.generate(
        job_title=job.title,
        company=job.company,
        job_description=job.description,
        resume_text=resume_text,
        strengths=match.strengths,
        missing_skills=match.missing_skills,
    )

    cover_letter = CoverLetter(
        user_id=match.user_id,
        match_id=match.id,
        content=content,
    )
    db.add(cover_letter)
    await db.flush()
    await db.refresh(cover_letter)

    return CoverLetterResponse.model_validate(cover_letter)
