"""Tests for the JobPreFilter module."""

from app.config import UserConfig
from app.schemas.matching import JobPosting
from app.services.matching.pre_filter import JobPreFilter, _detect_seniority, _location_matches


def _make_job(
    title: str = "Software Engineer",
    location: str | None = None,
    employment_type: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
) -> JobPosting:
    return JobPosting(
        external_id="test-001",
        source="test",
        title=title,
        company="TestCo",
        description="A test job posting.",
        location=location,
        employment_type=employment_type,
        salary_min=salary_min,
        salary_max=salary_max,
    )


class TestDetectSeniority:
    """Tests for seniority detection from titles."""

    def test_detects_senior(self):
        assert _detect_seniority("Senior Software Engineer") == 3

    def test_detects_junior(self):
        assert _detect_seniority("Junior Developer") == 1

    def test_detects_staff(self):
        assert _detect_seniority("Staff Engineer") == 4

    def test_detects_principal(self):
        assert _detect_seniority("Principal Engineer") == 5

    def test_detects_director(self):
        assert _detect_seniority("Director of Engineering") == 6

    def test_detects_vp(self):
        assert _detect_seniority("VP of Engineering") == 7

    def test_detects_intern(self):
        assert _detect_seniority("Software Engineering Intern") == 0

    def test_returns_none_for_plain_title(self):
        assert _detect_seniority("Software Engineer") is None

    def test_returns_highest_when_multiple(self):
        # "Senior Staff Engineer" has both senior(3) and staff(4)
        assert _detect_seniority("Senior Staff Engineer") == 4


class TestLocationMatches:
    """Tests for location matching logic."""

    def test_no_location_always_passes(self):
        assert _location_matches(None, ["United States"]) is True

    def test_remote_always_passes(self):
        assert _location_matches("Remote", ["Germany"]) is True
        assert _location_matches("Remote - US", ["Germany"]) is True
        assert _location_matches("Anywhere", ["Germany"]) is True

    def test_matching_country(self):
        assert _location_matches("New York, United States", ["United States"]) is True

    def test_no_match_different_country(self):
        assert _location_matches("Berlin, Germany", ["United States", "Canada"]) is False

    def test_user_wants_only_remote(self):
        # User only wants remote — non-remote jobs still pass (location info unreliable)
        assert _location_matches("Berlin, Germany", ["Remote"]) is True

    def test_user_wants_remote_plus_country(self):
        # Remote jobs pass, and country-matching jobs pass
        assert _location_matches("Remote", ["Remote", "United States"]) is True
        assert _location_matches("San Francisco, United States", ["Remote", "United States"]) is True
        assert _location_matches("Berlin, Germany", ["Remote", "United States"]) is False


class TestJobPreFilter:
    """Tests for the full JobPreFilter."""

    def test_filters_senior_roles_for_entry_user(self):
        config = UserConfig(experience_level="entry")
        pf = JobPreFilter(config)
        jobs = [
            _make_job("Junior Developer"),
            _make_job("Senior Staff Engineer"),
            _make_job("Principal Architect"),
            _make_job("Software Engineer"),  # no seniority detected → passes
        ]
        result = pf.filter(jobs)
        titles = [j.title for j in result]
        assert "Junior Developer" in titles
        assert "Software Engineer" in titles
        assert "Senior Staff Engineer" not in titles
        assert "Principal Architect" not in titles

    def test_keeps_mid_roles_for_mid_user(self):
        config = UserConfig(experience_level="mid")
        pf = JobPreFilter(config)
        jobs = [
            _make_job("Junior Developer"),
            _make_job("Software Engineer"),
            _make_job("Senior Software Engineer"),
            _make_job("Staff Engineer"),
            _make_job("Director of Engineering"),
        ]
        result = pf.filter(jobs)
        titles = [j.title for j in result]
        assert "Junior Developer" in titles
        assert "Software Engineer" in titles
        assert "Senior Software Engineer" in titles
        assert "Staff Engineer" not in titles
        assert "Director of Engineering" not in titles

    def test_filters_wrong_country(self):
        config = UserConfig(locations=["United States", "Canada"])
        pf = JobPreFilter(config)
        jobs = [
            _make_job(location="New York, United States"),
            _make_job(location="Berlin, Germany"),
            _make_job(location="London, England"),
            _make_job(location="Toronto, Canada"),
        ]
        result = pf.filter(jobs)
        locations = [j.location for j in result]
        assert "New York, United States" in locations
        assert "Toronto, Canada" in locations
        assert "Berlin, Germany" not in locations
        assert "London, England" not in locations

    def test_keeps_remote_jobs_always(self):
        config = UserConfig(locations=["United States"])
        pf = JobPreFilter(config)
        jobs = [
            _make_job(location="Remote"),
            _make_job(location="Remote - US"),
            _make_job(location="Anywhere"),
            _make_job(location="Berlin, Germany"),
        ]
        result = pf.filter(jobs)
        assert len(result) == 3  # All remote pass, Germany dropped

    def test_keeps_jobs_with_no_location(self):
        config = UserConfig(locations=["United States"])
        pf = JobPreFilter(config)
        jobs = [
            _make_job(location=None),
            _make_job(location=""),
        ]
        result = pf.filter(jobs)
        assert len(result) == 2

    def test_filters_mismatched_employment_type(self):
        config = UserConfig(employment_types=["FULLTIME"])
        pf = JobPreFilter(config)
        jobs = [
            _make_job(employment_type="Full-time"),
            _make_job(employment_type="Part-time"),
            _make_job(employment_type="Contract"),
            _make_job(employment_type=None),  # Unknown → passes
        ]
        result = pf.filter(jobs)
        assert len(result) == 2
        types = [j.employment_type for j in result]
        assert "Full-time" in types
        assert None in types

    def test_no_filter_when_no_config_restrictions(self):
        config = UserConfig(
            experience_level="mid",
            locations=[],
            employment_types=[],
        )
        pf = JobPreFilter(config)
        jobs = [
            _make_job("VP of Engineering", "Berlin, Germany", "Contract"),
        ]
        # VP is level 7, mid range is 1-3, so seniority filter still applies
        result = pf.filter(jobs)
        assert len(result) == 0

    def test_all_filters_combined(self):
        config = UserConfig(
            experience_level="mid",
            locations=["United States"],
            employment_types=["FULLTIME"],
        )
        pf = JobPreFilter(config)
        jobs = [
            # Passes all
            _make_job("Software Engineer", "Remote", "Full-time"),
            # Fails seniority (VP)
            _make_job("VP of Engineering", "Remote", "Full-time"),
            # Fails location
            _make_job("Software Engineer", "Berlin, Germany", "Full-time"),
            # Fails employment type
            _make_job("Software Engineer", "Remote", "Contract"),
            # Passes (unknown seniority, remote, unknown type)
            _make_job("Software Engineer", "Remote", None),
        ]
        result = pf.filter(jobs)
        assert len(result) == 2


