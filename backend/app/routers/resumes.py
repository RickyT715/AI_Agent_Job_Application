"""Resume generation API endpoints (external microservice integration)."""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.session import get_db_session
from app.models.generated_resume import GeneratedResume
from app.models.job import Job
from app.models.match import MatchResult
from app.models.user import User
from app.schemas.api import (
    ResumeGenerateRequest,
    ResumeGenerateResponse,
    ResumeGeneratorHealthResponse,
    ResumeStatusResponse,
)
from app.services.resume_generator.client import (
    ResumeGeneratorClient,
    ResumeGeneratorError,
    save_pdf_to_disk,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


def _get_client() -> ResumeGeneratorClient:
    """Build a client; raises 503 if the service URL is not configured."""
    url = get_settings().resume_generator_url
    if not url:
        raise HTTPException(
            status_code=503,
            detail="Resume generator service not configured",
        )
    return ResumeGeneratorClient(base_url=url)


@router.get("/health", response_model=ResumeGeneratorHealthResponse)
async def resume_generator_health():
    """Check whether the resume generator service is reachable."""
    url = get_settings().resume_generator_url
    if not url:
        return ResumeGeneratorHealthResponse(
            available=False, detail="Service URL not configured"
        )
    try:
        client = ResumeGeneratorClient(base_url=url)
        await client.health_check()
        return ResumeGeneratorHealthResponse(available=True, detail="Service healthy")
    except Exception as exc:
        return ResumeGeneratorHealthResponse(available=False, detail=str(exc))


@router.post("/generate", response_model=ResumeGenerateResponse)
async def generate_resume(
    request: ResumeGenerateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Create and start a resume generation task for a given match."""
    client = _get_client()

    # Load match with job + user
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

    try:
        # Sync user info, then create + start the pipeline
        await client.sync_user_info(resume_text)
        task = await client.create_and_start(
            job_description=job.description,
            generate_cover_letter=request.generate_cover_letter,
            template_id=request.template_id,
            language=request.language,
            experience_level=request.experience_level,
            provider=request.provider,
        )
    except ResumeGeneratorError as exc:
        raise HTTPException(status_code=502, detail=exc.detail) from exc

    task_id = str(task["id"])
    status = task.get("status", "running")

    record = GeneratedResume(
        user_id=user.id,
        match_id=match.id,
        external_task_id=task_id,
        status=status,
        language=request.language,
        provider=request.provider,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)

    return ResumeGenerateResponse.model_validate(record)


@router.get("/{resume_id}/status", response_model=ResumeStatusResponse)
async def get_resume_status(
    resume_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Get the current status of a generated resume, polling external if needed."""
    result = await db.execute(
        select(GeneratedResume).where(GeneratedResume.id == resume_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Generated resume not found")

    # If still in progress, poll the external service
    if record.status in ("pending", "running"):
        try:
            client = _get_client()
            task = await client.get_task_status(record.external_task_id)
            new_status = task.get("status", record.status)
            record.status = new_status

            # Download artifacts when newly completed
            if new_status == "completed":
                try:
                    resume_pdf = await client.download_resume_pdf(record.external_task_id)
                    filename = f"resume-{record.id}.pdf"
                    path = save_pdf_to_disk(resume_pdf, filename)
                    record.resume_pdf_path = str(path)
                except ResumeGeneratorError:
                    logger.warning("Could not download resume PDF for %s", record.id)

                try:
                    cl_pdf = await client.download_cover_letter_pdf(record.external_task_id)
                    cl_filename = f"cover-letter-{record.id}.pdf"
                    cl_path = save_pdf_to_disk(cl_pdf, cl_filename)
                    record.cover_letter_pdf_path = str(cl_path)
                except ResumeGeneratorError:
                    logger.warning("Could not download cover letter PDF for %s", record.id)

                try:
                    cl_text = await client.get_cover_letter_text(record.external_task_id)
                    record.cover_letter_text = cl_text
                except ResumeGeneratorError:
                    pass

            elif new_status == "failed":
                record.error_message = task.get("error", "Unknown error")

        except (ResumeGeneratorError, HTTPException):
            pass  # Keep existing status on communication failure

    return ResumeStatusResponse.model_validate(record)


@router.get("/{resume_id}/download/resume")
async def download_resume_pdf(
    resume_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Serve the generated resume PDF."""
    result = await db.execute(
        select(GeneratedResume).where(GeneratedResume.id == resume_id)
    )
    record = result.scalar_one_or_none()
    if not record or not record.resume_pdf_path:
        raise HTTPException(status_code=404, detail="Resume PDF not found")

    path = Path(record.resume_pdf_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Resume PDF file missing")

    return Response(
        content=path.read_bytes(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="resume-{record.id}.pdf"'},
    )


@router.get("/{resume_id}/download/cover-letter")
async def download_cover_letter_pdf(
    resume_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Serve the generated cover letter PDF."""
    result = await db.execute(
        select(GeneratedResume).where(GeneratedResume.id == resume_id)
    )
    record = result.scalar_one_or_none()
    if not record or not record.cover_letter_pdf_path:
        raise HTTPException(status_code=404, detail="Cover letter PDF not found")

    path = Path(record.cover_letter_pdf_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Cover letter PDF file missing")

    return Response(
        content=path.read_bytes(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="cover-letter-{record.id}.pdf"'
        },
    )


@router.get("/by-match/{match_id}", response_model=list[ResumeStatusResponse])
async def list_resumes_for_match(
    match_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """List all generated resumes for a specific match."""
    result = await db.execute(
        select(GeneratedResume)
        .where(GeneratedResume.match_id == match_id)
        .order_by(GeneratedResume.created_at.desc())
    )
    records = result.scalars().all()
    return [ResumeStatusResponse.model_validate(r) for r in records]
