"""End-to-end pipeline test: Scrape → Match → Score → Report.

Simulates a real user (Ruiqi Tian) searching for:
  1. Software Engineer
  2. AI Engineer
  3. Full-stack Developer

Uses available free APIs (Arbeitnow, Greenhouse, Lever public boards)
and Gemini for scoring (since Anthropic key is placeholder).
Outputs a detailed Markdown report.
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
# The .env is at project root; GEMINI_API_KEY is in system env
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            if val and "your-" not in val.lower() and "here" not in val.lower():
                os.environ.setdefault(key, val)

# Also propagate GEMINI_API_KEY → GOOGLE_API_KEY if needed
if os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("e2e_test")

# ── Now import app modules ──────────────────────────────────────────────────

import chromadb
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.config import UserConfig, get_settings, reset_settings
from app.schemas.matching import JobPosting, ScoredMatch
from app.services.matching.embedder import JobEmbedder
from app.services.matching.pipeline import MatchingPipeline
from app.services.matching.scorer import JobScorer
from app.services.scraping.api.arbeitnow import ArbeitnowScraper
from app.services.scraping.api.greenhouse import GreenhouseScraper
from app.services.scraping.api.lever import LeverScraper
from app.services.scraping.deduplicator import JobDeduplicator

# ── User Profile ─────────────────────────────────────────────────────────────

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

USER_CONFIG = UserConfig(
    job_titles=["Software Engineer", "AI Engineer", "Full-stack Developer"],
    locations=["Remote", "United States", "Canada"],
    salary_min=100000,
    salary_max=200000,
    workplace_types=["remote", "hybrid"],
    experience_level="mid",
    employment_types=["FULLTIME"],
    final_results_count=20,
    num_pages_per_source=3,
    enabled_sources=["arbeitnow", "greenhouse", "lever"],
    greenhouse_board_tokens=[
        "figma", "cloudflare", "stripe", "datadog",
        "airbnb", "databricks",
        # Additional boards with full-stack / web eng roles
        "airtable", "gusto", "cockroachlabs", "benchling",
        "relativityspace", "nianticlabs",
    ],
    lever_companies=[
        "netflix",
        # Additional Lever companies
        "nerdwallet", "rippling", "samsara",
    ],
)

# ── Well-known Greenhouse boards with many SWE jobs ─────────────────────────

# These boards are publicly accessible and don't need auth
GREENHOUSE_BOARDS = USER_CONFIG.greenhouse_board_tokens
LEVER_COMPANIES = USER_CONFIG.lever_companies

# ── Job title queries ────────────────────────────────────────────────────────

SEARCH_TITLES = [
    "Software Engineer",
    "AI Engineer",
    "Full-stack Developer",
]

# ── Scraping Phase ───────────────────────────────────────────────────────────


async def scrape_all_sources(title: str) -> list[JobPosting]:
    """Scrape from all free sources for a given job title."""
    MAX_JOBS_PER_TITLE = 100  # Cap to avoid API rate limits
    all_jobs: list[JobPosting] = []
    errors: list[str] = []
    title_lower = title.lower()

    # Build keyword variants for smarter matching on compound terms
    _TITLE_VARIANTS: dict[str, list[str]] = {
        "full-stack developer": ["full stack", "fullstack", "full-stack"],
        "full stack developer": ["full stack", "fullstack", "full-stack"],
        "ai engineer": ["ai engineer", "ai/ml engineer", "machine learning engineer", "ml engineer"],
    }

    def _is_relevant(job_title: str) -> bool:
        """Check if a job title is closely relevant to the search query.

        Uses the full search phrase as a substring match. For compound queries
        like 'Software Engineer', requires the full phrase (not just 'software').
        For 'Full-stack Developer', also matches 'Full Stack Engineer', 'Fullstack', etc.
        """
        jt = job_title.lower()
        # Direct phrase match (e.g., "software engineer" in title)
        if title_lower in jt:
            return True
        # Normalize dashes/underscores and check again
        normalized_query = title_lower.replace("-", " ").replace("_", " ")
        normalized_jt = jt.replace("-", " ").replace("_", " ")
        if normalized_query in normalized_jt:
            return True
        # Check known variants for compound titles
        variants = _TITLE_VARIANTS.get(title_lower, [])
        for variant in variants:
            if variant in normalized_jt:
                return True
        return False

    # 1. Arbeitnow (free public API, no auth)
    logger.info(f"  [Arbeitnow] Scraping for '{title}'...")
    arb = ArbeitnowScraper()
    try:
        arb_result = await arb.scrape(title, num_pages=5)
        all_jobs.extend(arb_result.jobs)
        logger.info(f"  [Arbeitnow] Found {len(arb_result.jobs)} jobs (scanned {arb_result.total_found})")
        if arb_result.errors:
            errors.extend(arb_result.errors)
    except Exception as e:
        logger.error(f"  [Arbeitnow] Failed: {e}")
        errors.append(f"Arbeitnow: {e}")
    finally:
        await arb.close()

    # 2. Greenhouse (free public API, no auth)
    logger.info(f"  [Greenhouse] Scraping {len(GREENHOUSE_BOARDS)} boards...")
    gh = GreenhouseScraper(board_tokens=GREENHOUSE_BOARDS)
    try:
        gh_result = await gh.scrape(title)
        # Filter by strict title relevance (full phrase match, not individual words)
        relevant_gh = [j for j in gh_result.jobs if _is_relevant(j.title)]
        all_jobs.extend(relevant_gh)
        logger.info(
            f"  [Greenhouse] Found {len(relevant_gh)} relevant / "
            f"{len(gh_result.jobs)} total from {len(GREENHOUSE_BOARDS)} boards"
        )
        if gh_result.errors:
            errors.extend(gh_result.errors)
    except Exception as e:
        logger.error(f"  [Greenhouse] Failed: {e}")
        errors.append(f"Greenhouse: {e}")
    finally:
        await gh.close()

    # 3. Lever (free public API, no auth)
    logger.info(f"  [Lever] Scraping {len(LEVER_COMPANIES)} companies...")
    lever = LeverScraper(companies=LEVER_COMPANIES)
    try:
        lever_result = await lever.scrape(title)
        relevant_lever = [j for j in lever_result.jobs if _is_relevant(j.title)]
        all_jobs.extend(relevant_lever)
        logger.info(
            f"  [Lever] Found {len(relevant_lever)} relevant / "
            f"{len(lever_result.jobs)} total from {len(LEVER_COMPANIES)} companies"
        )
        if lever_result.errors:
            errors.extend(lever_result.errors)
    except Exception as e:
        logger.error(f"  [Lever] Failed: {e}")
        errors.append(f"Lever: {e}")
    finally:
        await lever.close()

    # Deduplicate
    dedup = JobDeduplicator()
    unique_jobs = dedup.deduplicate(all_jobs)

    # Cap to avoid API quota exhaustion
    if len(unique_jobs) > MAX_JOBS_PER_TITLE:
        logger.info(
            f"  Capping from {len(unique_jobs)} to {MAX_JOBS_PER_TITLE} jobs "
            f"to stay within API limits"
        )
        unique_jobs = unique_jobs[:MAX_JOBS_PER_TITLE]

    logger.info(
        f"  Total: {len(all_jobs)} raw → {len(unique_jobs)} unique "
        f"({len(all_jobs) - len(unique_jobs)} removed by dedup/cap)"
    )

    return unique_jobs


# ── Matching Phase ───────────────────────────────────────────────────────────


def create_gemini_scorer() -> JobScorer:
    """Create a scorer that uses Gemini instead of Claude."""
    settings = get_settings()
    api_key = settings.google_api_key.get_secret_value()
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=api_key,
        temperature=0.0,
    )
    return JobScorer(llm=llm)


def create_embedder() -> JobEmbedder:
    """Create an ephemeral ChromaDB embedder for testing."""
    settings = get_settings()
    api_key = settings.google_api_key.get_secret_value()
    embeddings = GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=api_key,
        task_type="retrieval_document",
    )
    client = chromadb.EphemeralClient()
    return JobEmbedder(
        embeddings=embeddings,
        chroma_client=client,
    )


async def match_jobs(
    title: str,
    jobs: list[JobPosting],
    embedder: JobEmbedder,
    scorer: JobScorer,
    top_k: int = 20,
) -> list[ScoredMatch]:
    """Run matching pipeline for a job title search."""
    if not jobs:
        logger.warning(f"  No jobs to match for '{title}'")
        return []

    pipeline = MatchingPipeline(
        embedder=embedder,
        scorer=scorer,
        user_config=USER_CONFIG,
        initial_k=min(30, len(jobs)),
        final_k=min(top_k, len(jobs)),
    )

    logger.info(f"  Indexing {len(jobs)} jobs into ChromaDB...")
    indexed = pipeline.index_jobs(jobs)
    logger.info(f"  Indexed {indexed} new jobs")

    logger.info("  Running matching pipeline (retrieve → rerank → score)...")
    matches = await pipeline.match(resume_text=RESUME_TEXT, jobs=jobs)
    logger.info(f"  Scored {len(matches)} matches")

    return matches[:top_k]


# ── Report Generation ────────────────────────────────────────────────────────


def generate_report(
    all_results: dict[str, dict],
    output_path: Path,
) -> None:
    """Generate comprehensive Markdown report."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []
    lines.append("# AI Job Application Agent — End-to-End Pipeline Test Report")
    lines.append(f"\n**Generated:** {now}")
    lines.append("**User:** Ruiqi Tian (Master of Engineering, U of Waterloo)")
    lines.append(f"**Search Titles:** {', '.join(SEARCH_TITLES)}")
    lines.append(f"**Target Locations:** {', '.join(USER_CONFIG.locations)}")
    lines.append(
        f"**Salary Range:** ${USER_CONFIG.salary_min:,} - ${USER_CONFIG.salary_max:,} USD"
    )
    lines.append(f"**Workplace:** {', '.join(USER_CONFIG.workplace_types)}")
    lines.append("")

    # Executive summary
    lines.append("---")
    lines.append("## Executive Summary")
    lines.append("")
    total_scraped = sum(r["scraped_count"] for r in all_results.values())
    total_matched = sum(len(r["matches"]) for r in all_results.values())
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Jobs Scraped | {total_scraped} |")
    lines.append(f"| Total Jobs Scored | {total_matched} |")
    lines.append(f"| Search Queries | {len(SEARCH_TITLES)} |")

    sources_used = set()
    for r in all_results.values():
        sources_used.update(r.get("sources_used", []))
    lines.append(f"| Scraping Sources | {', '.join(sorted(sources_used))} |")
    lines.append("| Scoring Model | Gemini (via Google AI) |")
    lines.append("| Embedding Model | Gemini embedding-001 |")
    lines.append("| Retrieval | ChromaDB (top-30) → FlashRank rerank (top-20) |")
    lines.append("")

    # Scraping sources detail
    lines.append("---")
    lines.append("## Scraping Sources & Methodology")
    lines.append("")
    lines.append("| Source | Type | Auth Required | Method |")
    lines.append("|--------|------|---------------|--------|")
    lines.append("| Arbeitnow | Public API | No | Full-text search with client-side keyword filtering across 5 pages |")
    lines.append(f"| Greenhouse | Public Board API | No | Fetched ALL jobs from {len(GREENHOUSE_BOARDS)} boards, filtered by title keywords |")
    lines.append(f"| Lever | Public Postings API | No | Fetched ALL postings from {len(LEVER_COMPANIES)} companies, filtered by title keywords |")
    lines.append("")
    lines.append(f"**Greenhouse Boards:** {', '.join(GREENHOUSE_BOARDS)}")
    lines.append(f"**Lever Companies:** {', '.join(LEVER_COMPANIES)}")
    lines.append("")

    # Per-title detailed results
    for title, result in all_results.items():
        lines.append("---")
        lines.append(f"## Search: \"{title}\"")
        lines.append("")
        lines.append(f"**Jobs Scraped:** {result['scraped_count']} unique")
        lines.append(f"**Jobs Scored:** {len(result['matches'])}")
        if result.get("scrape_errors"):
            lines.append(f"**Scraping Errors:** {', '.join(result['scrape_errors'][:5])}")
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
        lines.append("| # | Score | Company | Title | Location | Source | Apply Link |")
        lines.append("|---|-------|---------|-------|----------|--------|------------|")

        for i, m in enumerate(matches, 1):
            score = f"{m.score.overall_score:.1f}/10"
            company = m.job.company or "Unknown"
            job_title = m.job.title
            loc = m.job.location or "Not specified"
            source = m.job.source
            link = f"[Apply]({m.job.apply_url})" if m.job.apply_url else "N/A"
            lines.append(f"| {i} | {score} | {company} | {job_title} | {loc} | {source} | {link} |")

        lines.append("")

        # Detailed per-job analysis
        lines.append("### Detailed Job Analysis")
        lines.append("")

        for i, m in enumerate(matches, 1):
            lines.append(f"#### {i}. {m.job.title} at {m.job.company or 'Unknown'}")
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
            lines.append(f"- **Employment Type:** {m.job.employment_type or 'Not specified'}")
            if m.job.salary_min and m.job.salary_max:
                lines.append(
                    f"- **Salary:** ${m.job.salary_min:,} - ${m.job.salary_max:,} "
                    f"{m.job.salary_currency or 'USD'}"
                )
            lines.append(f"- **Source:** {m.job.source}")
            if m.job.apply_url:
                lines.append(f"- **Apply URL:** {m.job.apply_url}")
            lines.append("")

            # Why it fits / doesn't fit
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

            # Job description (truncated)
            desc = m.job.description or ""
            if len(desc) > 500:
                desc = desc[:500] + "..."
            lines.append(f"**Job Description (preview):** {desc}")
            lines.append("")

    # Footer
    lines.append("---")
    lines.append("## Pipeline Architecture")
    lines.append("")
    lines.append("```")
    lines.append("User Profile + Job Titles")
    lines.append("        │")
    lines.append("        ▼")
    lines.append("┌─────────────────────────────┐")
    lines.append("│   SCRAPING PHASE            │")
    lines.append("│   Arbeitnow (5 pages)       │")
    lines.append("│   Greenhouse (12 boards)     │")
    lines.append("│   Lever (7 companies)        │")
    lines.append("│   + Deduplication            │")
    lines.append("└─────────────┬───────────────┘")
    lines.append("              │")
    lines.append("              ▼")
    lines.append("┌─────────────────────────────┐")
    lines.append("│   MATCHING PHASE            │")
    lines.append("│   1. Gemini Embeddings      │")
    lines.append("│   2. ChromaDB Vector Search  │")
    lines.append("│   3. FlashRank Reranking     │")
    lines.append("│   4. Gemini LLM-as-Judge     │")
    lines.append("└─────────────┬───────────────┘")
    lines.append("              │")
    lines.append("              ▼")
    lines.append("┌─────────────────────────────┐")
    lines.append("│   REPORT GENERATION         │")
    lines.append("│   Detailed Markdown Report   │")
    lines.append("│   with scores & analysis     │")
    lines.append("└─────────────────────────────┘")
    lines.append("```")
    lines.append("")
    lines.append("*Report generated by AI Job Application Agent E2E Pipeline Test*")

    report_text = "\n".join(lines)
    output_path.write_text(report_text, encoding="utf-8")
    logger.info(f"Report written to {output_path} ({len(report_text)} chars)")


