"""Multi-query retrieval: generate alternative search queries for broader coverage.

Uses Gemini (cheap) to generate alternative queries, runs base retriever on each,
deduplicates and merges results.
"""

import json
import logging

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel

from app.services.matching.retriever import TwoStageRetriever

logger = logging.getLogger(__name__)

_QUERY_GEN_PROMPT = """Generate {n} alternative search queries for finding relevant job postings.
The original query is: "{query}"

Return a JSON array of strings, e.g. ["query1", "query2", "query3"].
Focus on:
- Synonym variations (e.g., "software engineer" → "software developer")
- Skill-focused rephrasing
- Role-level variations

Return ONLY the JSON array, no other text."""


class MultiQueryRetriever:
    """Generates multiple search queries and merges retrieval results."""

    def __init__(
        self,
        retriever: TwoStageRetriever,
        llm: BaseChatModel,
        num_queries: int = 3,
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._num_queries = num_queries

    async def generate_queries(self, original_query: str) -> list[str]:
        """Generate alternative search queries using Gemini."""
        try:
            response = await self._llm.ainvoke(
                _QUERY_GEN_PROMPT.format(query=original_query, n=self._num_queries)
            )
            content = response.content if hasattr(response, "content") else str(response)
            text = content if isinstance(content, str) else str(content)
            # Gemini sometimes returns single-quoted JSON; normalize to double quotes
            text = text.strip()
            if text.startswith("[") and "'" in text:
                text = text.replace("'", '"')
            queries = json.loads(text)
            if isinstance(queries, list):
                return [str(q) for q in queries[: self._num_queries]]
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to generate alternative queries: {e}")

        return []

    def retrieve(self, query: str, alternative_queries: list[str] | None = None) -> list[Document]:
        """Run retrieval with original + alternative queries, deduplicate results.

        Args:
            query: Original search query.
            alternative_queries: Pre-generated alternative queries (if None, only uses original).

        Returns:
            Deduplicated list of documents from all queries.
        """
        all_queries = [query]
        if alternative_queries:
            all_queries.extend(alternative_queries)

        seen_ids: set[str] = set()
        merged: list[Document] = []

        for q in all_queries:
            try:
                docs = self._retriever.retrieve(q)
                for doc in docs:
                    doc_id = f"{doc.metadata.get('source', '')}:{doc.metadata.get('job_id', '')}"
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        merged.append(doc)
            except Exception as e:
                logger.warning(f"Retrieval failed for query '{q[:50]}...': {e}")

        logger.info(
            f"Multi-query: {len(all_queries)} queries → {len(merged)} unique docs"
        )
        return merged
