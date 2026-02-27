"""Tests for job deduplication."""


from app.schemas.matching import JobPosting
from app.services.scraping.deduplicator import (
    JobDeduplicator,
    normalize_company,
    normalize_location,
    normalize_title,
)


def _make_job(
    title: str = "Software Engineer",
    company: str = "TestCo",
    location: str | None = "Remote",
    source: str = "test",
    external_id: str = "j1",
) -> JobPosting:
    return JobPosting(
        external_id=external_id,
        source=source,
        title=title,
        company=company,
        location=location,
        description=f"{title} at {company}",
    )


class TestNormalization:
    """Tests for normalization functions."""

    def test_company_lowercase(self):
        assert normalize_company("Google") == "google"

    def test_company_strip_inc(self):
        assert normalize_company("Google Inc.") == "google"

    def test_company_strip_llc(self):
        assert normalize_company("Acme LLC") == "acme"

    def test_company_strip_ltd(self):
        assert normalize_company("DeepMind Ltd") == "deepmind"

    def test_company_strip_corp(self):
        assert normalize_company("IBM Corp") == "ibm"

    def test_company_whitespace(self):
        assert normalize_company("  Google   Inc  ") == "google"

    def test_title_lowercase(self):
        assert normalize_title("Software Engineer") == "software engineer"

    def test_title_whitespace(self):
        assert normalize_title("  Senior   Backend   Engineer  ") == "senior backend engineer"

    def test_location_lowercase(self):
        assert normalize_location("San Francisco, CA") == "san francisco, ca"

    def test_location_none(self):
        assert normalize_location(None) == ""


class TestJobDeduplicator:
    """Tests for the JobDeduplicator class."""

    def test_exact_duplicate_detected(self):
        dedup = JobDeduplicator()
        jobs = [
            _make_job("Engineer", "Google", "Remote", "source1", "j1"),
            _make_job("Engineer", "Google", "Remote", "source2", "j2"),
        ]
        result = dedup.deduplicate(jobs)
        assert len(result) == 1
        assert result[0].external_id == "j1"  # First wins

    def test_case_insensitive_dedup(self):
        dedup = JobDeduplicator()
        jobs = [
            _make_job("Software Engineer", "Google", "Remote"),
            _make_job("software engineer", "google", "remote"),
        ]
        result = dedup.deduplicate(jobs)
        assert len(result) == 1

    def test_suffix_stripping(self):
        dedup = JobDeduplicator()
        jobs = [
            _make_job("Engineer", "Google Inc.", "NYC"),
            _make_job("Engineer", "Google", "NYC"),
        ]
        result = dedup.deduplicate(jobs)
        assert len(result) == 1

    def test_different_location_not_duplicate(self):
        dedup = JobDeduplicator()
        jobs = [
            _make_job("Engineer", "Google", "New York", "s1", "j1"),
            _make_job("Engineer", "Google", "San Francisco", "s2", "j2"),
        ]
        result = dedup.deduplicate(jobs)
        assert len(result) == 2

    def test_different_title_not_duplicate(self):
        dedup = JobDeduplicator()
        jobs = [
            _make_job("Frontend Engineer", "Google", "Remote"),
            _make_job("Backend Engineer", "Google", "Remote"),
        ]
        result = dedup.deduplicate(jobs)
        assert len(result) == 2

    def test_whitespace_normalization(self):
        dedup = JobDeduplicator()
        jobs = [
            _make_job("Software  Engineer", "Google", "  Remote  "),
            _make_job("Software Engineer", "Google", "Remote"),
        ]
        result = dedup.deduplicate(jobs)
        assert len(result) == 1

    def test_seen_count(self):
        dedup = JobDeduplicator()
        jobs = [
            _make_job("E1", "C1", "L1", external_id="1"),
            _make_job("E2", "C2", "L2", external_id="2"),
            _make_job("E1", "C1", "L1", external_id="3"),  # dup
        ]
        dedup.deduplicate(jobs)
        assert dedup.seen_count == 2

    def test_reset_clears_state(self):
        dedup = JobDeduplicator()
        dedup.deduplicate([_make_job()])
        assert dedup.seen_count == 1
        dedup.reset()
        assert dedup.seen_count == 0

    def test_empty_input(self):
        dedup = JobDeduplicator()
        result = dedup.deduplicate([])
        assert result == []
