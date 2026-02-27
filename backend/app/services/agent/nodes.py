"""LangGraph node functions for the browser agent.

Each function takes and returns ApplicationState. Side effects (browser actions,
API calls) are handled here; the graph module handles routing logic.
"""

import logging

from browser_use import Agent, Browser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import interrupt

from app.services.agent.ats.greenhouse import GreenhouseSubmitter
from app.services.agent.ats.lever import LeverSubmitter
from app.services.agent.field_mapper import FieldMapper
from app.services.agent.state import ApplicationState
from app.services.llm_factory import LLMTask, get_llm

logger = logging.getLogger(__name__)

# URL patterns for ATS detection
ATS_PATTERNS: dict[str, list[str]] = {
    "greenhouse": ["boards.greenhouse.io", "grnh.se"],
    "lever": ["jobs.lever.co", "lever.co/"],
    "workday": [".myworkdayjobs.com", "workday.com/"],
}

SCREENING_ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are helping a job applicant answer screening questions. "
        "Be concise, professional, and honest. Use the resume context "
        "to craft relevant answers. Keep answers under 200 words each.",
    ),
    (
        "human",
        "Job: {job_title} at {company}\n\n"
        "Resume:\n{resume_text}\n\n"
        "Question: {question}\n\n"
        "Provide a clear, professional answer.",
    ),
])


def detect_ats(state: ApplicationState) -> dict:
    """Detect which ATS platform the apply URL belongs to.

    Examines the URL to determine if it matches known ATS patterns.
    Falls back to "generic" if no pattern matches.
    """
    url = state.get("apply_url", "").lower()

    for platform, patterns in ATS_PATTERNS.items():
        for pattern in patterns:
            if pattern in url:
                logger.info(f"Detected ATS platform: {platform} for URL: {url}")
                return {
                    "ats_platform": platform,
                    "status": "in_progress",
                    "current_step": "detect_ats",
                }

    logger.info(f"No known ATS detected for URL: {url}, using generic")
    return {
        "ats_platform": "generic",
        "status": "in_progress",
        "current_step": "detect_ats",
    }


async def navigate_to_form(state: ApplicationState) -> dict:
    """Navigate the browser to the application form URL.

    Uses browser-use Agent to load the page and detect form elements.
    """
    url = state.get("apply_url", "")
    logger.info(f"Navigating to form: {url}")

    browser = Browser()
    try:
        agent = Agent(
            task=f"Navigate to {url} and wait for the page to fully load. "
            "Identify any job application form on the page.",
            llm=get_llm(LLMTask.BROWSER_AGENT),
            browser=browser,
        )
        await agent.run()
    finally:
        await browser.close()

    return {
        "status": "navigating",
        "current_step": "navigate",
    }


async def fill_form_fields(state: ApplicationState) -> dict:
    """Fill form fields using the user profile data.

    Maps user profile fields to form inputs and uses browser-use to fill them.
    """
    user_profile = state.get("user_profile", {})
    mapper = FieldMapper(user_profile)

    fields_to_fill = state.get("fields_to_fill", {})

    # Map known profile fields
    filled: dict[str, str] = {}
    for field_name in fields_to_fill:
        value = mapper.get_field_value(field_name)
        if value is not None:
            filled[field_name] = value

    # Also include any standard fields we can auto-fill
    standard_fields = mapper.get_all_mappable_fields()
    for key, value in standard_fields.items():
        if key not in filled:
            filled[key] = value

    logger.info(f"Filling {len(filled)} form fields")

    # Use browser-use to fill the form
    fields_description = "\n".join(f"- {k}: {v}" for k, v in filled.items())
    browser = Browser()
    try:
        agent = Agent(
            task=(
                "Fill in the job application form with the following values:\n"
                f"{fields_description}\n\n"
                "For each field, find the matching input and type or select the value."
            ),
            llm=get_llm(LLMTask.BROWSER_AGENT),
            browser=browser,
        )
        await agent.run()
    finally:
        await browser.close()

    return {
        "fields_filled": filled,
        "status": "filling",
        "current_step": "fill_fields",
    }


async def upload_resume(state: ApplicationState) -> dict:
    """Upload the resume file to the application form.

    Uses browser-use to find the file input and upload via Playwright.
    """
    resume_path = state.get("resume_path", "")
    logger.info(f"Uploading resume: {resume_path}")

    if resume_path:
        browser = Browser()
        try:
            agent = Agent(
                task=(
                    f"Find the file upload input for resume/CV on this page and "
                    f"upload the file located at: {resume_path}"
                ),
                llm=get_llm(LLMTask.BROWSER_AGENT),
                browser=browser,
            )
            await agent.run()
        finally:
            await browser.close()

    return {
        "current_step": "upload_resume",
    }


