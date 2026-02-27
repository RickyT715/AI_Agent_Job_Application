"""CLI script to test the matching pipeline.

Usage:
    uv run python scripts/run_matching.py

Requires: GOOGLE_API_KEY and ANTHROPIC_API_KEY in .env
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import UserConfig, load_user_config
from app.schemas.matching import JobPosting
from app.services.llm_factory import LLMTask, get_embeddings, get_llm
from app.services.matching.embedder import JobEmbedder
from app.services.matching.pipeline import MatchingPipeline
from app.services.matching.scorer import JobScorer

import chromadb

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
DATA_DIR = Path(__file__).parent.parent / "data"


async def main():
    print("=" * 60)
    print("AI Job Application Agent - Matching Pipeline Test")
    print("=" * 60)

    # Load resume
    resume_path = FIXTURES_DIR / "sample_resume.txt"
    if not resume_path.exists():
        print(f"ERROR: Resume file not found at {resume_path}")
        sys.exit(1)
    resume_text = resume_path.read_text(encoding="utf-8")
    print(f"\nLoaded resume ({len(resume_text)} chars)")

    # Load jobs
    jobs_path = FIXTURES_DIR / "sample_jobs.json"
    raw_jobs = json.loads(jobs_path.read_text(encoding="utf-8"))
    jobs = [JobPosting(**j) for j in raw_jobs]
    print(f"Loaded {len(jobs)} sample jobs")

    # Load user config
    user_config_path = DATA_DIR / "user_config.yaml"
    user_config = load_user_config(user_config_path)
    print(f"User config: titles={user_config.job_titles}, locations={user_config.locations}")

    # Set up pipeline with ephemeral ChromaDB (no persistence for testing)
    print("\nInitializing pipeline...")
    client = chromadb.EphemeralClient()
    embeddings = get_embeddings("retrieval_document")
    embedder = JobEmbedder(embeddings=embeddings, chroma_client=client)
    scorer = JobScorer(llm=get_llm(LLMTask.SCORE))

    pipeline = MatchingPipeline(
        embedder=embedder,
        scorer=scorer,
        user_config=user_config,
        initial_k=10,
        final_k=5,
    )

    # Run matching
    print("Running matching pipeline (embed → retrieve → rerank → score)...")
    print("This may take a minute due to API calls...\n")

    results = await pipeline.match(resume_text, jobs=jobs)

    # Display results
    print(f"{'=' * 60}")
    print(f"TOP {len(results)} MATCHES")
    print(f"{'=' * 60}\n")

    for i, match in enumerate(results, 1):
        job = match.job
        score = match.score
        print(f"#{i} | Score: {score.overall_score:.1f}/10")
        print(f"   Title:    {job.title}")
        print(f"   Company:  {job.company}")
        print(f"   Location: {job.location or 'N/A'}")
        print(f"   Salary:   ", end="")
        if job.salary_min and job.salary_max:
            print(f"${job.salary_min:,} - ${job.salary_max:,}")
        else:
            print("Not specified")
        print(f"   Breakdown: skills={score.breakdown.skills}, "
              f"exp={score.breakdown.experience}, "
              f"edu={score.breakdown.education}, "
              f"loc={score.breakdown.location}, "
              f"sal={score.breakdown.salary}")
        print(f"   Reasoning: {score.reasoning}")
        print(f"   Strengths: {', '.join(score.strengths)}")
        if score.missing_skills:
            print(f"   Gaps:      {', '.join(score.missing_skills)}")
        print()

    print(f"{'=' * 60}")
    print("Pipeline test complete!")


if __name__ == "__main__":
    asyncio.run(main())
