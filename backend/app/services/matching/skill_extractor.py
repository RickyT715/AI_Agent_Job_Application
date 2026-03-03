"""Public skill extraction API.

Wraps the keyword extraction logic from ``ats_scorer`` to expose a clean
public interface for extracting technical and soft skills from text.
"""

from app.services.matching.ats_scorer import (
    _extract_keywords,
    _extract_keywords_zh,
)
from app.services.matching.language_detect import detect_language


def extract_skills(
    text: str, language: str = "auto"
) -> tuple[set[str], set[str]]:
    """Extract technical and soft-skill keywords from *text*.

    Args:
        text: Arbitrary text (job description, resume, etc.).
        language: ``"auto"`` (detect), ``"en"``, or ``"zh"``.

    Returns:
        ``(technical_set, soft_set)`` of normalized keyword strings.
    """
    if not text or not text.strip():
        return set(), set()

    if language == "auto":
        language = detect_language(text)

    if language == "zh":
        return _extract_keywords_zh(text)
    return _extract_keywords(text)


def extract_skills_from_job(
    description: str,
    requirements: str | None = None,
    language: str = "auto",
) -> tuple[set[str], set[str]]:
    """Extract skills from a job posting's description + requirements.

    Combines both text fields before extraction so that skills mentioned
    in either section are captured.

    Args:
        description: Job description text.
        requirements: Optional separate requirements text.
        language: ``"auto"`` (detect), ``"en"``, or ``"zh"``.

    Returns:
        ``(technical_set, soft_set)`` of normalized keyword strings.
    """
    combined = description or ""
    if requirements:
        combined = f"{combined}\n{requirements}"
    return extract_skills(combined, language=language)
