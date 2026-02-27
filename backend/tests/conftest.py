"""Root conftest with shared fixtures."""

import json
from pathlib import Path

import pytest

from app.schemas.matching import JobPosting

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_resume_text() -> str:
    """Load sample resume text from fixture file."""
    return (FIXTURES_DIR / "sample_resume.txt").read_text(encoding="utf-8")


@pytest.fixture
def sample_jobs() -> list[JobPosting]:
    """Load sample job postings from fixture file."""
    raw = json.loads((FIXTURES_DIR / "sample_jobs.json").read_text(encoding="utf-8"))
    return [JobPosting(**job) for job in raw]


@pytest.fixture
def sample_job(sample_jobs: list[JobPosting]) -> JobPosting:
    """Return a single high-match job (Senior Backend Engineer)."""
    return sample_jobs[0]


@pytest.fixture
def unrelated_job(sample_jobs: list[JobPosting]) -> JobPosting:
    """Return an unrelated job (Marketing Coordinator)."""
    return sample_jobs[8]  # job-009: Marketing Coordinator
