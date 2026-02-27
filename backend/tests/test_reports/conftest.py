"""Shared fixtures for report tests."""

import pytest


@pytest.fixture
def sample_report_data() -> dict:
    """Complete report data for testing."""
    return {
        "job_title": "Senior Software Engineer",
        "company": "TechCorp Inc.",
        "overall_score": 8.5,
        "breakdown": {
            "skills": 9,
            "experience": 8,
            "education": 7,
            "location": 9,
            "salary": 8,
        },
        "reasoning": "Strong match due to extensive Python and FastAPI experience.",
        "strengths": ["Python expertise", "FastAPI experience", "Cloud deployment"],
        "missing_skills": ["Kubernetes", "Go programming"],
        "interview_talking_points": [
            "Discuss ML pipeline architecture",
            "Talk about system design experience",
        ],
        "salary_min": 120000,
        "salary_max": 180000,
        "salary_currency": "USD",
    }


@pytest.fixture
def sample_report_data_minimal() -> dict:
    """Minimal report data — no salary, no talking points."""
    return {
        "job_title": "Data Analyst",
        "company": "Analytics Co",
        "overall_score": 5.5,
        "breakdown": {"skills": 6, "experience": 5},
        "reasoning": "Partial match.",
        "strengths": ["SQL"],
        "missing_skills": ["Tableau"],
    }


@pytest.fixture
def sample_cover_letter_input() -> dict:
    """Input data for cover letter generation."""
    return {
        "job_title": "Senior Backend Engineer",
        "company": "TechCorp",
        "job_description": "Build scalable APIs with Python, FastAPI, PostgreSQL. 5+ years required.",
        "resume_text": "John Doe. 6 years Python, FastAPI, PostgreSQL. Built microservices at scale.",
        "strengths": ["Python", "FastAPI", "PostgreSQL"],
        "missing_skills": ["Kubernetes"],
    }
