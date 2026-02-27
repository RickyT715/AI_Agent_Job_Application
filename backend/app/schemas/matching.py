"""Pydantic schemas for the matching pipeline."""

from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    """Normalized job posting schema used across all scrapers."""

    external_id: str
    source: str  # greenhouse, lever, jsearch, workday, generic
    title: str
    company: str
    location: str | None = None
    workplace_type: str | None = None  # remote, hybrid, onsite
    description: str
    requirements: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    employment_type: str | None = None  # full-time, part-time, contract
    experience_level: str | None = None
    apply_url: str | None = None
    raw_data: dict | None = None


class ScoreBreakdown(BaseModel):
    """Individual dimension scores from LLM-as-Judge."""

    skills: int = Field(ge=1, le=10)
    experience: int = Field(ge=1, le=10)
    education: int = Field(ge=1, le=10)
    location: int = Field(ge=1, le=10)
    salary: int = Field(ge=1, le=10)


class JobMatchScore(BaseModel):
    """Structured output from Claude LLM-as-Judge scoring."""

    overall_score: float = Field(ge=1.0, le=10.0)
    breakdown: ScoreBreakdown
    reasoning: str
    strengths: list[str]
    missing_skills: list[str]
    interview_talking_points: list[str] = Field(default_factory=list)


class ScoredMatch(BaseModel):
    """A job posting with its match score."""

    job: JobPosting
    score: JobMatchScore
