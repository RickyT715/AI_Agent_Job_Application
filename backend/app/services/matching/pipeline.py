"""Full matching pipeline orchestrator.

Combines all stages: embed → retrieve → rerank → score into a single pipeline.
"""

import logging

from langchain_core.documents import Document

from app.config import UserConfig, load_user_config
from app.schemas.matching import JobPosting, ScoredMatch
from app.services.llm_factory import LLMTask, get_embeddings, get_llm
from app.services.matching.embedder import JobEmbedder
from app.services.matching.retriever import TwoStageRetriever
from app.services.matching.scorer import JobScorer

logger = logging.getLogger(__name__)


def _doc_metadata_to_job(doc: Document, jobs_by_id: dict[str, JobPosting]) -> JobPosting | None:
    """Resolve a retrieved Document back to its JobPosting."""
    job_id = doc.metadata.get("job_id", "")
    source = doc.metadata.get("source", "")
    key = f"{source}:{job_id}"
    return jobs_by_id.get(key)


class MatchingPipeline:
    """Orchestrates the full job matching pipeline.

    Steps:
        1. Index jobs into ChromaDB with Gemini embeddings
        2. Retrieve candidates via vector similarity (top-30)
        3. Rerank with FlashRank (top-10)
        4. Score each candidate with Claude LLM-as-Judge
    """

    def __init__(
        self,
        embedder: JobEmbedder | None = None,
        scorer: JobScorer | None = None,
        user_config: UserConfig | None = None,
        initial_k: int = 30,
        final_k: int = 10,
    ) -> None:
        # Embedder (ChromaDB + Gemini)
        if embedder is not None:
            self._embedder = embedder
        else:
            self._embedder = JobEmbedder(embeddings=get_embeddings("retrieval_document"))

        # Scorer (Claude LLM-as-Judge)
        if scorer is not None:
            self._scorer = scorer
        else:
            self._scorer = JobScorer(llm=get_llm(LLMTask.SCORE))

        # User config
        self._user_config = user_config

        self._initial_k = initial_k
        self._final_k = final_k

    def index_jobs(self, jobs: list[JobPosting]) -> int:
        """Index jobs into the vector store."""
        return self._embedder.index_jobs(jobs)

    async def match(
        self,
        resume_text: str,
        jobs: list[JobPosting] | None = None,
    ) -> list[ScoredMatch]:
        """Run the full matching pipeline.

        Args:
            resume_text: The candidate's resume text.
            jobs: Optional list of jobs to index first. If None, uses existing index.

        Returns:
            List of ScoredMatch objects sorted by overall_score descending.
        """
        # Step 1: Index new jobs if provided
        if jobs:
            new_count = self.index_jobs(jobs)
            logger.info(f"Indexed {new_count} new jobs")

        # Check if vectorstore has any documents
        if self._embedder.get_collection_count() == 0:
            logger.warning("No jobs in vector store, returning empty results")
            return []

        # Step 2: Two-stage retrieval
        retriever = TwoStageRetriever(
            vectorstore=self._embedder.vectorstore,
            initial_k=self._initial_k,
            final_k=self._final_k,
        )
        retrieved_docs = retriever.retrieve(resume_text)
        logger.info(f"Retrieved {len(retrieved_docs)} candidates after reranking")

        # Build lookup from indexed jobs
        jobs_by_id: dict[str, JobPosting] = {}
        if jobs:
            for job in jobs:
                jobs_by_id[f"{job.source}:{job.external_id}"] = job

        # Step 3: Score each candidate with Claude
        user_cfg = self._user_config
        preferred_locations = "Any"
        salary_range = "Not specified"
        if user_cfg:
            preferred_locations = ", ".join(user_cfg.locations) if user_cfg.locations else "Any"
            if user_cfg.salary_min and user_cfg.salary_max:
                salary_range = f"${user_cfg.salary_min:,} - ${user_cfg.salary_max:,}"
            elif user_cfg.salary_min:
                salary_range = f"${user_cfg.salary_min:,}+"

        scored_matches: list[ScoredMatch] = []
        for doc in retrieved_docs:
            job = _doc_metadata_to_job(doc, jobs_by_id)
            if job is None:
                # Reconstruct minimal job from document metadata
                job = JobPosting(
                    external_id=doc.metadata.get("job_id", "unknown"),
                    source=doc.metadata.get("source", "unknown"),
                    title=doc.metadata.get("title", "Unknown"),
                    company=doc.metadata.get("company", "Unknown"),
                    location=doc.metadata.get("location") or None,
                    description=doc.page_content,
                )

            score = await self._scorer.score(
                resume_text=resume_text,
                job_title=job.title,
                job_company=job.company,
                job_description=job.description,
                job_location=job.location or "Not specified",
                job_requirements=job.requirements or "Not specified",
                job_salary=(
                    f"${job.salary_min:,} - ${job.salary_max:,}"
                    if job.salary_min and job.salary_max
                    else "Not specified"
                ),
                preferred_locations=preferred_locations,
                salary_range=salary_range,
            )

            scored_matches.append(ScoredMatch(job=job, score=score))

        # Step 4: Sort by overall score descending
        scored_matches.sort(key=lambda m: m.score.overall_score, reverse=True)

        return scored_matches
