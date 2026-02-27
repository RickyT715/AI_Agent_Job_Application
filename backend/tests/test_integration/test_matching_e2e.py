"""End-to-end matching pipeline test using real APIs.

Run: uv run pytest -m integration tests/test_integration/test_matching_e2e.py
Requires: GOOGLE_API_KEY and ANTHROPIC_API_KEY in .env
"""

import json
from pathlib import Path

import chromadb
import pytest

from app.config import UserConfig
from app.schemas.matching import JobPosting, ScoredMatch
from app.services.llm_factory import LLMTask, get_embeddings, get_llm
from app.services.matching.embedder import JobEmbedder
from app.services.matching.pipeline import MatchingPipeline
from app.services.matching.scorer import JobScorer

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.mark.integration
async def test_full_matching_pipeline():
    """Full pipeline: embed → retrieve → rerank → score with real APIs."""
    # 1. Load sample resume
    resume_text = (FIXTURES_DIR / "sample_resume.txt").read_text(encoding="utf-8")

    # 2. Load sample jobs
    raw_jobs = json.loads((FIXTURES_DIR / "sample_jobs.json").read_text(encoding="utf-8"))
    jobs = [JobPosting(**j) for j in raw_jobs]

    # 3. Set up ephemeral ChromaDB with real Gemini embeddings
    client = chromadb.EphemeralClient()
    embeddings = get_embeddings("retrieval_document")
    embedder = JobEmbedder(embeddings=embeddings, chroma_client=client)

    # 4. Set up scorer with real Claude
    scorer = JobScorer(llm=get_llm(LLMTask.SCORE))

    # 5. Set up user config
    user_config = UserConfig(
        locations=["Remote", "San Francisco, CA"],
        salary_min=120000,
        salary_max=200000,
    )

    # 6. Run pipeline (with small k values for cost efficiency)
    pipeline = MatchingPipeline(
        embedder=embedder,
        scorer=scorer,
        user_config=user_config,
        initial_k=10,
        final_k=3,
    )
    results = await pipeline.match(resume_text, jobs=jobs)

    # 7. Assertions
    assert len(results) > 0, "Pipeline should return at least one result"
    assert all(isinstance(r, ScoredMatch) for r in results)

    # Results should be sorted by score descending
    scores = [r.score.overall_score for r in results]
    assert scores == sorted(scores, reverse=True)

    # Each result should have full scoring data
    for result in results:
        assert result.score.reasoning, "Each score should have reasoning"
        assert isinstance(result.score.missing_skills, list)
        assert isinstance(result.score.strengths, list)
        assert 1.0 <= result.score.overall_score <= 10.0

    # Top result should be a relevant tech job (not marketing)
    top_job = results[0].job
    assert top_job.title != "Marketing Coordinator", (
        "Top match for a SWE resume should not be a marketing role"
    )