class TestSalaryFilter:
    """Tests for salary range pre-filtering."""

    def test_no_user_salary_passes_all(self):
        config = UserConfig(salary_min=None, salary_max=None)
        pf = JobPreFilter(config)
        jobs = [_make_job(salary_min=50000, salary_max=80000)]
        assert len(pf.filter(jobs)) == 1

    def test_no_job_salary_passes(self):
        config = UserConfig(salary_min=100000, salary_max=200000)
        pf = JobPreFilter(config)
        jobs = [_make_job(salary_min=None, salary_max=None)]
        assert len(pf.filter(jobs)) == 1

    def test_job_pays_too_little(self):
        config = UserConfig(salary_min=150000, salary_max=250000)
        pf = JobPreFilter(config)
        jobs = [_make_job(salary_min=50000, salary_max=80000)]
        assert len(pf.filter(jobs)) == 0

    def test_job_pays_too_much(self):
        config = UserConfig(salary_min=50000, salary_max=80000)
        pf = JobPreFilter(config)
        jobs = [_make_job(salary_min=200000, salary_max=300000)]
        assert len(pf.filter(jobs)) == 0

    def test_overlapping_ranges_pass(self):
        config = UserConfig(salary_min=100000, salary_max=200000)
        pf = JobPreFilter(config)
        jobs = [_make_job(salary_min=150000, salary_max=250000)]
        assert len(pf.filter(jobs)) == 1

    def test_user_min_only(self):
        config = UserConfig(salary_min=100000, salary_max=None)
        pf = JobPreFilter(config)
        jobs = [
            _make_job(salary_min=50000, salary_max=80000),   # pays too little
            _make_job(salary_min=120000, salary_max=180000),  # overlaps
        ]
        result = pf.filter(jobs)
        assert len(result) == 1

    def test_user_max_only(self):
        config = UserConfig(salary_min=None, salary_max=100000)
        pf = JobPreFilter(config)
        jobs = [
            _make_job(salary_min=50000, salary_max=80000),   # fits
            _make_job(salary_min=150000, salary_max=200000),  # too much
        ]
        result = pf.filter(jobs)
        assert len(result) == 1

    def test_exact_boundary_passes(self):
        config = UserConfig(salary_min=100000, salary_max=200000)
        pf = JobPreFilter(config)
        # Job max exactly equals user min — passes
        jobs = [_make_job(salary_min=80000, salary_max=100000)]
        assert len(pf.filter(jobs)) == 1


class TestLocationExclusion:
    """Tests for location exclusion pre-filtering."""

    def test_no_exclusions_passes_all(self):
        config = UserConfig(excluded_locations=[])
        pf = JobPreFilter(config)
        jobs = [_make_job(location="Beijing, China")]
        assert len(pf.filter(jobs)) == 1

    def test_excludes_matching_location(self):
        config = UserConfig(excluded_locations=["China", "India"])
        pf = JobPreFilter(config)
        jobs = [
            _make_job(location="Beijing, China"),
            _make_job(location="Mumbai, India"),
            _make_job(location="Remote"),
        ]
        result = pf.filter(jobs)
        assert len(result) == 1
        assert result[0].location == "Remote"

    def test_case_insensitive(self):
        config = UserConfig(excluded_locations=["china"])
        pf = JobPreFilter(config)
        jobs = [_make_job(location="Beijing, CHINA")]
        assert len(pf.filter(jobs)) == 0

    def test_no_location_passes(self):
        config = UserConfig(excluded_locations=["China"])
        pf = JobPreFilter(config)
        jobs = [_make_job(location=None)]
        assert len(pf.filter(jobs)) == 1

    def test_partial_match_excludes(self):
        config = UserConfig(excluded_locations=["India"])
        pf = JobPreFilter(config)
        jobs = [_make_job(location="Bangalore, India - Remote")]
        assert len(pf.filter(jobs)) == 0
