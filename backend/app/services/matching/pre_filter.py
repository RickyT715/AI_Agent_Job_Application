"""Pre-filter module to remove obviously irrelevant jobs before expensive scoring.

Applies fast heuristic filters: seniority level, location, and employment type.
"""

import logging
import re

from app.config import UserConfig
from app.schemas.matching import JobPosting

logger = logging.getLogger(__name__)

# Seniority keywords mapped to levels (higher = more senior)
_SENIORITY_KEYWORDS: list[tuple[str, int, bool]] = [
    # (keyword, level, word_boundary) — word_boundary=True requires the keyword
    # to appear as a whole word (not a substring of another word)
    ("internship", 0, False),
    ("intern", 0, True),
    ("junior", 1, False),
    ("entry", 1, True),
    ("associate", 1, False),
    ("senior", 3, False),
    ("sr.", 3, False),
    ("sr ", 3, False),
    ("staff", 4, False),
    ("principal", 5, False),
    ("distinguished", 5, False),
    ("fellow", 5, True),
    ("director", 6, False),
    ("head of", 6, False),
    ("vice president", 7, False),
    ("vp ", 7, False),
    (" vp", 7, False),
    ("chief", 8, True),
    (" cto", 8, False),
    (" cio", 8, False),
]

# Maps user experience_level to the acceptable seniority range (min_level, max_level)
_LEVEL_RANGES: dict[str, tuple[int, int]] = {
    "entry": (0, 2),      # intern, junior, mid
    "mid": (1, 3),        # junior, mid, senior
    "senior": (2, 4),     # mid, senior, staff
    "lead": (3, 5),       # senior, staff, principal
    "executive": (5, 8),  # principal+
}

# Normalize employment type keywords
_EMPLOYMENT_ALIASES: dict[str, str] = {
    "full-time": "FULLTIME",
    "full time": "FULLTIME",
    "fulltime": "FULLTIME",
    "part-time": "PARTTIME",
    "part time": "PARTTIME",
    "parttime": "PARTTIME",
    "contract": "CONTRACT",
    "contractor": "CONTRACT",
    "freelance": "CONTRACT",
    "intern": "INTERNSHIP",
    "internship": "INTERNSHIP",
    "temporary": "TEMPORARY",
    "temp": "TEMPORARY",
}


def _detect_seniority(title: str) -> int | None:
    """Detect seniority level from job title. Returns None if undetectable."""
    title_lower = f" {title.lower()} "  # pad for word boundary matching
    detected: int | None = None
    for keyword, level, word_boundary in _SENIORITY_KEYWORDS:
        if word_boundary:
            # Check as whole word using word boundaries
            if re.search(rf"\b{re.escape(keyword)}\b", title_lower):
                if detected is None or level > detected:
                    detected = level
        else:
            if keyword in title_lower:
                if detected is None or level > detected:
                    detected = level
    return detected


def _normalize_employment_type(raw: str) -> str:
    """Normalize employment type string to canonical form."""
    raw_lower = raw.lower().strip()
    return _EMPLOYMENT_ALIASES.get(raw_lower, raw.upper())


def _location_matches(job_location: str | None, user_locations: list[str]) -> bool:
    """Check if job location is compatible with user's preferred locations.

    Returns True if:
    - Job has no location specified
    - Job is remote/anywhere
    - Job location overlaps with any user location keyword
    """
    if not job_location:
        return True

    loc_lower = job_location.lower()

    # Remote jobs always pass
    remote_keywords = ["remote", "anywhere", "distributed", "work from home"]
    if any(kw in loc_lower for kw in remote_keywords):
        return True

    # If user wants remote, also allow jobs that don't specify remote
    # (we can't be sure they're NOT remote)
    user_lower = [u.lower() for u in user_locations]
    if "remote" in user_lower:
        # User wants remote — remote jobs already passed above.
        # For non-remote jobs, check if any other location matches.
        non_remote = [u for u in user_lower if u != "remote"]
        if not non_remote:
            # User ONLY wants remote, but this job isn't remote → still pass
            # (let the scorer decide, since location info can be unreliable)
            return True
        user_lower = non_remote

    # Check for keyword overlap with user's location preferences
    for user_loc in user_lower:
        # Split into individual words for flexible matching
        # e.g. "United States" matches "New York, United States"
        words = re.split(r"[,\s]+", user_loc)
        # Match if any significant word (>2 chars) appears in job location
        for word in words:
            if len(word) > 2 and word in loc_lower:
                return True

    return False


class JobPreFilter:
    """Removes obviously irrelevant jobs before expensive embedding/scoring."""

    def __init__(self, user_config: UserConfig) -> None:
        self._config = user_config

    def filter(
        self,
        jobs: list[JobPosting],
        target_title: str | None = None,
    ) -> list[JobPosting]:
        """Apply all pre-filters and return surviving jobs.

        Args:
            jobs: Raw job postings to filter.
            target_title: The job title the user is searching for (unused currently).

        Returns:
            Filtered list of jobs that pass all heuristic checks.
        """
        initial_count = len(jobs)
        seniority_dropped = 0
        location_dropped = 0
        employment_dropped = 0

        result: list[JobPosting] = []
        for job in jobs:
            # Seniority filter
            if not self._passes_seniority(job.title):
                seniority_dropped += 1
                continue

            # Location filter
            if self._config.locations and not _location_matches(
                job.location, self._config.locations
            ):
                location_dropped += 1
                continue

            # Employment type filter
            if not self._passes_employment_type(job.employment_type):
                employment_dropped += 1
                continue

            result.append(job)

        dropped = initial_count - len(result)
        if dropped > 0:
            logger.info(
                f"Pre-filtered: {initial_count} → {len(result)} "
                f"(dropped {seniority_dropped} seniority, "
                f"{location_dropped} location, "
                f"{employment_dropped} employment type)"
            )
        else:
            logger.info(
                f"Pre-filter: all {initial_count} jobs passed"
            )

        return result

    def _passes_seniority(self, title: str) -> bool:
        """Check if job title seniority matches user's experience level."""
        level = _detect_seniority(title)
        if level is None:
            # Can't detect seniority → let it pass
            return True

        exp = self._config.experience_level
        min_level, max_level = _LEVEL_RANGES.get(exp, (0, 8))
        return min_level <= level <= max_level

    def _passes_employment_type(self, job_type: str | None) -> bool:
        """Check if job employment type matches user's preferences."""
        if not self._config.employment_types:
            return True
        if not job_type:
            # Unknown type → let it pass
            return True

        normalized = _normalize_employment_type(job_type)
        return normalized in self._config.employment_types
