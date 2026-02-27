"""MCP server definition using FastMCP.

Exposes job application agent capabilities as MCP tools, resources, and prompts.
Supports stdio transport (local) and Streamable HTTP (remote).
"""

import logging

from fastmcp import FastMCP

from app.config import UserConfig, get_settings, load_user_config

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="Job Application Agent",
    instructions=(
        "An AI-powered job application agent. Use these tools to search for jobs, "
        "match them against a resume, generate cover letters and reports, "
        "and fill out job applications."
    ),
)

# ---------------------------------------------------------------------------
# Helper: load resume text
# ---------------------------------------------------------------------------

def _load_resume_text() -> str:
    """Load the current resume text from the configured path."""
    settings = get_settings()
    user_config = load_user_config(settings.user_config_path)

    if user_config.resume_path and user_config.resume_path.exists():
        return user_config.resume_path.read_text(encoding="utf-8")

    # Fall back to data/resume.txt
    resume_path = settings.data_dir / "resume.txt"
    if resume_path.exists():
        return resume_path.read_text(encoding="utf-8")

    return ""


def _load_user_config() -> UserConfig:
    """Load the current user config."""
    settings = get_settings()
    return load_user_config(settings.user_config_path)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_jobs(
    query: str,
    location: str = "Remote",
    limit: int = 10,
) -> dict:
    """Search for job postings matching a query.

    Args:
        query: Job search query (e.g., "Python Developer", "ML Engineer").
        location: Location filter (e.g., "Remote", "San Francisco").
        limit: Maximum number of results to return.

    Returns:
        Dictionary with jobs list and metadata.
    """
    from app.services.scraping.api.jsearch import JSearchScraper
    from app.services.scraping.deduplicator import JobDeduplicator
    from app.services.scraping.orchestrator import ScrapingOrchestrator

    scraper = JSearchScraper()
    orchestrator = ScrapingOrchestrator(
        scrapers=[scraper],
        deduplicator=JobDeduplicator(),
    )

    result = await orchestrator.run(query, location=location)

    jobs = [
        {
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "description": j.description[:500] if j.description else "",
            "apply_url": j.apply_url,
            "source": j.source,
        }
        for j in result.jobs[:limit]
    ]

    return {
        "total_found": result.total,
        "unique": result.new,
        "duplicates": result.duplicates,
        "jobs": jobs,
        "errors": result.errors,
    }


@mcp.tool()
async def match_resume_to_jobs(
    query: str = "Software Engineer",
    location: str = "Remote",
    top_k: int = 5,
) -> dict:
    """Search for jobs and score them against the current resume.

    Runs the full pipeline: scrape → embed → retrieve → rerank → score.

    Args:
        query: Job search query.
        location: Location filter.
        top_k: Number of top matches to return.

    Returns:
        Dictionary with scored matches.
    """
    from app.services.matching.pipeline import MatchingPipeline
    from app.services.scraping.api.jsearch import JSearchScraper
    from app.services.scraping.deduplicator import JobDeduplicator
    from app.services.scraping.orchestrator import ScrapingOrchestrator

    resume_text = _load_resume_text()
    if not resume_text:
        return {"error": "No resume found. Upload a resume first."}

    user_config = _load_user_config()

    # Scrape jobs
    scraper = JSearchScraper()
    orchestrator = ScrapingOrchestrator(
        scrapers=[scraper],
        deduplicator=JobDeduplicator(),
    )
    scrape_result = await orchestrator.run(query, location=location)

    if not scrape_result.jobs:
        return {
            "error": "No jobs found for the given query.",
            "scraping_errors": scrape_result.errors,
        }

    # Match
    pipeline = MatchingPipeline(user_config=user_config, final_k=top_k)
    matches = await pipeline.match(resume_text, jobs=scrape_result.jobs)

    return {
        "total_jobs_scraped": scrape_result.new,
        "matches": [
            {
                "job_title": m.job.title,
                "company": m.job.company,
                "location": m.job.location,
                "overall_score": m.score.overall_score,
                "reasoning": m.score.reasoning,
                "strengths": m.score.strengths,
                "missing_skills": m.score.missing_skills,
                "apply_url": m.job.apply_url,
            }
            for m in matches[:top_k]
        ],
    }