async def answer_questions(state: ApplicationState) -> dict:
    """Answer screening questions using Claude LLM.

    Uses Claude to generate answers to custom screening questions
    based on the user's resume and job context.
    """
    questions = state.get("screening_questions", [])

    if not questions:
        return {"current_step": "answer_questions", "screening_answers": {}}

    llm = get_llm(LLMTask.SCORE)
    resume_text = state.get("resume_text", "")
    job_title = state.get("job_title", "")
    company = state.get("company", "")

    answers: dict[str, str] = {}
    for q in questions:
        question_text = q.get("question", "")
        if not question_text:
            continue

        try:
            chain = SCREENING_ANSWER_PROMPT | llm
            result = await chain.ainvoke({
                "job_title": job_title,
                "company": company,
                "resume_text": resume_text,
                "question": question_text,
            })
            answers[question_text] = result.content
        except Exception as e:
            logger.error(f"Failed to answer question '{question_text}': {e}")
            answers[question_text] = ""

    logger.info(f"Answered {len(answers)} screening questions")

    return {
        "screening_answers": answers,
        "current_step": "answer_questions",
    }


def review_node(state: ApplicationState) -> dict:
    """Pause for human review before submission.

    Uses LangGraph's interrupt() to pause execution and wait for
    human approval. The dashboard shows the filled fields and screenshot
    for the user to review.
    """
    fields_filled = state.get("fields_filled", {})
    screenshot = state.get("screenshot_b64", "")

    logger.info("Pausing for human review")

    review = interrupt({
        "type": "review_request",
        "fields_filled": fields_filled,
        "screenshot_b64": screenshot,
        "message": "Please review the filled application before submission.",
    })

    action = review.get("action", "reject")
    edits = review.get("edits", {})

    return {
        "review_decision": action,
        "review_edits": edits,
        "status": "paused",
        "current_step": "review",
    }


async def submit_application(state: ApplicationState) -> dict:
    """Submit the application form.

    Uses browser-use to click the submit button.
    """
    logger.info("Submitting application")

    browser = Browser()
    try:
        agent = Agent(
            task="Click the submit button on this job application form to submit the application.",
            llm=get_llm(LLMTask.BROWSER_AGENT),
            browser=browser,
        )
        await agent.run()
    finally:
        await browser.close()

    return {
        "status": "submitted",
        "current_step": "submit",
    }


def abort_application(state: ApplicationState) -> dict:
    """Abort the application process.

    Called when the user rejects the application during review.
    """
    logger.info("Application aborted by user")

    return {
        "status": "aborted",
        "current_step": "abort",
    }


async def api_submit(state: ApplicationState) -> dict:
    """Submit via direct API for supported ATS platforms.

    Bypasses browser for Greenhouse/Lever where we have API access.
    """
    platform = state.get("ats_platform", "unknown")
    fields_filled = state.get("fields_filled", {})
    resume_path = state.get("resume_path", "")
    apply_url = state.get("apply_url", "")

    logger.info(f"API submission for platform: {platform}")

    if platform == "greenhouse":
        # Extract board_token and job_id from URL
        # e.g. https://boards.greenhouse.io/{board_token}/jobs/{job_id}
        parts = apply_url.rstrip("/").split("/")
        board_token = ""
        gh_job_id = ""
        if "boards.greenhouse.io" in apply_url:
            try:
                idx = parts.index("boards.greenhouse.io")
                board_token = parts[idx + 1] if len(parts) > idx + 1 else ""
                jobs_idx = parts.index("jobs") if "jobs" in parts else -1
                gh_job_id = (
                    parts[jobs_idx + 1]
                    if jobs_idx >= 0 and len(parts) > jobs_idx + 1
                    else ""
                )
            except (ValueError, IndexError):
                pass

        submitter = GreenhouseSubmitter()
        result = await submitter.submit(board_token, gh_job_id, fields_filled, resume_path or None)
        return {
            "status": "submitted" if result.success else "failed",
            "error_message": "" if result.success else result.message,
            "current_step": "api_submit",
        }

    elif platform == "lever":
        # Extract company and posting_id from URL
        # e.g. https://jobs.lever.co/{company}/{posting_id}
        company_slug = ""
        posting_id = ""
        if "jobs.lever.co" in apply_url:
            try:
                parts = apply_url.rstrip("/").split("/")
                idx = parts.index("jobs.lever.co")
                company_slug = parts[idx + 1] if len(parts) > idx + 1 else ""
                posting_id = parts[idx + 2] if len(parts) > idx + 2 else ""
            except (ValueError, IndexError):
                pass

        submitter = LeverSubmitter()
        result = await submitter.submit(
            company_slug, posting_id, fields_filled, resume_path or None,
        )
        return {
            "status": "submitted" if result.success else "failed",
            "error_message": "" if result.success else result.message,
            "current_step": "api_submit",
        }

    return {
        "status": "failed",
        "error_message": f"Unsupported ATS platform for API submit: {platform}",
        "current_step": "api_submit",
    }
