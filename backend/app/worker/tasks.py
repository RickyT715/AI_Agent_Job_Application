"""ARQ background task definitions.

These tasks are enqueued from the API layer and run by the ARQ worker process.
"""

import logging

from sqlalchemy import select

from app.config import UserConfig, get_settings, load_user_config
from app.db.session import get_db_session_ctx
from app.models.application import Application
from app.models.job import Job
from app.models.match import MatchResult
from app.models.user import User
from app.schemas.matching import JobPosting
from app.services.agent.graph import compile_agent_graph
from app.services.agent.state import make_initial_state
from app.services.matching.pipeline import MatchingPipeline
from app.services.scraping.api.jsearch import JSearchScraper
from app.services.scraping.deduplicator import JobDeduplicator
from app.services.scraping.orchestrator import ScrapingOrchestrator

logger = logging.getLogger(__name__)


def _job_model_to_posting(j: Job) -> JobPosting:
    """Convert a DB Job model to a JobPosting schema."""
    return JobPosting(
        external_id=j.external_id,
        source=j.source,
        title=j.title,
        company=j.company,
        location=j.location,
        workplace_type=j.workplace_type,
        description=j.description,
        requirements=j.requirements,
        salary_min=j.salary_min,
        salary_max=j.salary_max,
        salary_currency=j.salary_currency,
        employment_type=j.employment_type,
        experience_level=j.experience_level,
        apply_url=j.apply_url,
    )


def _build_scrapers(config: UserConfig) -> list:
    """Build scraper list based on user's enabled_sources config."""
    scrapers = []

    if "jsearch" in config.enabled_sources:
        scrapers.append(JSearchScraper())

    if "adzuna" in config.enabled_sources:
        from app.services.scraping.api.adzuna import AdzunaScraper
        scrapers.append(AdzunaScraper())

    if "arbeitnow" in config.enabled_sources:
        from app.services.scraping.api.arbeitnow import ArbeitnowScraper
        scrapers.append(ArbeitnowScraper())

    if "greenhouse" in config.enabled_sources and config.greenhouse_board_tokens:
        from app.services.scraping.api.greenhouse import GreenhouseScraper
        scrapers.append(GreenhouseScraper(board_tokens=config.greenhouse_board_tokens))

    if "lever" in config.enabled_sources and config.lever_companies:
        from app.services.scraping.api.lever import LeverScraper
        scrapers.append(LeverScraper(companies=config.lever_companies))

    if "remoteok" in config.enabled_sources:
        from app.services.scraping.api.remoteok import RemoteOKScraper
        scrapers.append(RemoteOKScraper())

    if "weworkremotely" in config.enabled_sources:
        from app.services.scraping.api.weworkremotely import WeWorkRemotelyScraper
        scrapers.append(WeWorkRemotelyScraper())

    # Default to JSearch if no scrapers configured
    if not scrapers:
        scrapers.append(JSearchScraper())

    return scrapers


async def run_scraping(
    ctx: dict, queries: list[str], location: str = "", remote_only: bool = False,
):
    """Background task: run scraping orchestrator.

    Args:
        ctx: ARQ worker context (contains Redis pool).
        queries: List of search queries.
        location: Location filter.
        remote_only: Whether to filter for remote only.
    """
    logger.info(f"Starting scraping task: queries={queries}, location={location}")

    settings = get_settings()
    config = load_user_config(settings.user_config_path)
    scrapers = _build_scrapers(config)

    orchestrator = ScrapingOrchestrator(
        scrapers=scrapers,
        deduplicator=JobDeduplicator(),
    )

    results = {}
    all_jobs: list[JobPosting] = []

    for query in queries:
        result = await orchestrator.run(
            query,
            location=location,
            remote_only=remote_only,
            num_pages=config.num_pages_per_source,
            employment_type=(
                config.employment_types[0] if config.employment_types else None
            ),
            date_posted=config.date_posted,
        )
        all_jobs.extend(result.jobs)
        results[query] = {
            "total": result.total,
            "new": result.new,
            "duplicates": result.duplicates,
            "errors": result.errors,
        }

    # Persist scraped jobs to database
    async with get_db_session_ctx() as db:
        for posting in all_jobs:
            # Check for existing job by external_id + source
            existing = await db.execute(
                select(Job).where(
                    Job.external_id == posting.external_id,
                    Job.source == posting.source,
                )
            )
            if existing.scalar_one_or_none():
                continue

            job = Job(
                external_id=posting.external_id,
                source=posting.source,
                title=posting.title,
                company=posting.company,
                location=posting.location,
                workplace_type=posting.workplace_type,
                description=posting.description,
                requirements=posting.requirements,
                salary_min=posting.salary_min,
                salary_max=posting.salary_max,
                salary_currency=posting.salary_currency,
                employment_type=posting.employment_type,
                experience_level=posting.experience_level,
                apply_url=posting.apply_url,
                raw_data=posting.raw_data,
            )
            db.add(job)

    logger.info(f"Scraping complete: {results}")
    return results


