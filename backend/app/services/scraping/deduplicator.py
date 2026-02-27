"""Job posting deduplication using composite keys.

Deduplication strategy:
- Normalize company names (strip suffixes, lowercase, collapse whitespace)
- Composite key: (normalized_company, normalized_title, normalized_location)
- First-seen wins — duplicates from later sources are dropped
"""

import re

from app.schemas.matching import JobPosting

# Common company suffixes to strip for comparison
_COMPANY_SUFFIXES = re.compile(
    r"\s*,?\s*\b(inc|incorporated|llc|ltd|limited|corp|corporation|co|company|"
    r"group|holdings|international|plc|gmbh|ag|sa|srl|pty)\b\.?\s*$",
    re.IGNORECASE,
)


def normalize_company(name: str) -> str:
    """Normalize a company name for deduplication.

    Strips common suffixes (Inc, LLC, Ltd, etc.), lowercases,
    and collapses whitespace.
    """
    name = name.strip()
    name = _COMPANY_SUFFIXES.sub("", name)
    name = re.sub(r"\s+", " ", name).strip().lower()
    return name


def normalize_title(title: str) -> str:
    """Normalize a job title for deduplication."""
    return re.sub(r"\s+", " ", title).strip().lower()


def normalize_location(location: str | None) -> str:
    """Normalize a location for deduplication."""
    if not location:
        return ""
    return re.sub(r"\s+", " ", location).strip().lower()


def make_dedup_key(job: JobPosting) -> str:
    """Create a composite deduplication key for a job posting."""
    company = normalize_company(job.company)
    title = normalize_title(job.title)
    location = normalize_location(job.location)
    return f"{company}|{title}|{location}"


class JobDeduplicator:
    """Deduplicates job postings across multiple scraping sources."""

    def __init__(self) -> None:
        self._seen_keys: set[str] = set()

    def deduplicate(self, jobs: list[JobPosting]) -> list[JobPosting]:
        """Remove duplicate job postings from a list.

        First-seen wins — later duplicates are dropped.

        Args:
            jobs: List of job postings (potentially from multiple sources).

        Returns:
            Deduplicated list preserving original order.
        """
        unique: list[JobPosting] = []

        for job in jobs:
            key = make_dedup_key(job)
            if key not in self._seen_keys:
                self._seen_keys.add(key)
                unique.append(job)

        return unique

    @property
    def seen_count(self) -> int:
        """Number of unique keys seen so far."""
        return len(self._seen_keys)

    def reset(self) -> None:
        """Clear seen keys for a fresh deduplication pass."""
        self._seen_keys.clear()
