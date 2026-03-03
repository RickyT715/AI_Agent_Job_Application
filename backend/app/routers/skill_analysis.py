"""Skill market analysis API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.api import (
    BackfillSkillsResponse,
    SkillAnalysisRequest,
    SkillCoOccurrenceRequest,
    SkillCoOccurrenceResponse,
    SkillFrequencyResponse,
    SkillMarketReportResponse,
    TitleGroupResponse,
)
from app.services.analysis.skill_market import (
    build_skill_market_report,
    get_available_title_groups,
    get_skill_co_occurrences,
    get_skill_frequencies,
)
from app.services.matching.skill_persistence import backfill_all_job_skills

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/skill-analysis", tags=["skill-analysis"])


@router.get("/title-groups", response_model=list[TitleGroupResponse])
async def title_groups(
    min_jobs: int = Query(default=3, ge=1),
    db: AsyncSession = Depends(get_db_session),
):
    """Return available title groups with at least *min_jobs* postings."""
    groups = await get_available_title_groups(db, min_jobs=min_jobs)
    return [TitleGroupResponse(**g) for g in groups]


@router.post("/frequencies", response_model=list[SkillFrequencyResponse])
async def skill_frequencies(
    request: SkillAnalysisRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Return skill frequencies for jobs matching a title pattern."""
    frequencies, total_jobs = await get_skill_frequencies(
        db, request.title_pattern, top_n=request.top_n
    )
    if total_jobs == 0:
        raise HTTPException(status_code=404, detail="No jobs match the given title pattern")
    return [
        SkillFrequencyResponse(
            skill_name=f.skill_name,
            category=f.category,
            count=f.count,
            percentage=f.percentage,
        )
        for f in frequencies
    ]


@router.post("/co-occurrences", response_model=list[SkillCoOccurrenceResponse])
async def skill_co_occurrences(
    request: SkillCoOccurrenceRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Return co-occurring skills for a specific skill within a title pattern."""
    co_occs = await get_skill_co_occurrences(
        db, request.title_pattern, request.skill_name, top_n=request.top_n
    )
    return [
        SkillCoOccurrenceResponse(
            skill_a=c.skill_a,
            skill_b=c.skill_b,
            co_count=c.co_count,
            percentage=c.percentage,
        )
        for c in co_occs
    ]


@router.post("/report", response_model=SkillMarketReportResponse)
async def skill_report(
    request: SkillAnalysisRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Build a full skill market analysis report."""
    report = await build_skill_market_report(
        db, request.title_pattern, top_n=request.top_n
    )
    if report.total_jobs == 0:
        raise HTTPException(status_code=404, detail="No jobs match the given title pattern")
    return SkillMarketReportResponse(
        title_pattern=report.title_pattern,
        total_jobs=report.total_jobs,
        top_skills=[
            SkillFrequencyResponse(
                skill_name=s.skill_name, category=s.category,
                count=s.count, percentage=s.percentage,
            )
            for s in report.top_skills
        ],
        technical_skills=[
            SkillFrequencyResponse(
                skill_name=s.skill_name, category=s.category,
                count=s.count, percentage=s.percentage,
            )
            for s in report.technical_skills
        ],
        soft_skills=[
            SkillFrequencyResponse(
                skill_name=s.skill_name, category=s.category,
                count=s.count, percentage=s.percentage,
            )
            for s in report.soft_skills
        ],
        co_occurrences=[
            SkillCoOccurrenceResponse(
                skill_a=c.skill_a, skill_b=c.skill_b,
                co_count=c.co_count, percentage=c.percentage,
            )
            for c in report.co_occurrences
        ],
        category_breakdown=report.category_breakdown,
    )


@router.post("/report/pdf")
async def skill_report_pdf(
    request: SkillAnalysisRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Generate and return a PDF (or HTML fallback) skill market report."""
    report = await build_skill_market_report(
        db, request.title_pattern, top_n=request.top_n
    )
    if report.total_jobs == 0:
        raise HTTPException(status_code=404, detail="No jobs match the given title pattern")

    from app.services.reports.skill_report_generator import SkillReportGenerator

    generator = SkillReportGenerator()
    pdf_bytes = generator.generate_pdf(report)

    content_type = (
        "application/pdf" if pdf_bytes[:5] == b"%PDF-" else "text/html; charset=utf-8"
    )
    return Response(
        content=pdf_bytes,
        media_type=content_type,
        headers={"Content-Disposition": 'attachment; filename="skill-report.pdf"'},
    )


@router.post("/backfill", response_model=BackfillSkillsResponse)
async def backfill_skills(
    db: AsyncSession = Depends(get_db_session),
):
    """Backfill skills for all existing jobs that have no skills extracted."""
    result = await backfill_all_job_skills(db)
    return BackfillSkillsResponse(**result)
