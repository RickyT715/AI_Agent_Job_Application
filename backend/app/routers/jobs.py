"""Job posting API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import limiter
from app.db.session import get_db_session
from app.models.job import Job
from app.schemas.api import (
    JobResponse,
    PaginatedResponse,
    ScrapeRequest,
    TaskStatusResponse,
)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=PaginatedResponse[JobResponse])
async def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = None,
    location: str | None = None,
    workplace_type: str | None = None,
    source: str | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    """List jobs with optional filters and full-text search."""
    query = select(Job)

    if q:
        query = query.where(
            Job.title.ilike(f"%{q}%") | Job.description.ilike(f"%{q}%")
        )
    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))
    if workplace_type:
        query = query.where(Job.workplace_type == workplace_type)
    if source:
        query = query.where(Job.source == source)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination
    query = query.order_by(Job.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return PaginatedResponse(
        items=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Get a single job by ID."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@router.post("/scrape", response_model=TaskStatusResponse)
@limiter.limit("10/minute")
async def trigger_scraping(request: Request, request_body: ScrapeRequest):
    """Trigger a background scraping task."""
    arq_pool = getattr(request.app.state, "arq_pool", None)
    if arq_pool is None:
        raise HTTPException(status_code=503, detail="Task queue unavailable")

    job = await arq_pool.enqueue_job(
        "run_scraping",
        queries=request_body.queries,
        location=request_body.location,
        remote_only=request_body.remote_only,
    )
    return TaskStatusResponse(task_id=job.job_id, status="queued")


@router.get("/scrape/{task_id}/status", response_model=TaskStatusResponse)
async def scraping_status(request: Request, task_id: str):
    """Get the status of a scraping task."""
    arq_pool = getattr(request.app.state, "arq_pool", None)
    if arq_pool is None:
        return TaskStatusResponse(task_id=task_id, status="unknown")

    try:
        from arq.jobs import Job as ArqJob

        job = ArqJob(task_id, arq_pool)
        info = await job.info()
        if info is None:
            return TaskStatusResponse(task_id=task_id, status="not_found")

        status = info.status.value if info.status else "unknown"
        result_data = info.result if info.result and isinstance(info.result, dict) else None
        return TaskStatusResponse(task_id=task_id, status=status, result=result_data)
    except Exception:
        return TaskStatusResponse(task_id=task_id, status="pending")
