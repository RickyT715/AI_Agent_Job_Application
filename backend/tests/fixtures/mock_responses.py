"""Deterministic mock LLM response factories for testing."""

from app.schemas.matching import JobMatchScore, ScoreBreakdown


def make_high_match_score() -> JobMatchScore:
    """Create a high match score response (good match)."""
    return JobMatchScore(
        overall_score=8.5,
        breakdown=ScoreBreakdown(
            skills=9,
            experience=8,
            education=8,
            location=9,
            salary=8,
        ),
        reasoning=(
            "Strong match. The candidate has extensive Python and FastAPI experience "
            "matching the core requirements. ML pipeline experience aligns well with "
            "the role's focus on AI infrastructure."
        ),
        strengths=[
            "5+ years Python experience matches requirement",
            "Direct FastAPI and PostgreSQL experience",
            "ML pipeline and RAG system experience",
            "Remote work experience aligns with location",
        ],
        missing_skills=[
            "No specific mention of Kubernetes operator development",
        ],
        interview_talking_points=[
            "Highlight the RAG pipeline built at TechCorp",
            "Discuss microservices migration leadership",
            "Mention ML inference pipeline scale (10M+ predictions/day)",
        ],
    )


def make_low_match_score() -> JobMatchScore:
    """Create a low match score response (poor match)."""
    return JobMatchScore(
        overall_score=3.0,
        breakdown=ScoreBreakdown(
            skills=2,
            experience=3,
            education=4,
            location=5,
            salary=3,
        ),
        reasoning=(
            "Poor match. The candidate is a software engineer but the role requires "
            "marketing experience and skills that don't overlap with their background."
        ),
        strengths=[
            "Strong communication skills implied by mentoring experience",
        ],
        missing_skills=[
            "Social media management",
            "Email marketing tools (Mailchimp, HubSpot)",
            "Marketing campaign coordination",
            "Content writing for marketing",
        ],
        interview_talking_points=[
            "Transferable project management skills",
        ],
    )


def make_medium_match_score() -> JobMatchScore:
    """Create a medium match score response (partial match)."""
    return JobMatchScore(
        overall_score=6.5,
        breakdown=ScoreBreakdown(
            skills=7,
            experience=6,
            education=7,
            location=6,
            salary=7,
        ),
        reasoning=(
            "Moderate match. The candidate has relevant technical skills but lacks "
            "some specific domain expertise required for the role."
        ),
        strengths=[
            "Python proficiency matches requirement",
            "Database experience with PostgreSQL",
            "CI/CD and Docker experience",
        ],
        missing_skills=[
            "No financial systems experience",
            "Payment API integration not mentioned",
            "Security certifications not listed",
        ],
        interview_talking_points=[
            "Emphasize API development experience",
            "Discuss data pipeline reliability practices",
        ],
    )
