"""End-to-end pipeline test: Scrape -> Match -> Score -> Report.

Simulates a real user (Ruiqi Tian) searching for:
  1. Software Engineer
  2. AI Engineer
  3. Full-stack Developer

Uses free public APIs (Arbeitnow, Greenhouse, Lever) for scraping
and Claude (via claude-code-proxy at localhost:42069) for scoring.
Outputs a detailed Markdown report with job descriptions.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set up env vars BEFORE importing app modules
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            if val and "your-" not in val.lower() and "here" not in val.lower():
                os.environ.setdefault(key, val)

# Also propagate GEMINI_API_KEY -> GOOGLE_API_KEY if needed
if os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("e2e_test")

# -- Now import app modules --

import chromadb
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import UserConfig, get_settings, reset_settings
from app.schemas.matching import JobPosting, ScoredMatch
from app.services.matching.embedder import JobEmbedder
from app.services.matching.pipeline import MatchingPipeline
from app.services.matching.scorer import JobScorer
from app.services.scraping.api.arbeitnow import ArbeitnowScraper
from app.services.scraping.api.greenhouse import GreenhouseScraper
from app.services.scraping.api.lever import LeverScraper
from app.services.scraping.deduplicator import JobDeduplicator

# -- Configuration --

# Claude proxy URL
CLAUDE_PROXY_URL = "http://localhost:42069"
CLAUDE_MODEL = "claude-sonnet-4-6"

# How many jobs to score per title (target 200+ total across 3 titles)
SCORE_PER_TITLE = 70
MAX_JOBS_PER_TITLE = 200  # Scraping cap per title

# -- User Profile --

RESUME_TEXT = """
Ruiqi Tian
Email: ruiqitian@outlook.com | Mobile: +1-236-989-3086
LinkedIn: https://www.linkedin.com/in/ruiqi-tian-a53159249/
GitHub: https://github.com/RickyT715

EDUCATION
- Master of Engineering in Electrical and Computer Engineering, GPA: 3.9
  University of Waterloo, Waterloo, ON (Sept 2024 - Oct 2025)
  Specialization: Software Engineering, Full-stack Development, Computer Graphics,
  Computer Vision, Reinforcement Learning, LLM, DevOps, Performance Testing

- Bachelor of Applied Science in Computer Engineering, GPA: 3.7
  University of British Columbia, Vancouver, BC (Sept 2020 - May 2024)
  Specialization: Software Engineering, Full-stack Development, Phone App Development,
  Computer Graphics, Computer Vision, Deep Learning, Embedded Development
  Honor: 2022, 2023, 2024 Dean's Honor List

EXPERIENCE
- Software Engineer Intern, Disanji Technology Institute (Jun 2024 - Aug 2024)
  Built production-grade RAG system over 500+ pages Chinese documents.
  Architected end-to-end RAG pipeline using LangChain LCEL with hybrid retrieval
  (BM25 + BGE-M3 dense/sparse vectors in Milvus), FlashRank reranking, and streaming.
  Improved retrieval precision 35% over vector-only baseline.
  Built automated evaluation pipeline using RAGAS achieving 0.84 context recall.
  Deployed via Docker Compose with FastAPI + SSE streaming, Redis semantic caching.

- Research Assistant, Nanjing University (Jun 2023 - Aug 2023)
  Co-developed Dual Branches Video Modeling (DBVM) for multimodal QA on movies.
  Published "Deep Video Understanding with Video-Language Model" in ACM MM '23.

- Software Engineer Intern, GuoLing Technology Institute (Apr 2023 - May 2023)
  Trained 4 face-specific YOLOv8 models for industrial defect detection (91% mAP@50).
  Built end-to-end data pipeline processing 5,000+ images.

PROJECTS
- AI Agent-powered Resume & Cover Letter Generator (Oct 2025 - Feb 2026)
  Architected 4-agent LangGraph pipeline with quality-gated routing.
  Engineered RAG pipeline using ChromaDB and BGE-M3 embeddings.
  Built dual-layer evaluation with ATS keyword scoring and LLM self-critique.
  Full-stack: FastAPI, React/TypeScript, WebSocket, PostgreSQL, Docker, 80%+ test coverage.

