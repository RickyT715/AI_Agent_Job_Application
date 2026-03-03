"""Match result API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.auth import require_api_key
from app.core.utils import escape_like
from app.db.session import get_db_session
from app.models.job import Job
from app.models.match import MatchResult
from app.schemas.api import (
    MatchResponse,
    MatchRunRequest,
    PaginatedResponse,
    TaskStatusResponse,
)

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("", response_model=PaginatedResponse[MatchResponse])
async def list_matches(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_score: float | None = None,
    q: str | None = None,
    location: str | None = None,
    workplace_type: str | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    """List match results sorted by score descending."""
    query = select(MatchResult).options(joinedload(MatchResult.job))

    if min_score is not None:
        query = query.where(MatchResult.overall_score >= min_score)

    # Join with Job for text/location/workplace filters
    if q or location or workplace_type:
        query = query.join(MatchResult.job)
        if q:
            safe_q = escape_like(q)
            query = query.where(
                Job.title.ilike(f"%{safe_q}%") | Job.description.ilike(f"%{safe_q}%")
            )
        if location:
            safe_loc = escape_like(location)
            query = query.where(Job.location.ilike(f"%{safe_loc}%"))
        if workplace_type:
            query = query.where(Job.workplace_type == workplace_type)

    # Total count (replicate filters)
    count_base = select(MatchResult)
    if min_score is not None:
        count_base = count_base.where(MatchResult.overall_score >= min_score)
    if q or location or workplace_type:
        count_base = count_base.join(MatchResult.job)
        if q:
            safe_q = escape_like(q)
            count_base = count_base.where(
                Job.title.ilike(f"%{safe_q}%") | Job.description.ilike(f"%{safe_q}%")
            )
        if location:
            safe_loc = escape_like(location)
            count_base = count_base.where(Job.location.ilike(f"%{safe_loc}%"))
        if workplace_type:
            count_base = count_base.where(Job.workplace_type == workplace_type)
    count_query = select(func.count()).select_from(count_base.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sorted + paginated
    query = query.order_by(MatchResult.overall_score.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    matches = result.unique().scalars().all()

    return PaginatedResponse(
        items=[MatchResponse.model_validate(m) for m in matches],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Get a single match result with full detail."""
    result = await db.execute(
        select(MatchResult)
        .options(joinedload(MatchResult.job))
        .where(MatchResult.id == match_id)
    )
    match = result.unique().scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return MatchResponse.model_validate(match)


@router.post("/run", response_model=TaskStatusResponse)
async def trigger_matching(
    request: Request,
    body: MatchRunRequest | None = None,
    _key: str = Depends(require_api_key),
):
    """Trigger the matching pipeline as a background task."""
    arq_pool = getattr(request.app.state, "arq_pool", None)
    if arq_pool is None:
        raise HTTPException(status_code=503, detail="Task queue unavailable")

    job = await arq_pool.enqueue_job("run_matching")
    return TaskStatusResponse(task_id=job.job_id, status="queued")


@router.post("/{match_id}/rescore", response_model=TaskStatusResponse)
async def rescore_match(match_id: int, request: Request, _key: str = Depends(require_api_key)):
    """Re-run scoring for a specific match."""
    arq_pool = getattr(request.app.state, "arq_pool", None)
    if arq_pool is None:
        raise HTTPException(status_code=503, detail="Task queue unavailable")

    job = await arq_pool.enqueue_job("run_matching", _job_id=f"rescore-{match_id}")
    return TaskStatusResponse(task_id=job.job_id, status="queued")
