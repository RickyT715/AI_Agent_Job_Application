"""Full matching pipeline orchestrator.

Combines all stages: pre-filter → embed → retrieve → quick-score → full-score.
"""

import asyncio
import logging
import re

from langchain_core.documents import Document

from app.config import MatchingWeights, UserConfig
from app.schemas.matching import JobPosting, ScoredMatch
from app.services.llm_factory import LLMTask, get_embeddings, get_llm
from app.services.matching.ats_scorer import compute_ats_score
from app.services.matching.embedder import JobEmbedder
from app.services.matching.multi_query import MultiQueryRetriever
from app.services.matching.pre_filter import JobPreFilter
from app.services.matching.retriever import TwoStageRetriever, compute_dynamic_k
from app.services.matching.scorer import JobScorer

logger = logging.getLogger(__name__)

# Minimum quick-score relevance to proceed to full scoring
QUICK_SCORE_THRESHOLD = 4


def _doc_metadata_to_job(doc: Document, jobs_by_id: dict[str, JobPosting]) -> JobPosting | None:
    """Resolve a retrieved Document back to its JobPosting."""
    job_id = doc.metadata.get("job_id", "")
    source = doc.metadata.get("source", "")
    key = f"{source}:{job_id}"
    return jobs_by_id.get(key)


def _extract_skills_section(resume_text: str) -> str:
    """Extract a skills section from resume text if present."""
    # Look for common skills section headers
    patterns = [
        r"(?i)(?:SKILLS|TECHNICAL SKILLS|TECHNOLOGIES|TECH STACK)[:\s]*\n(.*?)(?:\n\n|\n[A-Z])",
        r"(?i)(?:Languages|Technologies|AI/ML|Backend)[:\s]*(.*?)(?:\n\n|\n[A-Z])",
    ]
    sections = []
    for pattern in patterns:
        matches = re.findall(pattern, resume_text, re.DOTALL)
        sections.extend(matches)

    if sections:
        # Combine and truncate
        combined = " ".join(s.strip() for s in sections)
        return combined[:500]
    return ""


def _weights_to_percentages(weights: MatchingWeights) -> dict[str, int]:
    """Convert MatchingWeights (0-1 floats) to percentage integers."""
    return {
        "skills": round(weights.skills * 100),
        "experience": round(weights.experience * 100),
        "education": round(weights.education * 100),
        "location": round(weights.location * 100),
        "salary": round(weights.salary * 100),
    }


def _compute_integrated_score(
    llm_score: float,
    ats_score: float,
    requirements_met_ratio: float | None = None,
    llm_weight: float = 0.60,
    ats_weight: float = 0.25,
    req_weight: float = 0.15,
) -> float:
    """Combine LLM overall_score (1-10), ATS score (0-100→1-10), and requirements ratio (0-1→1-10).

    Returns a score on a 1-10 scale.
    """
    # Normalize ATS score from 0-100 to 1-10
    ats_normalized = 1.0 + (ats_score / 100.0) * 9.0

    if requirements_met_ratio is not None:
        req_normalized = 1.0 + requirements_met_ratio * 9.0
        return round(
            llm_score * llm_weight + ats_normalized * ats_weight + req_normalized * req_weight,
            2,
        )

    # No requirements ratio — redistribute weight to LLM and ATS
    adjusted_llm = llm_weight + req_weight * 0.6
    adjusted_ats = ats_weight + req_weight * 0.4
    return round(
        llm_score * adjusted_llm + ats_normalized * adjusted_ats,
        2,
    )


