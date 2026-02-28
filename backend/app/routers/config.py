"""User configuration and preferences API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import MatchingWeights, UserConfig, get_settings, load_user_config
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.api import (
    PreferencesResponse,
    PreferencesUpdateRequest,
    ResumeUploadResponse,
)

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences():
    """Get current user preferences from YAML config."""
    settings = get_settings()
    config = load_user_config(settings.user_config_path)
    return _config_to_response(config)


def _config_to_response(config: UserConfig) -> PreferencesResponse:
    """Convert UserConfig to PreferencesResponse."""
    settings = get_settings()
    return PreferencesResponse(
        job_titles=config.job_titles,
        locations=config.locations,
        salary_min=config.salary_min,
        salary_max=config.salary_max,
        workplace_types=config.workplace_types,
        experience_level=config.experience_level,
        weights=config.weights.model_dump(),
        employment_types=config.employment_types,
        date_posted=config.date_posted,
        salary_currency=config.salary_currency,
        final_results_count=config.final_results_count,
        num_pages_per_source=config.num_pages_per_source,
        enabled_sources=config.enabled_sources,
        greenhouse_board_tokens=config.greenhouse_board_tokens,
        lever_companies=config.lever_companies,
        workday_urls=config.workday_urls,
        anthropic_base_url=settings.anthropic_base_url,
    )


@router.put("/preferences", response_model=PreferencesResponse)
async def update_preferences(request: PreferencesUpdateRequest):
    """Update user preferences.

    Validates the new preferences and saves to YAML config.
    """
    settings = get_settings()
    current = load_user_config(settings.user_config_path)

    # Apply updates
    update_data = request.model_dump(exclude_none=True)

    if "weights" in update_data:
        # Validate weights
        try:
            MatchingWeights(**update_data["weights"])
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    # Handle anthropic_base_url separately (infrastructure setting)
    if "anthropic_base_url" in update_data:
        settings.anthropic_base_url = update_data.pop("anthropic_base_url")

    merged = current.model_dump()
    merged.update(update_data)

    # Validate the full config
    try:
        updated_config = UserConfig(**merged)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Save to YAML
    import yaml
    with open(settings.user_config_path, "w", encoding="utf-8") as f:
        yaml.dump(updated_config.model_dump(mode="json"), f, default_flow_style=False)

    return _config_to_response(updated_config)


@router.post("/resume", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile,
    db: AsyncSession = Depends(get_db_session),
):
    """Upload a resume file (text/plain or PDF).

    Stores the extracted text in the user's profile.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()

    # For now, handle plain text only
    # TODO: Add PDF extraction support
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Only plain text files are supported. PDF support coming soon.",
        )

    # Store in first user record (single-user mode)
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user:
        user.resume_text = text
    else:
        user = User(
            email="user@example.com",
            full_name="Default User",
            resume_text=text,
        )
        db.add(user)

    return ResumeUploadResponse(
        message="Resume uploaded successfully",
        character_count=len(text),
    )
