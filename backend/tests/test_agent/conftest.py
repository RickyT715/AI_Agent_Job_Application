"""Shared fixtures for agent tests."""

import pytest

from app.services.agent.state import ApplicationState, make_initial_state

SAMPLE_USER_PROFILE = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "linkedin_url": "https://linkedin.com/in/johndoe",
}

SAMPLE_RESUME_TEXT = "John Doe\nSenior Software Engineer\n5+ years Python, FastAPI, PostgreSQL"


@pytest.fixture
def user_profile() -> dict[str, str]:
    return SAMPLE_USER_PROFILE.copy()


@pytest.fixture
def initial_state() -> ApplicationState:
    """A valid initial state for testing."""
    return make_initial_state(
        job_id=42,
        apply_url="https://boards.greenhouse.io/testco/jobs/12345",
        job_title="Software Engineer",
        company="TestCo",
        user_profile=SAMPLE_USER_PROFILE.copy(),
        resume_text=SAMPLE_RESUME_TEXT,
    )


@pytest.fixture
def generic_state() -> ApplicationState:
    """State for a generic (non-API) ATS platform."""
    return make_initial_state(
        job_id=99,
        apply_url="https://careers.somecompany.com/apply/12345",
        job_title="Data Engineer",
        company="SomeCo",
        user_profile=SAMPLE_USER_PROFILE.copy(),
        resume_text=SAMPLE_RESUME_TEXT,
    )
