"""Persist extracted skills into the database."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.job_skill import JobSkill
from app.services.matching.skill_extractor import extract_skills_from_job

logger = logging.getLogger(__name__)


async def extract_and_persist_skills(
    db: AsyncSession, job: Job, *, skip_existing: bool = True
) -> int:
    """Extract skills from a job and persist them as ``JobSkill`` rows.

    Args:
        db: Active async DB session (caller commits).
        job: A ``Job`` instance with ``description`` (and optionally ``requirements``).
        skip_existing: When *True*, skip jobs that already have skills.

    Returns:
        Number of skill rows created.
    """
    if skip_existing:
        result = await db.execute(
            select(JobSkill.id).where(JobSkill.job_id == job.id).limit(1)
        )
        if result.scalar_one_or_none() is not None:
            return 0

    technical, soft = extract_skills_from_job(
        job.description, job.requirements
    )

    count = 0
    for skill in technical:
        db.add(
            JobSkill(
                job_id=job.id,
                skill_name=skill.lower(),
                category="technical",
            )
        )
        count += 1

    for skill in soft:
        db.add(
            JobSkill(
                job_id=job.id,
                skill_name=skill.lower(),
                category="soft_skill",
            )
        )
        count += 1

    return count


async def backfill_all_job_skills(db: AsyncSession) -> dict[str, int]:
    """Backfill skills for all jobs that don't yet have any.

    Returns:
        ``{"jobs_processed": N, "total_skills": M}``
    """
    # Find jobs with no skills
    subq = select(JobSkill.job_id).distinct().subquery()
    result = await db.execute(
        select(Job).where(Job.id.notin_(select(subq.c.job_id)))
    )
    jobs = result.scalars().all()

    total_skills = 0
    for job in jobs:
        count = await extract_and_persist_skills(db, job, skip_existing=False)
        total_skills += count

    logger.info("Backfilled skills: %d jobs, %d skills", len(jobs), total_skills)
    return {"jobs_processed": len(jobs), "total_skills": total_skills}
