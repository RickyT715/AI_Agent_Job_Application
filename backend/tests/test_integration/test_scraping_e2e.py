"""End-to-end scraping + matching pipeline test.

Run: uv run pytest -m integration tests/test_integration/test_scraping_e2e.py
Requires: GOOGLE_API_KEY, ANTHROPIC_API_KEY, and JSEARCH_API_KEY in .env
"""

from pathlib import Path

import chromadb
import pytest

from app.config import UserConfig
from app.schemas.matching import JobPosting
from app.services.llm_factory import LLMTask, get_embeddings, get_llm
from app.services.matching.embedder import JobEmbedder
from app.services.matching.pipeline import MatchingPipeline
from app.services.matching.scorer import JobScorer
from app.services.scraping.api.jsearch import JSearchScraper
from app.services.scraping.deduplicator import JobDeduplicator
from app.services.scraping.orchestrator import ScrapingOrchestrator

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.mark.integration
async def test_scrape_and_match_pipeline():
    """Scrape real jobs via JSearch, then run matching pipeline."""
    # 1. Set up scraping
    scraper = JSearchScraper()
    dedup = JobDeduplicator()
    orchestrator = ScrapingOrchestrator(scrapers=[scraper], deduplicator=dedup)

    # 2. Run scraping
    scrape_result = await orchestrator.run(
        "Software Engineer",
        location="Remote",
        num_pages=1,
    )

    # 3. Assert: at least some jobs scraped
    assert len(scrape_result.jobs) >= 1, "Should scrape at least 1 job"
    for job in scrape_result.jobs:
        assert isinstance(job, JobPosting)
        assert job.title
        assert job.company

    # 4. Assert: no duplicates in results
    assert scrape_result.duplicates >= 0

    # 5. Set up matching pipeline with ephemeral ChromaDB
    client = chromadb.EphemeralClient()
    embeddings = get_embeddings("retrieval_document")
    embedder = JobEmbedder(embeddings=embeddings, chroma_client=client)
    scorer = JobScorer(llm=get_llm(LLMTask.SCORE))

    user_config = UserConfig(
        locations=["Remote"],
        salary_min=100000,
    )

    pipeline = MatchingPipeline(
        embedder=embedder,
        scorer=scorer,
        user_config=user_config,
        initial_k=min(len(scrape_result.jobs), 10),
        final_k=min(len(scrape_result.jobs), 3),
    )

    # 6. Load resume and run matching
    resume_text = (FIXTURES_DIR / "sample_resume.txt").read_text(encoding="utf-8")
    results = await pipeline.match(resume_text, jobs=scrape_result.jobs)

    # 7. Assert: scored matches returned
    assert len(results) > 0
    scores = [r.score.overall_score for r in results]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.integration
async def test_individual_jsearch_real_api():
    """Test JSearch scraper with real API."""
    scraper = JSearchScraper()
    result = await scraper.scrape("Python Developer", num_pages=1)
    await scraper.close()

    assert len(result.jobs) > 0
    for job in result.jobs:
        assert job.title
        assert job.company
        assert job.source == "jsearch"