# ── Main ─────────────────────────────────────────────────────────────────────


async def main():
    """Run the full end-to-end pipeline test."""
    logger.info("=" * 70)
    logger.info("AI Job Application Agent — End-to-End Pipeline Test")
    logger.info("=" * 70)

    # Verify API key
    reset_settings()
    settings = get_settings()
    api_key = settings.google_api_key.get_secret_value()
    if not api_key or "your-" in api_key.lower():
        logger.error("GOOGLE_API_KEY is not set! Cannot run test.")
        sys.exit(1)
    logger.info(f"Google API key: {api_key[:8]}...")
    logger.info(f"Gemini model: {settings.gemini_model}")
    logger.info(f"Embedding model: {settings.embedding_model}")

    all_results: dict[str, dict] = {}

    for title_idx, title in enumerate(SEARCH_TITLES):
        # Wait between searches to avoid API rate limits
        if title_idx > 0:
            wait = 30
            logger.info(f"Waiting {wait}s between searches for API quota recovery...")
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
        scrape_errors = []

        if len(jobs) < 20:
            logger.warning(
                f"Only found {len(jobs)} jobs for '{title}'. "
                f"Proceeding with what we have."
            )

        # Phase 2: Match & Score
        logger.info(f"Phase 2: Matching & scoring {len(jobs)} jobs...")

        # Create fresh embedder per search (isolated ChromaDB)
        embedder = create_embedder()
        scorer = create_gemini_scorer()

        try:
            matches = await match_jobs(
                title=title,
                jobs=jobs,
                embedder=embedder,
                scorer=scorer,
                top_k=20,
            )
        except Exception as e:
            logger.error(f"Matching failed for '{title}': {e}", exc_info=True)
            matches = []
            scrape_errors.append(f"Matching error: {e}")

        duration = round(time.time() - t0, 1)
        logger.info(
            f"Completed '{title}': {len(jobs)} scraped, "
            f"{len(matches)} scored in {duration}s"
        )

        all_results[title] = {
            "scraped_count": len(jobs),
            "matches": matches,
            "sources_used": sources_used,
            "scrape_errors": scrape_errors,
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

    # Also output a JSON summary
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
                    "score": m.score.overall_score,
                    "breakdown": m.score.breakdown.model_dump(),
                    "reasoning": m.score.reasoning,
                    "strengths": m.score.strengths,
                    "missing_skills": m.score.missing_skills,
                    "apply_url": m.job.apply_url,
                    "source": m.job.source,
                }
                for m in result["matches"]
            ],
        }
    json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"JSON data written to {json_path}")

    # Final summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 70)
    for title, result in all_results.items():
        matches = result["matches"]
        avg_score = (
            sum(m.score.overall_score for m in matches) / len(matches)
            if matches
            else 0
        )
        logger.info(
            f"  {title}: {result['scraped_count']} scraped, "
            f"{len(matches)} scored, avg score {avg_score:.1f}/10"
        )
    logger.info(f"\nReport: {output_path}")
    logger.info(f"JSON:   {json_path}")


