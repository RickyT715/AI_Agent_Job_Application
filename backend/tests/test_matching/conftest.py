"""Shared fixtures for matching tests."""

import chromadb
import pytest

from app.schemas.matching import JobMatchScore, ScoreBreakdown


@pytest.fixture
def ephemeral_chroma_client():
    """Create an ephemeral ChromaDB client for testing."""
    return chromadb.EphemeralClient()


@pytest.fixture
def mock_score() -> JobMatchScore:
    """Create a sample match score for testing."""
    return JobMatchScore(
        overall_score=8.0,
        breakdown=ScoreBreakdown(
            skills=9,
            experience=8,
            education=7,
            location=8,
            salary=8,
        ),
        reasoning="Strong match for backend engineering role.",
        strengths=["Python expertise", "FastAPI experience"],
        missing_skills=["Kubernetes operator development"],
        interview_talking_points=["Discuss ML pipeline experience"],
    )
