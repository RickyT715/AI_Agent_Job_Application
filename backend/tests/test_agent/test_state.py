"""Tests for agent state schema and validation."""


from app.services.agent.state import (
    make_initial_state,
    validate_ats_platform,
    validate_status,
)


class TestStateValidation:
    """Tests for state validation functions."""

    def test_valid_statuses(self):
        """All expected status values are valid."""
        for status in ["pending", "in_progress", "navigating", "filling",
                       "paused", "submitting", "submitted", "failed", "aborted"]:
            assert validate_status(status) is True

    def test_invalid_status_rejected(self):
        """Unknown status values are rejected."""
        assert validate_status("unknown_status") is False
        assert validate_status("") is False
        assert validate_status("PENDING") is False  # case-sensitive

    def test_valid_ats_platforms(self):
        """All expected ATS platforms are valid."""
        for platform in ["greenhouse", "lever", "workday", "generic", "unknown"]:
            assert validate_ats_platform(platform) is True

    def test_invalid_ats_platform_rejected(self):
        """Unknown ATS platforms are rejected."""
        assert validate_ats_platform("indeed") is False
        assert validate_ats_platform("") is False


class TestMakeInitialState:
    """Tests for make_initial_state factory."""

    def test_initial_state_has_required_fields(self):
        state = make_initial_state(job_id=1, apply_url="https://example.com/apply")
        assert state["job_id"] == 1
        assert state["apply_url"] == "https://example.com/apply"
        assert state["status"] == "pending"
        assert state["ats_platform"] == "unknown"

    def test_initial_state_has_empty_collections(self):
        state = make_initial_state(job_id=1, apply_url="https://example.com")
        assert state["fields_filled"] == {}
        assert state["fields_to_fill"] == {}
        assert state["screening_questions"] == []
        assert state["screening_answers"] == {}

    def test_initial_state_with_user_profile(self):
        profile = {"first_name": "Alice", "email": "alice@test.com"}
        state = make_initial_state(
            job_id=1, apply_url="https://example.com",
            user_profile=profile,
        )
        assert state["user_profile"] == profile

    def test_initial_state_with_resume(self):
        state = make_initial_state(
            job_id=1, apply_url="https://example.com",
            resume_text="My resume",
        )
        assert state["resume_text"] == "My resume"

    def test_initial_state_without_optional_fields(self):
        """Optional fields get defaults."""
        state = make_initial_state(job_id=1, apply_url="https://example.com")
        assert state["job_title"] == ""
        assert state["company"] == ""
        assert state["user_profile"] == {}
        assert state["resume_text"] == ""