- Aerial Drone Footage Lost Hiker Challenge (Sep 2023 - Apr 2024)
  YOLOv8 model with SAHI pipeline for detecting lost hikers in drone footage.
  React frontend for uploading footage and viewing detection results.

SKILLS
Languages: Python, JavaScript, C++, SQL, Java, Verilog, VHDL, HTML, CSS, Lua
Technologies: AWS, Azure, Kafka, React, Vue, Qt, Git, Android Studio
AI/ML: RAG, LLM, LangChain, LangGraph, ChromaDB, Computer Vision, YOLO, Deep Learning
Backend: FastAPI, Node.js, REST APIs, WebSocket, Docker, PostgreSQL, MongoDB, Redis
"""

# Expanded Greenhouse boards for more jobs
GREENHOUSE_BOARDS = [
    # Big tech / well-known
    "figma", "cloudflare", "stripe", "datadog", "airbnb", "databricks",
    "airtable", "gusto", "cockroachlabs", "benchling",
    "relativityspace", "nianticlabs",
    # Additional boards for volume
    "hashicorp", "elastic", "gitlab", "mixpanel",
    "hubspot", "snyk", "brex", "ramp",
]

LEVER_COMPANIES = [
    "netflix", "nerdwallet", "rippling", "samsara",
]

USER_CONFIG = UserConfig(
    job_titles=["Software Engineer", "AI Engineer", "Full-stack Developer"],
    locations=["Remote", "United States", "Canada"],
    salary_min=100000,
    salary_max=200000,
    workplace_types=["remote", "hybrid"],
    experience_level="mid",
    employment_types=["FULLTIME"],
    final_results_count=SCORE_PER_TITLE,
    num_pages_per_source=5,
    enabled_sources=["arbeitnow", "greenhouse", "lever"],
    greenhouse_board_tokens=GREENHOUSE_BOARDS,
    lever_companies=LEVER_COMPANIES,
)

SEARCH_TITLES = [
    "Software Engineer",
    "AI Engineer",
    "Full-stack Developer",
]

# -- Title matching helpers --

_TITLE_VARIANTS: dict[str, list[str]] = {
    "full-stack developer": ["full stack", "fullstack", "full-stack"],
    "full stack developer": ["full stack", "fullstack", "full-stack"],
    "ai engineer": [
        "ai engineer", "ai/ml engineer", "machine learning engineer",
        "ml engineer", "artificial intelligence",
    ],
}


def _is_relevant(job_title: str, title_lower: str) -> bool:
    """Check if a job title matches the search query."""
    jt = job_title.lower()
    if title_lower in jt:
        return True
    normalized_query = title_lower.replace("-", " ").replace("_", " ")
    normalized_jt = jt.replace("-", " ").replace("_", " ")
    if normalized_query in normalized_jt:
        return True
    variants = _TITLE_VARIANTS.get(title_lower, [])
    for variant in variants:
        if variant in normalized_jt:
            return True
    return False


# -- Scraping Phase --


async def scrape_all_sources(title: str) -> list[JobPosting]:
    """Scrape from all free sources for a given job title."""
    all_jobs: list[JobPosting] = []
    title_lower = title.lower()

    # 1. Arbeitnow (free public API)
    logger.info(f"  [Arbeitnow] Scraping for '{title}'...")
    arb = ArbeitnowScraper()
    try:
        arb_result = await arb.scrape(title, num_pages=5)
        all_jobs.extend(arb_result.jobs)
        logger.info(
            f"  [Arbeitnow] Found {len(arb_result.jobs)} jobs "
            f"(scanned {arb_result.total_found})"
        )
    except Exception as e:
        logger.error(f"  [Arbeitnow] Failed: {e}")
    finally:
        await arb.close()

    # 2. Greenhouse (free public API)
    logger.info(f"  [Greenhouse] Scraping {len(GREENHOUSE_BOARDS)} boards...")
    gh = GreenhouseScraper(board_tokens=GREENHOUSE_BOARDS)
    try:
        gh_result = await gh.scrape(title)
        relevant_gh = [j for j in gh_result.jobs if _is_relevant(j.title, title_lower)]
        all_jobs.extend(relevant_gh)
        logger.info(
            f"  [Greenhouse] Found {len(relevant_gh)} relevant / "
            f"{len(gh_result.jobs)} total from {len(GREENHOUSE_BOARDS)} boards"
        )
    except Exception as e:
        logger.error(f"  [Greenhouse] Failed: {e}")
    finally:
        await gh.close()

    # 3. Lever (free public API)
    logger.info(f"  [Lever] Scraping {len(LEVER_COMPANIES)} companies...")
    lever = LeverScraper(companies=LEVER_COMPANIES)
    try:
        lever_result = await lever.scrape(title)
        relevant_lever = [
            j for j in lever_result.jobs if _is_relevant(j.title, title_lower)
        ]
        all_jobs.extend(relevant_lever)
        logger.info(
            f"  [Lever] Found {len(relevant_lever)} relevant / "
            f"{len(lever_result.jobs)} total from {len(LEVER_COMPANIES)} companies"
        )
    except Exception as e:
        logger.error(f"  [Lever] Failed: {e}")
    finally:
        await lever.close()

    # Deduplicate
    dedup = JobDeduplicator()
    unique_jobs = dedup.deduplicate(all_jobs)

    # Cap to avoid overwhelming the scorer
    if len(unique_jobs) > MAX_JOBS_PER_TITLE:
        logger.info(
            f"  Capping from {len(unique_jobs)} to {MAX_JOBS_PER_TITLE} jobs"
        )
        unique_jobs = unique_jobs[:MAX_JOBS_PER_TITLE]

    logger.info(
        f"  Total: {len(all_jobs)} raw -> {len(unique_jobs)} unique "
        f"({len(all_jobs) - len(unique_jobs)} removed)"
    )

    return unique_jobs


# -- Matching Phase --


def create_claude_scorer() -> JobScorer:
    """Create a scorer that uses Claude via the proxy."""
    llm = ChatAnthropic(
        model=CLAUDE_MODEL,
        base_url=CLAUDE_PROXY_URL,
        api_key="proxy-no-key-needed",
        temperature=0.0,
        max_tokens=4096,
    )
    return JobScorer(llm=llm)


def create_embedder() -> JobEmbedder:
    """Create an ephemeral ChromaDB embedder."""
    settings = get_settings()
    api_key = settings.google_api_key.get_secret_value()
    embeddings = GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=api_key,
        task_type="retrieval_document",
    )
    client = chromadb.EphemeralClient()
    return JobEmbedder(embeddings=embeddings, chroma_client=client)


async def match_jobs(
    title: str,
    jobs: list[JobPosting],
    embedder: JobEmbedder,
    scorer: JobScorer,
    top_k: int = 70,
) -> list[ScoredMatch]:
    """Run matching pipeline for a job title search."""
    if not jobs:
        logger.warning(f"  No jobs to match for '{title}'")
        return []

    pipeline = MatchingPipeline(
        embedder=embedder,
        scorer=scorer,
        user_config=USER_CONFIG,
        initial_k=min(top_k + 10, len(jobs)),  # Retrieve a bit more than needed
        final_k=min(top_k, len(jobs)),
        score_concurrency=3,
    )

    logger.info(f"  Indexing {len(jobs)} jobs into ChromaDB...")
    indexed = pipeline.index_jobs(jobs)
    logger.info(f"  Indexed {indexed} new jobs")

    logger.info(
        f"  Running matching pipeline "
        f"(retrieve top-{min(top_k + 10, len(jobs))} -> "
        f"rerank top-{min(top_k, len(jobs))} -> score)..."
    )
    matches = await pipeline.match(resume_text=RESUME_TEXT, jobs=jobs, target_title=title)
    logger.info(f"  Scored {len(matches)} matches")

    return matches[:top_k]


# -- Report Generation --


def generate_report(
    all_results: dict[str, dict],
    output_path: Path,
    scoring_model: str = "Claude Sonnet 4.6 (via proxy)",
) -> None:
    """Generate comprehensive Markdown report with job descriptions."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []
    lines.append("# AI Job Application Agent -- End-to-End Pipeline Test Report")
    lines.append(f"\n**Generated:** {now}")
    lines.append("**User:** Ruiqi Tian (Master of Engineering, U of Waterloo)")
    lines.append(f"**Search Titles:** {', '.join(SEARCH_TITLES)}")
    lines.append(f"**Target Locations:** {', '.join(USER_CONFIG.locations)}")
    lines.append(
        f"**Salary Range:** ${USER_CONFIG.salary_min:,} - "
        f"${USER_CONFIG.salary_max:,} USD"
    )
    lines.append(f"**Workplace:** {', '.join(USER_CONFIG.workplace_types)}")
    lines.append(f"**Scoring Model:** {scoring_model}")
    lines.append("")

    # Executive summary
    lines.append("---")
    lines.append("## Executive Summary")
    lines.append("")
    total_scraped = sum(r["scraped_count"] for r in all_results.values())
    total_matched = sum(len(r["matches"]) for r in all_results.values())
    sources_used: set[str] = set()
    for r in all_results.values():
        sources_used.update(r.get("sources_used", []))

    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Jobs Scraped | {total_scraped} |")
    lines.append(f"| Total Jobs Scored | {total_matched} |")
    lines.append(f"| Search Queries | {len(all_results)} |")
    lines.append(f"| Scraping Sources | {', '.join(sorted(sources_used))} |")
    lines.append(f"| Scoring Model | {scoring_model} |")
    lines.append("| Embedding Model | Gemini embedding-001 |")
    lines.append("| Retrieval | ChromaDB vector search -> FlashRank rerank |")
    lines.append("")

    # Per-title summary table
    lines.append("### Per-Title Summary")
    lines.append("")
    lines.append(
        "| Search Query | Scraped | Scored | Avg Score | "
        "Top Score | Duration |"
    )
    lines.append("|-------------|---------|--------|-----------|-----------|----------|")
    for title, result in all_results.items():
        matches = result["matches"]
        avg = sum(m.score.overall_score for m in matches) / len(matches) if matches else 0
        top = max(m.score.overall_score for m in matches) if matches else 0
        dur = result.get("duration_sec", "N/A")
        lines.append(
            f"| {title} | {result['scraped_count']} | {len(matches)} | "
            f"{avg:.1f}/10 | {top:.1f}/10 | {dur}s |"
        )
    lines.append("")

    # Scraping methodology
    lines.append("---")
    lines.append("## Scraping Sources")
    lines.append("")
    lines.append(f"**Greenhouse Boards ({len(GREENHOUSE_BOARDS)}):** "
                 f"{', '.join(GREENHOUSE_BOARDS)}")
    lines.append(f"**Lever Companies ({len(LEVER_COMPANIES)}):** "
                 f"{', '.join(LEVER_COMPANIES)}")
    lines.append("**Arbeitnow:** 5 pages per search query")
    lines.append("")

    # Per-title detailed results
    for title, result in all_results.items():
        lines.append("---")
        lines.append(f"## Search: \"{title}\"")
        lines.append("")
        lines.append(f"**Jobs Scraped:** {result['scraped_count']} unique")
        lines.append(f"**Jobs Scored:** {len(result['matches'])}")
        lines.append(f"**Duration:** {result.get('duration_sec', 'N/A')}s")
        lines.append("")

        matches: list[ScoredMatch] = result["matches"]

        if not matches:
            lines.append("*No matches found for this search query.*")
            lines.append("")
            continue

        # Summary table
        lines.append("### Match Results Overview")
        lines.append("")
        lines.append(
            "| # | Score | Company | Title | Location | Source | Apply Link |"
        )
        lines.append(
            "|---|-------|---------|-------|----------|--------|------------|"
        )

        for i, m in enumerate(matches, 1):
            score = f"{m.score.overall_score:.1f}/10"
            company = m.job.company or "Unknown"
            loc = m.job.location or "N/A"
            source = m.job.source
            link = f"[Apply]({m.job.apply_url})" if m.job.apply_url else "N/A"
            lines.append(
                f"| {i} | {score} | {company} | {m.job.title} | "
                f"{loc} | {source} | {link} |"
            )
        lines.append("")

        # Detailed per-job analysis with descriptions
        lines.append("### Detailed Job Analysis")
        lines.append("")

        for i, m in enumerate(matches, 1):
            lines.append(
                f"#### {i}. {m.job.title} at {m.job.company or 'Unknown'}"
            )
            lines.append("")
            lines.append(f"- **Overall Score:** {m.score.overall_score:.1f}/10")
            lines.append(
                f"- **Breakdown:** Skills: {m.score.breakdown.skills}/10 | "
                f"Experience: {m.score.breakdown.experience}/10 | "
                f"Education: {m.score.breakdown.education}/10 | "
                f"Location: {m.score.breakdown.location}/10 | "
                f"Salary: {m.score.breakdown.salary}/10"
            )
            lines.append(f"- **Location:** {m.job.location or 'Not specified'}")
            lines.append(
                f"- **Employment Type:** "
                f"{m.job.employment_type or 'Not specified'}"
            )
            if m.job.salary_min and m.job.salary_max:
                lines.append(
                    f"- **Salary:** ${m.job.salary_min:,} - "
                    f"${m.job.salary_max:,} "
                    f"{m.job.salary_currency or 'USD'}"
                )
            lines.append(f"- **Source:** {m.job.source}")
            if m.job.apply_url:
                lines.append(f"- **Apply URL:** {m.job.apply_url}")
            lines.append("")

            # Analysis
            lines.append(f"**Analysis:** {m.score.reasoning}")
            lines.append("")

            if m.score.strengths:
                lines.append("**Strengths (Why it fits):**")
                for s in m.score.strengths:
                    lines.append(f"- {s}")
                lines.append("")

            if m.score.missing_skills:
                lines.append("**Gaps (Why it may not fit):**")
                for s in m.score.missing_skills:
                    lines.append(f"- {s}")
                lines.append("")

            if m.score.interview_talking_points:
                lines.append("**Interview Talking Points:**")
                for p in m.score.interview_talking_points:
                    lines.append(f"- {p}")
                lines.append("")

            # Full job description
            desc = m.job.description or "No description available."
            lines.append("<details>")
            lines.append("<summary>Job Description (click to expand)</summary>")
            lines.append("")
            lines.append(desc)
            lines.append("")
            lines.append("</details>")
            lines.append("")

    # Footer
    lines.append("---")
    lines.append(
        f"*Report generated by AI Job Application Agent E2E Pipeline Test "
        f"using {scoring_model}*"
    )

    report_text = "\n".join(lines)
    output_path.write_text(report_text, encoding="utf-8")
    logger.info(f"Report written to {output_path} ({len(report_text):,} chars)")


