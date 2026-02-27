"""LangGraph state schema for the browser agent."""

from typing import Literal, TypedDict


# Valid status transitions: pending → in_progress → paused → submitted/failed/aborted
AgentStatus = Literal[
    "pending",
    "in_progress",
    "navigating",
    "filling",
    "paused",       # waiting for human review
    "submitting",
    "submitted",
    "failed",
    "aborted",
]

# ATS platforms we can detect and handle
ATSPlatform = Literal[
    "greenhouse",
    "lever",
    "workday",
    "generic",
    "unknown",
]

# Human review actions
ReviewAction = Literal["approve", "reject", "edit"]

# Valid status values as a set for validation
VALID_STATUSES: set[str] = {
    "pending", "in_progress", "navigating", "filling",
    "paused", "submitting", "submitted", "failed", "aborted",
}

VALID_ATS_PLATFORMS: set[str] = {
    "greenhouse", "lever", "workday", "generic", "unknown",
}


class ApplicationState(TypedDict, total=False):
    """State flowing through the LangGraph agent.

    Required fields have no default; optional fields use total=False.
    """

    # --- Job context (set at start) ---
    job_id: int
    apply_url: str
    job_title: str
    company: str

    # --- ATS detection ---
    ats_platform: ATSPlatform

    # --- Agent progress ---
    status: AgentStatus
    current_step: str
    error_message: str

    # --- Form filling ---
    fields_filled: dict[str, str]
    fields_to_fill: dict[str, str]
    screenshot_b64: str

    # --- Resume & profile ---
    resume_path: str
    resume_text: str
    user_profile: dict[str, str]

    # --- Human-in-the-loop ---
    review_decision: ReviewAction
    review_edits: dict[str, str]

    # --- Screening questions ---
    screening_questions: list[dict[str, str]]
    screening_answers: dict[str, str]


def validate_status(status: str) -> bool:
    """Check if a status value is valid."""
    return status in VALID_STATUSES


def validate_ats_platform(platform: str) -> bool:
    """Check if an ATS platform value is valid."""
    return platform in VALID_ATS_PLATFORMS


def make_initial_state(
    job_id: int,
    apply_url: str,
    job_title: str = "",
    company: str = "",
    user_profile: dict[str, str] | None = None,
    resume_text: str = "",
) -> ApplicationState:
    """Create a valid initial state for the agent graph."""
    state: ApplicationState = {
        "job_id": job_id,
        "apply_url": apply_url,
        "job_title": job_title,
        "company": company,
        "status": "pending",
        "current_step": "start",
        "ats_platform": "unknown",
        "fields_filled": {},
        "fields_to_fill": {},
        "user_profile": user_profile or {},
        "resume_text": resume_text,
        "screening_questions": [],
        "screening_answers": {},
    }
    return state
