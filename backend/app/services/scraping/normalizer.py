"""Job data normalizer: JSON-LD first, Gemini Flash LLM fallback.

Handles messy or unstructured job data by:
1. Attempting JSON-LD Schema.org extraction
2. Falling back to Gemini Flash with structured output for extraction
"""

import logging

from app.schemas.matching import JobPosting
from app.services.llm_factory import LLMTask, get_llm
from app.services.scraping.browser.generic import extract_jsonld_jobs

logger = logging.getLogger(__name__)


class JobNormalizer:
    """Normalizes raw HTML or unstructured data into JobPosting."""

    def __init__(self, llm=None) -> None:
        self._llm = llm

    def _get_llm(self):
        if self._llm is None:
            self._llm = get_llm(LLMTask.EXTRACT)
        return self._llm

    async def normalize_html(self, html: str, source_url: str = "") -> JobPosting | None:
        """Normalize an HTML page to a JobPosting.

        Strategy:
        1. Try JSON-LD extraction (fast, free)
        2. Fall back to LLM extraction (Gemini Flash)
        """
        # Strategy 1: JSON-LD
        jsonld_jobs = extract_jsonld_jobs(html)
        if jsonld_jobs:
            logger.info("Extracted job via JSON-LD")
            return self._jsonld_to_posting(jsonld_jobs[0], source_url)

        # Strategy 2: LLM extraction
        logger.info("No JSON-LD found, falling back to LLM extraction")
        return await self._llm_extract(html, source_url)

    def _jsonld_to_posting(self, data: dict, source_url: str) -> JobPosting | None:
        """Convert JSON-LD data to a JobPosting."""
        try:
            title = data.get("title", "")
            if not title:
                return None

            org = data.get("hiringOrganization", {})
            company = org.get("name", "Unknown") if isinstance(org, dict) else "Unknown"

            description = data.get("description", "")

            return JobPosting(
                external_id=str(hash(f"{company}:{title}")),
                source="generic",
                title=title,
                company=company,
                description=description,
                apply_url=source_url or data.get("url"),
                raw_data=data,
            )
        except Exception as e:
            logger.warning(f"JSON-LD conversion failed: {e}")
            return None

    async def _llm_extract(self, html: str, source_url: str) -> JobPosting | None:
        """Use Gemini Flash to extract job posting from messy HTML."""
        llm = self._get_llm()
        structured_llm = llm.with_structured_output(JobPosting)

        # Truncate HTML to avoid token limits
        truncated = html[:15000] if len(html) > 15000 else html

        try:
            result = await structured_llm.ainvoke(
                f"Extract the job posting details from this HTML page. "
                f"If you cannot find a job posting, return a minimal object with "
                f'title="Unknown" and description="No job posting found".\n\n'
                f"Source URL: {source_url}\n\n"
                f"HTML content:\n{truncated}"
            )
            # Fill in source info
            if hasattr(result, "source") and not result.source:
                result.source = "generic"
            if hasattr(result, "apply_url") and not result.apply_url:
                result.apply_url = source_url
            return result
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return None
