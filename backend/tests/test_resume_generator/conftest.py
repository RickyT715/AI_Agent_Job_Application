"""Fixtures for resume generator tests."""

import pytest


@pytest.fixture
def sample_task_response():
    """Sample task response from the resume generator API."""
    return {
        "id": "task-abc-123",
        "status": "running",
        "job_description": "Senior Python developer...",
        "generate_cover_letter": True,
        "language": "en",
        "experience_level": "mid",
        "provider": "anthropic",
    }


@pytest.fixture
def completed_task_response():
    """Sample completed task response."""
    return {
        "id": "task-abc-123",
        "status": "completed",
        "job_description": "Senior Python developer...",
        "generate_cover_letter": True,
        "language": "en",
        "experience_level": "mid",
        "provider": "anthropic",
        "resume_path": "/output/task-abc-123/resume.pdf",
        "cover_letter_path": "/output/task-abc-123/cover_letter.pdf",
    }


@pytest.fixture
def failed_task_response():
    """Sample failed task response."""
    return {
        "id": "task-abc-123",
        "status": "failed",
        "error": "LaTeX compilation failed",
    }


@pytest.fixture
def health_response():
    """Sample health check response."""
    return {"status": "healthy", "version": "1.0.0"}