class MatchingPipeline:
    """Orchestrates the full job matching pipeline.

    Steps:
        0. Pre-filter jobs (seniority, location, employment type)
        1. Index filtered jobs into ChromaDB with Gemini embeddings
        2. Two-stage retrieval with focused query
        3. Quick-score all reranked candidates (parallel, cheap)
        4. Full-score only candidates with relevance >= threshold (parallel, expensive)
        5. Sort by overall_score descending
    """

    def __init__(
        self,
        embedder: JobEmbedder | None = None,
        scorer: JobScorer | None = None,
        user_config: UserConfig | None = None,
        initial_k: int = 30,
        final_k: int = 10,
        score_concurrency: int = 1,
        quick_score_concurrency: int = 5,
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
        self._score_concurrency = score_concurrency
        self._quick_score_concurrency = quick_score_concurrency

    def index_jobs(self, jobs: list[JobPosting]) -> int:
        """Index jobs into the vector store."""
        return self._embedder.index_jobs(jobs)

    def _build_retrieval_query(self, resume_text: str, target_title: str | None) -> str:
        """Build a focused retrieval query instead of using raw resume text."""
        parts: list[str] = []

        if target_title:
            parts.append(target_title)

        if self._user_config:
            cfg = self._user_config
            if cfg.locations:
                parts.append(" ".join(cfg.locations))
            if cfg.workplace_types:
                parts.append(" ".join(cfg.workplace_types))

        # Extract skills section from resume for focused matching
        skills = _extract_skills_section(resume_text)
        if skills:
            parts.append(skills)

        return " ".join(parts) if parts else resume_text

    async def match(
        self,
        resume_text: str,
        jobs: list[JobPosting] | None = None,
        target_title: str | None = None,
    ) -> list[ScoredMatch]:
        """Run the full matching pipeline.

        Args:
            resume_text: The candidate's resume text.
            jobs: Optional list of jobs to index first. If None, uses existing index.
            target_title: The job title being searched for (e.g. "Software Engineer").

        Returns:
            List of ScoredMatch objects sorted by overall_score descending.
        """
        # Step 0: Pre-filter jobs if we have config and jobs
        if jobs and self._user_config:
            pre_filter = JobPreFilter(self._user_config)
            jobs = pre_filter.filter(jobs, target_title=target_title)

        # Step 1: Index new jobs if provided
        if jobs:
            new_count = self.index_jobs(jobs)
            logger.info(f"Indexed {new_count} new jobs")

        # Check if vectorstore has any documents
        if self._embedder.get_collection_count() == 0:
            logger.warning("No jobs in vector store, returning empty results")
            return []

        # Step 2: Two-stage retrieval with focused query
        # Use dynamic k based on collection size, unless explicitly overridden
        collection_size = self._embedder.get_collection_count()
        initial_k = self._initial_k
        final_k = self._final_k

        if self._user_config:
            cfg = self._user_config
            if cfg.retrieval_initial_k is not None:
                initial_k = cfg.retrieval_initial_k
            elif initial_k == 30:  # default — use dynamic
                initial_k, _ = compute_dynamic_k(collection_size)
            if cfg.retrieval_final_k is not None:
                final_k = cfg.retrieval_final_k
            elif final_k == 10:  # default — use dynamic
                _, final_k = compute_dynamic_k(collection_size)

        query = self._build_retrieval_query(resume_text, target_title)
        retriever = TwoStageRetriever(
            vectorstore=self._embedder.vectorstore,
            initial_k=initial_k,
            final_k=final_k,
        )

        # Multi-query retrieval if enabled
        enable_multi_query = (
            self._user_config.enable_multi_query if self._user_config else False
        )
        if enable_multi_query:
            try:
                llm = get_llm(LLMTask.CLASSIFY)  # Gemini (cheap)
                mq = MultiQueryRetriever(retriever=retriever, llm=llm)
                alt_queries = await mq.generate_queries(query)
                retrieved_docs = mq.retrieve(query, alternative_queries=alt_queries)
            except Exception as e:
                logger.warning(f"Multi-query retrieval failed, falling back: {e}")
                retrieved_docs = retriever.retrieve(query)
        else:
            retrieved_docs = retriever.retrieve(query)

        logger.info(f"Retrieved {len(retrieved_docs)} candidates after reranking")

        # Build lookup from indexed jobs
        jobs_by_id: dict[str, JobPosting] = {}
        if jobs:
            for job in jobs:
                jobs_by_id[f"{job.source}:{job.external_id}"] = job

        # Resolve docs to jobs
        resolved_jobs: list[JobPosting] = []
        for doc in retrieved_docs:
            job = _doc_metadata_to_job(doc, jobs_by_id)
            if job is None:
                job = JobPosting(
                    external_id=doc.metadata.get("job_id", "unknown"),
                    source=doc.metadata.get("source", "unknown"),
                    title=doc.metadata.get("title", "Unknown"),
                    company=doc.metadata.get("company", "Unknown"),
                    location=doc.metadata.get("location") or None,
                    description=doc.page_content,
                )
            resolved_jobs.append(job)

        # Prepare context for scoring
        user_cfg = self._user_config
        preferred_locations = "Any"
        salary_range = "Not specified"
        target_role = target_title or "Software Engineer"
        experience_level = "mid"
        workplace_types = "remote, hybrid"
        weights_pct: dict[str, int] | None = None

        if user_cfg:
            preferred_locations = ", ".join(user_cfg.locations) if user_cfg.locations else "Any"
            if user_cfg.salary_min and user_cfg.salary_max:
                salary_range = f"${user_cfg.salary_min:,} - ${user_cfg.salary_max:,}"
            elif user_cfg.salary_min:
                salary_range = f"${user_cfg.salary_min:,}+"
            experience_level = user_cfg.experience_level
            workplace_types = (
                ", ".join(user_cfg.workplace_types)
                if user_cfg.workplace_types
                else "remote, hybrid"
            )
            weights_pct = _weights_to_percentages(user_cfg.weights)

        # Step 3: Quick-score all candidates (cheap, parallel)
        resume_summary = _extract_skills_section(resume_text) or resume_text[:500]
        qs_sem = asyncio.Semaphore(self._quick_score_concurrency)

        async def _quick_score_one(job: JobPosting) -> tuple[JobPosting, int, str]:
            async with qs_sem:
                try:
                    relevance, reason = await self._scorer.quick_score(
                        resume_summary=resume_summary,
                        job_title=job.title,
                        job_company=job.company,
                        job_description=job.description,
                        target_role=target_role,
                        experience_level=experience_level,
                    )
                    return (job, relevance, reason)
                except Exception as e:
                    logger.warning(f"Quick-score failed for '{job.title}': {e}")
                    # On failure, give benefit of the doubt
                    return (job, QUICK_SCORE_THRESHOLD, "quick-score error")

        quick_results = await asyncio.gather(*[_quick_score_one(j) for j in resolved_jobs])

        # Filter by quick-score threshold
        candidates = []
        skipped = 0
        for job, relevance, reason in quick_results:
            if relevance >= QUICK_SCORE_THRESHOLD:
                candidates.append(job)
            else:
                skipped += 1
                logger.debug(f"Skipped '{job.title}' (quick-score {relevance}: {reason})")

        if skipped > 0:
            logger.info(
                f"Quick-score: {len(resolved_jobs)} → {len(candidates)} "
                f"(skipped {skipped} below threshold {QUICK_SCORE_THRESHOLD})"
            )

        # Step 4: Full-score surviving candidates with Claude
        sem = asyncio.Semaphore(self._score_concurrency)

        async def _score_one(job: JobPosting) -> ScoredMatch | None:
            async with sem:
                for attempt in range(3):
                    try:
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
                            target_role=target_role,
                            experience_level=experience_level,
                            workplace_types=workplace_types,
                            weights=weights_pct,
                        )
                        return ScoredMatch(job=job, score=score)
                    except Exception as e:
                        if attempt < 2:
                            wait = 2 ** attempt
                            logger.warning(
                                f"Score attempt {attempt+1} failed for "
                                f"'{job.title}' at {job.company}, "
                                f"retrying in {wait}s: {e}"
                            )
                            await asyncio.sleep(wait)
                        else:
                            logger.error(
                                f"Scoring failed for '{job.title}' at "
                                f"{job.company} after 3 attempts: {e}"
                            )
                            return None

        results = await asyncio.gather(*[_score_one(j) for j in candidates])
        scored_matches = [m for m in results if m is not None]

        # Step 4.5: Compute ATS scores and integrated scores
        for match in scored_matches:
            try:
                ats = compute_ats_score(
                    resume_text=resume_text,
                    job_description=match.job.description,
                    job_requirements=match.job.requirements,
                )
                match.ats_score = ats
                match.integrated_score = _compute_integrated_score(
                    llm_score=match.score.overall_score,
                    ats_score=ats.score,
                    requirements_met_ratio=match.score.requirements_met_ratio,
                )
            except Exception as e:
                logger.warning(f"ATS scoring failed for '{match.job.title}': {e}")
                match.integrated_score = match.score.overall_score

        # Step 5: Sort by integrated score (fallback to overall_score)
        scored_matches.sort(
            key=lambda m: m.integrated_score if m.integrated_score is not None else m.score.overall_score,
            reverse=True,
        )

        return scored_matches