async def run_matching(ctx: dict, user_id: int = 1):
    """Background task: run matching pipeline for a user.

    Args:
        ctx: ARQ worker context.
        user_id: The user to run matching for.
    """
    logger.info(f"Starting matching task for user {user_id}")

    # Load user and jobs from DB
    async with get_db_session_ctx() as db:
        user = await db.get(User, user_id)
        if not user or not user.resume_text:
            logger.error(f"User {user_id} not found or has no resume")
            return {"status": "failed", "error": "User not found or missing resume"}

        resume_text = user.resume_text
        jobs_result = await db.execute(select(Job))
        db_jobs = jobs_result.scalars().all()

    if not db_jobs:
        logger.warning("No jobs in database to match against")
        return {"status": "complete", "matches": 0}

    # Skip already-scored jobs for this user
    async with get_db_session_ctx() as db:
        scored_result = await db.execute(
            select(MatchResult.job_id).where(MatchResult.user_id == user_id)
        )
        scored_job_ids = {row for row in scored_result.scalars().all()}

    unscored_jobs = [j for j in db_jobs if j.id not in scored_job_ids]
    if not unscored_jobs:
        logger.info(f"All {len(db_jobs)} jobs already scored for user {user_id}")
        return {"status": "complete", "matches": 0, "skipped": len(db_jobs)}

    logger.info(
        f"Matching {len(unscored_jobs)} unscored jobs "
        f"(skipped {len(db_jobs) - len(unscored_jobs)} already scored)"
    )

    postings = [_job_model_to_posting(j) for j in unscored_jobs]

    config = load_user_config(get_settings().user_config_path)
    pipeline = MatchingPipeline(final_k=config.final_results_count, user_config=config)
    matches = await pipeline.match(resume_text, jobs=postings)

    # Store results in DB
    async with get_db_session_ctx() as db:
        for m in matches:
            # Find the DB job ID by external_id + source
            job_result = await db.execute(
                select(Job).where(
                    Job.external_id == m.job.external_id,
                    Job.source == m.job.source,
                )
            )
            db_job = job_result.scalar_one_or_none()
            if not db_job:
                continue

            # Check for existing match
            existing = await db.execute(
                select(MatchResult).where(
                    MatchResult.user_id == user_id,
                    MatchResult.job_id == db_job.id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            match_result = MatchResult(
                user_id=user_id,
                job_id=db_job.id,
                overall_score=m.score.overall_score,
                score_breakdown=m.score.breakdown,
                reasoning=m.score.reasoning,
                strengths=m.score.strengths,
                missing_skills=m.score.missing_skills,
                interview_talking_points=getattr(m.score, "interview_talking_points", []),
                ats_score=m.ats_score.score if m.ats_score else None,
                ats_details=m.ats_score.model_dump() if m.ats_score else None,
                requirement_matches=(
                    [rm.model_dump() for rm in m.score.requirement_matches]
                    if m.score.requirement_matches
                    else None
                ),
                requirements_met_ratio=m.score.requirements_met_ratio,
                integrated_score=m.integrated_score,
            )
            db.add(match_result)

    logger.info(f"Matching complete: {len(matches)} matches for user {user_id}")
    return {"status": "complete", "matches": len(matches)}


async def run_agent(ctx: dict, job_id: int, user_id: int = 1):
    """Background task: run browser agent for a job application.

    Args:
        ctx: ARQ worker context.
        job_id: The job to apply to.
        user_id: The user applying.
    """
    logger.info(f"Starting agent task: job_id={job_id}, user_id={user_id}")

    from langgraph.checkpoint.memory import MemorySaver

    # Load job and user from DB
    async with get_db_session_ctx() as db:
        job = await db.get(Job, job_id)
        if not job:
            return {"status": "failed", "error": f"Job {job_id} not found"}

        user = await db.get(User, user_id)
        if not user:
            return {"status": "failed", "error": f"User {user_id} not found"}

        # Create application record
        application = Application(
            user_id=user_id,
            job_id=job_id,
            status="in_progress",
            ats_platform=None,
            apply_url=job.apply_url,
        )
        db.add(application)
        await db.flush()
        app_id = application.id

    # Build user profile from DB user
    user_profile = {
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone or "",
        "linkedin_url": user.linkedin_url or "",
    }

    graph = compile_agent_graph(checkpointer=MemorySaver())
    state = make_initial_state(
        job_id=job_id,
        apply_url=job.apply_url or "",
        job_title=job.title,
        company=job.company,
        user_profile=user_profile,
        resume_text=user.resume_text or "",
    )

    try:
        result = await graph.ainvoke(
            state,
            config={"configurable": {"thread_id": f"agent-{job_id}"}},
        )
        final_status = result.get("status", "failed")
    except Exception as e:
        logger.error(f"Agent failed for job {job_id}: {e}", exc_info=True)
        final_status = "failed"

    # Update application status
    async with get_db_session_ctx() as db:
        application = await db.get(Application, app_id)
        if application:
            application.status = final_status

    logger.info(f"Agent complete: job_id={job_id}, status={final_status}")
    return {"status": final_status, "job_id": job_id}


async def startup(ctx: dict):
    """ARQ worker startup hook."""
    logger.info("ARQ worker starting up")


async def shutdown(ctx: dict):
    """ARQ worker shutdown hook."""
    logger.info("ARQ worker shutting down")