@mcp.tool()
async def fill_application(
    apply_url: str,
    dry_run: bool = True,
) -> dict:
    """Fill out a job application form.

    By default, runs in dry_run mode to preview what would be filled
    without actually submitting.

    Args:
        apply_url: URL of the job application form.
        dry_run: If True, preview without submitting. Defaults to True.

    Returns:
        Dictionary with filled fields and status.
    """
    from app.services.agent.field_mapper import FieldMapper
    from app.services.agent.nodes import detect_ats
    from app.services.agent.state import make_initial_state

    _load_user_config()
    resume_text = _load_resume_text()

    state = make_initial_state(
        job_id=0,
        apply_url=apply_url,
        user_profile={
            "resume_text": resume_text,
        },
    )

    # Detect ATS platform
    state = detect_ats(state)

    # Map fields from profile
    mapper = FieldMapper(user_profile=state.get("user_profile", {}))
    common_fields = ["first_name", "last_name", "email", "phone", "linkedin_url"]
    mapped = mapper.map_fields(common_fields)

    result = {
        "apply_url": apply_url,
        "ats_platform": state.get("ats_platform", "unknown"),
        "dry_run": dry_run,
        "fields_preview": mapped,
        "status": "preview" if dry_run else "would_submit",
    }

    if dry_run:
        result["message"] = (
            "Dry run complete. Set dry_run=False to actually submit. "
            "Note: submission requires human approval via the dashboard."
        )
    else:
        result["message"] = (
            "Live submission requires the browser agent. "
            "Start the agent via the dashboard for human-in-the-loop approval."
        )
        result["status"] = "requires_dashboard"

    return result


@mcp.tool()
async def generate_cover_letter(
    job_title: str,
    company: str,
    job_description: str,
) -> dict:
    """Generate a personalized cover letter for a job application.

    Args:
        job_title: Title of the target job.
        company: Company name.
        job_description: Full job description text.

    Returns:
        Dictionary with the generated cover letter text.
    """
    from app.services.reports.cover_letter import CoverLetterGenerator

    resume_text = _load_resume_text()
    if not resume_text:
        return {"error": "No resume found. Upload a resume first."}

    generator = CoverLetterGenerator()
    letter = await generator.generate(
        job_title=job_title,
        company=company,
        job_description=job_description,
        resume_text=resume_text,
        strengths=[],
        missing_skills=[],
    )

    return {
        "cover_letter": letter,
        "job_title": job_title,
        "company": company,
        "word_count": len(letter.split()),
    }


@mcp.tool()
async def generate_report(
    job_title: str,
    company: str,
    overall_score: float,
    breakdown: dict[str, float],
    reasoning: str,
    strengths: list[str],
    missing_skills: list[str],
) -> dict:
    """Generate an HTML match report for a job application.

    Args:
        job_title: Title of the job.
        company: Company name.
        overall_score: Overall match score (0-10).
        breakdown: Score breakdown by category.
        reasoning: Explanation of the scoring.
        strengths: List of matching strengths.
        missing_skills: List of skill gaps.

    Returns:
        Dictionary with the HTML report content and metadata.
    """
    from app.services.reports.generator import ReportGenerator

    generator = ReportGenerator()
    html = generator.render_html(
        job_title=job_title,
        company=company,
        overall_score=overall_score,
        breakdown=breakdown,
        reasoning=reasoning,
        strengths=strengths,
        missing_skills=missing_skills,
    )

    return {
        "html": html,
        "job_title": job_title,
        "company": company,
        "overall_score": overall_score,
        "format": "html",
    }


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("resume://current")
def get_current_resume() -> str:
    """Get the current resume text."""
    text = _load_resume_text()
    return text if text else "No resume uploaded yet."


@mcp.resource("preferences://job-search")
def get_job_search_preferences() -> str:
    """Get the current job search preferences as JSON."""
    config = _load_user_config()
    return config.model_dump_json(indent=2)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@mcp.prompt()
def cover_letter_prompt(job_title: str, company: str) -> str:
    """Generate a prompt for writing a cover letter.

    Args:
        job_title: Target job title.
        company: Target company name.
    """
    resume_text = _load_resume_text()
    return (
        f"Write a cover letter for the position of {job_title} at {company}.\n\n"
        f"Resume:\n{resume_text}\n\n"
        f"Focus on relevant experience and genuine enthusiasm for the role."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def create_mcp_server() -> FastMCP:
    """Return the configured MCP server instance."""
    return mcp
