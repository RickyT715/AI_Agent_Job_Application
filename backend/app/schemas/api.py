"""Pydantic request/response schemas for the API layer."""

from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class PaginationParams(BaseModel):
    """Common pagination parameters."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse[T](BaseModel):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

class JobResponse(BaseModel):
    """Job posting returned from the API."""

    id: int
    external_id: str
    source: str
    title: str
    company: str
    location: str | None = None
    workplace_type: str | None = None
    description: str
    requirements: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    apply_url: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ScrapeRequest(BaseModel):
    """Request to trigger job scraping."""

    queries: list[str] = Field(default=["Software Engineer"])
    location: str = ""
    remote_only: bool = False


class TaskStatusResponse(BaseModel):
    """Status of a background task."""

    task_id: str
    status: str  # queued, running, complete, failed
    result: dict | None = None


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------

class MatchResponse(BaseModel):
    """Match result returned from the API."""

    id: int
    job_id: int
    overall_score: float
    score_breakdown: dict
    reasoning: str
    strengths: list[str]
    missing_skills: list[str]
    interview_talking_points: list[str] = []
    job: JobResponse | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class MatchRunRequest(BaseModel):
    """Request to trigger matching pipeline."""

    rescore: bool = False


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class AgentStartRequest(BaseModel):
    """Request to start the browser agent for a job."""

    job_id: int
    match_id: int | None = None


class AgentResumeRequest(BaseModel):
    """Request to resume an interrupted agent."""

    action: str = Field(description="approve, reject, or edit")
    edits: dict | None = None


class AgentStatusMessage(BaseModel):
    """WebSocket message for agent progress updates."""

    step: str
    status: str  # navigating, filling, reviewing, submitted, failed
    progress: float = Field(ge=0.0, le=1.0)
    message: str = ""
    fields_filled: dict | None = None
    screenshot_b64: str | None = None


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class ReportGenerateRequest(BaseModel):
    """Request to generate a PDF report."""

    match_id: int


class CoverLetterRequest(BaseModel):
    """Request to generate a cover letter."""

    match_id: int


class CoverLetterResponse(BaseModel):
    """Generated cover letter."""

    id: int
    match_id: int
    content: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Config / Preferences
# ---------------------------------------------------------------------------

class PreferencesResponse(BaseModel):
    """User preferences as returned by the API."""

    job_titles: list[str]
    locations: list[str]
    salary_min: int | None = None
    salary_max: int | None = None
    workplace_types: list[str]
    experience_level: str
    weights: dict
    employment_types: list[str] = []
    date_posted: str = "month"
    salary_currency: str = "USD"
    final_results_count: int = 10
    num_pages_per_source: int = 1
    enabled_sources: list[str] = []
    greenhouse_board_tokens: list[str] = []
    lever_companies: list[str] = []
    workday_urls: list[str] = []


class PreferencesUpdateRequest(BaseModel):
    """Request to update user preferences."""

    job_titles: list[str] | None = None
    locations: list[str] | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    workplace_types: list[str] | None = None
    experience_level: str | None = None
    weights: dict | None = None
    employment_types: list[str] | None = None
    date_posted: str | None = None
    salary_currency: str | None = None
    final_results_count: int | None = None
    num_pages_per_source: int | None = None
    enabled_sources: list[str] | None = None
    greenhouse_board_tokens: list[str] | None = None
    lever_companies: list[str] | None = None
    workday_urls: list[str] | None = None


class ResumeUploadResponse(BaseModel):
    """Response after resume upload."""

    message: str
    character_count: int
