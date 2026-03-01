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


class RequirementMatch(BaseModel):
    """Point-by-point matching of a single job requirement."""

    requirement: str
    category: str  # technical_skill, soft_skill, experience, education, certification, other
    met: bool
    evidence: str  # Brief evidence from resume or "Not found"
    confidence: float = Field(ge=0.0, le=1.0)


class ATSKeywordScore(BaseModel):
    """Programmatic keyword overlap scoring (no LLM calls)."""

    score: float = Field(ge=0.0, le=100.0)
    matched_keywords: list[str]
    missing_keywords: list[str]
    total_job_keywords: int
    technical_match_pct: float = Field(ge=0.0, le=100.0)
    soft_skill_match_pct: float = Field(ge=0.0, le=100.0)


class JobMatchScore(BaseModel):
    """Structured output from Claude LLM-as-Judge scoring."""

    overall_score: float = Field(ge=1.0, le=10.0)
    breakdown: ScoreBreakdown
    reasoning: str
    strengths: list[str]
    missing_skills: list[str]
    interview_talking_points: list[str] = Field(default_factory=list)
    requirement_matches: list[RequirementMatch] = Field(default_factory=list)
    requirements_met_ratio: float | None = None


class ScoredMatch(BaseModel):
    """A job posting with its match score."""

    job: JobPosting
    score: JobMatchScore
    ats_score: ATSKeywordScore | None = None
    integrated_score: float | None = None
