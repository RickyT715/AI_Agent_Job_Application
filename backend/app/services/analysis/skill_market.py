"""Skill market analysis queries.

Aggregates extracted skills across job postings to reveal market-wide
demand patterns, co-occurrences, and category breakdowns.
"""

import logging
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import escape_like
from app.models.job import Job
from app.models.job_skill import JobSkill

logger = logging.getLogger(__name__)


@dataclass
class SkillFrequency:
    skill_name: str
    category: str
    count: int
    percentage: float


@dataclass
class SkillCoOccurrence:
    skill_a: str
    skill_b: str
    co_count: int
    percentage: float


@dataclass
class SkillMarketReport:
    title_pattern: str
    total_jobs: int
    top_skills: list[SkillFrequency] = field(default_factory=list)
    technical_skills: list[SkillFrequency] = field(default_factory=list)
    soft_skills: list[SkillFrequency] = field(default_factory=list)
    co_occurrences: list[SkillCoOccurrence] = field(default_factory=list)
    category_breakdown: dict[str, int] = field(default_factory=dict)


async def get_available_title_groups(
    db: AsyncSession, *, min_jobs: int = 3
) -> list[dict[str, object]]:
    """Return distinct job titles with at least *min_jobs* postings.

    Groups by ``lower(title)`` and returns ``[{"title": str, "job_count": int}]``.
    """
    stmt = (
        select(
            func.lower(Job.title).label("title"),
            func.count(Job.id).label("job_count"),
        )
        .group_by(func.lower(Job.title))
        .having(func.count(Job.id) >= min_jobs)
        .order_by(func.count(Job.id).desc())
    )
    result = await db.execute(stmt)
    return [{"title": row.title, "job_count": row.job_count} for row in result.all()]


async def get_skill_frequencies(
    db: AsyncSession,
    title_pattern: str,
    *,
    category: str | None = None,
    top_n: int = 30,
) -> tuple[list[SkillFrequency], int]:
    """Count how many jobs (matching *title_pattern*) contain each skill.

    Returns ``(frequencies, total_jobs_matched)``.
    """
    # Subquery: job IDs matching the title pattern
    safe_pattern = escape_like(title_pattern.lower())
    job_ids_sq = (
        select(Job.id)
        .where(func.lower(Job.title).like(f"%{safe_pattern}%"))
        .subquery()
    )

    # Total jobs matching pattern
    total_result = await db.execute(
        select(func.count()).select_from(job_ids_sq)
    )
    total_jobs = total_result.scalar() or 0

    if total_jobs == 0:
        return [], 0

    # Skill frequencies
    stmt = (
        select(
            JobSkill.skill_name,
            JobSkill.category,
            func.count(func.distinct(JobSkill.job_id)).label("cnt"),
        )
        .where(JobSkill.job_id.in_(select(job_ids_sq.c.id)))
    )
    if category:
        stmt = stmt.where(JobSkill.category == category)

    stmt = (
        stmt
        .group_by(JobSkill.skill_name, JobSkill.category)
        .order_by(func.count(func.distinct(JobSkill.job_id)).desc())
        .limit(top_n)
    )

    result = await db.execute(stmt)
    frequencies = [
        SkillFrequency(
            skill_name=row.skill_name,
            category=row.category,
            count=row.cnt,
            percentage=round(row.cnt / total_jobs * 100, 1),
        )
        for row in result.all()
    ]
    return frequencies, total_jobs


async def get_skill_co_occurrences(
    db: AsyncSession,
    title_pattern: str,
    skill_name: str,
    *,
    top_n: int = 10,
) -> list[SkillCoOccurrence]:
    """For jobs matching *title_pattern* that require *skill_name*,
    find which other skills co-occur most frequently.
    """
    # Job IDs matching title pattern AND containing the anchor skill
    safe_pattern = escape_like(title_pattern.lower())
    anchor_jobs_sq = (
        select(JobSkill.job_id)
        .join(Job, Job.id == JobSkill.job_id)
        .where(
            func.lower(Job.title).like(f"%{safe_pattern}%"),
            JobSkill.skill_name == skill_name.lower(),
        )
        .subquery()
    )

    anchor_count_result = await db.execute(
        select(func.count()).select_from(anchor_jobs_sq)
    )
    anchor_count = anchor_count_result.scalar() or 0

    if anchor_count == 0:
        return []

    # Co-occurring skills (exclude the anchor skill itself)
    stmt = (
        select(
            JobSkill.skill_name,
            func.count(func.distinct(JobSkill.job_id)).label("cnt"),
        )
        .where(
            JobSkill.job_id.in_(select(anchor_jobs_sq.c.job_id)),
            JobSkill.skill_name != skill_name.lower(),
        )
        .group_by(JobSkill.skill_name)
        .order_by(func.count(func.distinct(JobSkill.job_id)).desc())
        .limit(top_n)
    )

    result = await db.execute(stmt)
    return [
        SkillCoOccurrence(
            skill_a=skill_name.lower(),
            skill_b=row.skill_name,
            co_count=row.cnt,
            percentage=round(row.cnt / anchor_count * 100, 1),
        )
        for row in result.all()
    ]


async def build_skill_market_report(
    db: AsyncSession, title_pattern: str, *, top_n: int = 20
) -> SkillMarketReport:
    """Build a full market analysis report for jobs matching *title_pattern*."""
    top_skills, total_jobs = await get_skill_frequencies(
        db, title_pattern, top_n=top_n
    )
    technical_skills, _ = await get_skill_frequencies(
        db, title_pattern, category="technical", top_n=top_n
    )
    soft_skills, _ = await get_skill_frequencies(
        db, title_pattern, category="soft_skill", top_n=top_n
    )

    # Co-occurrences for the top skill
    co_occurrences: list[SkillCoOccurrence] = []
    if top_skills:
        co_occurrences = await get_skill_co_occurrences(
            db, title_pattern, top_skills[0].skill_name, top_n=10
        )

    # Category breakdown
    safe_pattern = escape_like(title_pattern.lower())
    job_ids_sq = (
        select(Job.id)
        .where(func.lower(Job.title).like(f"%{safe_pattern}%"))
        .subquery()
    )
    cat_stmt = (
        select(
            JobSkill.category,
            func.count(func.distinct(JobSkill.skill_name)).label("cnt"),
        )
        .where(JobSkill.job_id.in_(select(job_ids_sq.c.id)))
        .group_by(JobSkill.category)
    )
    cat_result = await db.execute(cat_stmt)
    category_breakdown = {row.category: row.cnt for row in cat_result.all()}

    return SkillMarketReport(
        title_pattern=title_pattern,
        total_jobs=total_jobs,
        top_skills=top_skills,
        technical_skills=technical_skills,
        soft_skills=soft_skills,
        co_occurrences=co_occurrences,
        category_breakdown=category_breakdown,
    )