# -- Main --


async def main():
    """Run the full end-to-end pipeline test."""
    logger.info("=" * 70)
    logger.info("AI Job Application Agent -- End-to-End Pipeline Test")
    logger.info("  Scoring model: Claude Sonnet 4.6 via proxy")
    logger.info(f"  Proxy URL: {CLAUDE_PROXY_URL}")
    logger.info(f"  Target: {SCORE_PER_TITLE} scored jobs per title")
    logger.info("=" * 70)

    # Verify Google API key (for embeddings)
    reset_settings()
    settings = get_settings()
    api_key = settings.google_api_key.get_secret_value()
    if not api_key or "your-" in api_key.lower():
        logger.error("GOOGLE_API_KEY is not set! Cannot run test.")
        sys.exit(1)
    logger.info(f"Google API key: {api_key[:8]}...")
    logger.info(f"Embedding model: {settings.embedding_model}")

    all_results: dict[str, dict] = {}

    for title_idx, title in enumerate(SEARCH_TITLES):
        if title_idx > 0:
            wait = 10
            logger.info(f"Waiting {wait}s between searches...")
            await asyncio.sleep(wait)

        logger.info("")
        logger.info(f"{'=' * 60}")
        logger.info(f"SEARCH: \"{title}\"")
        logger.info(f"{'=' * 60}")

        t0 = time.time()

        # Phase 1: Scrape
        logger.info(f"Phase 1: Scraping jobs for '{title}'...")
        jobs = await scrape_all_sources(title)

        sources_used = list(set(j.source for j in jobs))

        if len(jobs) < 20:
            logger.warning(
                f"Only found {len(jobs)} jobs for '{title}'. "
                f"Proceeding with what we have."
            )

        # Phase 2: Match & Score
        logger.info(f"Phase 2: Matching & scoring {len(jobs)} jobs...")

        embedder = create_embedder()
        scorer = create_claude_scorer()

        try:
            matches = await match_jobs(
                title=title,
                jobs=jobs,
                embedder=embedder,
                scorer=scorer,
                top_k=SCORE_PER_TITLE,
            )
        except Exception as e:
            logger.error(f"Matching failed for '{title}': {e}", exc_info=True)
            matches = []

        duration = round(time.time() - t0, 1)
        logger.info(
            f"Completed '{title}': {len(jobs)} scraped, "
            f"{len(matches)} scored in {duration}s"
        )

        all_results[title] = {
            "scraped_count": len(jobs),
            "matches": matches,
            "sources_used": sources_used,
            "duration_sec": duration,
        }

    # Phase 3: Generate report
    logger.info("")
    logger.info("=" * 60)
    logger.info("Phase 3: Generating report...")
    logger.info("=" * 60)

    output_dir = Path(__file__).resolve().parent.parent.parent
    output_path = output_dir / "E2E_Pipeline_Test_Report.md"

    generate_report(all_results, output_path)

    # JSON output with job descriptions
    json_path = output_dir / "E2E_Pipeline_Test_Data.json"
    json_data = {}
    for title, result in all_results.items():
        json_data[title] = {
            "scraped_count": result["scraped_count"],
            "scored_count": len(result["matches"]),
            "sources_used": result["sources_used"],
            "duration_sec": result["duration_sec"],
            "matches": [
                {
                    "title": m.job.title,
                    "company": m.job.company,
                    "location": m.job.location,
                    "description": m.job.description,
                    "requirements": m.job.requirements,
                    "employment_type": m.job.employment_type,
                    "salary_min": m.job.salary_min,
                    "salary_max": m.job.salary_max,
                    "salary_currency": m.job.salary_currency,
                    "score": m.score.overall_score,
                    "breakdown": m.score.breakdown.model_dump(),
                    "reasoning": m.score.reasoning,
                    "strengths": m.score.strengths,
                    "missing_skills": m.score.missing_skills,
                    "interview_talking_points": m.score.interview_talking_points,
                    "apply_url": m.job.apply_url,
                    "source": m.job.source,
                }
                for m in result["matches"]
            ],
        }
    json_path.write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info(f"JSON data written to {json_path}")

    # Final summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 70)
    total_scored = 0
    for title, result in all_results.items():
        matches = result["matches"]
        avg_score = (
            sum(m.score.overall_score for m in matches) / len(matches)
            if matches else 0
        )
        total_scored += len(matches)
        logger.info(
            f"  {title}: {result['scraped_count']} scraped, "
            f"{len(matches)} scored, avg score {avg_score:.1f}/10"
        )
    logger.info(f"  TOTAL SCORED: {total_scored}")
    logger.info(f"\nReport: {output_path}")
    logger.info(f"JSON:   {json_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single title mode
        title_arg = " ".join(sys.argv[1:])
        asyncio.run(main())  # Always run full for 200+ job requirement
    else:
        asyncio.run(main())