async def run_single_title(title: str):
    """Run the pipeline for a single title (useful for re-running one search)."""
    logger.info("=" * 70)
    logger.info(f"AI Job Application Agent — Single Title Search: '{title}'")
    logger.info("=" * 70)

    reset_settings()
    settings = get_settings()
    api_key = settings.google_api_key.get_secret_value()
    if not api_key or "your-" in api_key.lower():
        logger.error("GOOGLE_API_KEY is not set! Cannot run test.")
        sys.exit(1)
    logger.info(f"Google API key: {api_key[:8]}...")
    logger.info(f"Gemini model: {settings.gemini_model}")
    logger.info(f"Embedding model: {settings.embedding_model}")

    t0 = time.time()

    logger.info(f"Phase 1: Scraping jobs for '{title}'...")
    jobs = await scrape_all_sources(title)

    logger.info(f"Phase 2: Matching & scoring {len(jobs)} jobs...")
    embedder = create_embedder()
    scorer = create_gemini_scorer()

    try:
        matches = await match_jobs(
            title=title, jobs=jobs, embedder=embedder, scorer=scorer, top_k=20,
        )
    except Exception as e:
        logger.error(f"Matching failed: {e}", exc_info=True)
        matches = []

    duration = round(time.time() - t0, 1)
    logger.info(f"Completed: {len(jobs)} scraped, {len(matches)} scored in {duration}s")

    # Generate a partial report
    result = {
        "scraped_count": len(jobs),
        "matches": matches,
        "sources_used": list(set(j.source for j in jobs)),
        "scrape_errors": [],
        "duration_sec": duration,
    }

    output_dir = Path(__file__).resolve().parent.parent.parent
    output_path = output_dir / f"E2E_Single_{title.replace(' ', '_')}_Report.md"
    generate_report({title: result}, output_path)

    # JSON output
    json_path = output_dir / f"E2E_Single_{title.replace(' ', '_')}_Data.json"
    json_data = {
        title: {
            "scraped_count": result["scraped_count"],
            "scored_count": len(matches),
            "sources_used": result["sources_used"],
            "duration_sec": result["duration_sec"],
            "matches": [
                {
                    "title": m.job.title,
                    "company": m.job.company,
                    "location": m.job.location,
                    "score": m.score.overall_score,
                    "breakdown": m.score.breakdown.model_dump(),
                    "reasoning": m.score.reasoning,
                    "strengths": m.score.strengths,
                    "missing_skills": m.score.missing_skills,
                    "apply_url": m.job.apply_url,
                    "source": m.job.source,
                }
                for m in matches
            ],
        }
    }
    json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info(f"\nReport: {output_path}")
    logger.info(f"JSON:   {json_path}")

    return result


if __name__ == "__main__":
    # If run with a title argument, run just that title; otherwise run all
    if len(sys.argv) > 1:
        asyncio.run(run_single_title(" ".join(sys.argv[1:])))
    else:
        asyncio.run(main())
