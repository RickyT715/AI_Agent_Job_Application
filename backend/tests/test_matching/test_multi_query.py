"""Tests for multi-query retrieval."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.documents import Document

from app.services.matching.multi_query import MultiQueryRetriever


def _make_doc(job_id: str, source: str = "test") -> Document:
    return Document(
        page_content=f"Job {job_id}",
        metadata={"job_id": job_id, "source": source},
    )


@pytest.fixture
def mock_retriever():
    retriever = MagicMock()
    retriever.retrieve.return_value = [_make_doc("job-001"), _make_doc("job-002")]
    return retriever


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    response = MagicMock()
    response.content = '["query alt 1", "query alt 2", "query alt 3"]'
    llm.ainvoke = AsyncMock(return_value=response)
    return llm


class TestMultiQueryRetriever:
    """Tests for MultiQueryRetriever."""

    async def test_generate_queries_returns_list(self, mock_retriever, mock_llm):
        mq = MultiQueryRetriever(retriever=mock_retriever, llm=mock_llm)
        queries = await mq.generate_queries("Python engineer")
        assert isinstance(queries, list)
        assert len(queries) == 3

    async def test_generate_queries_handles_bad_json(self, mock_retriever):
        llm = MagicMock()
        response = MagicMock()
        response.content = "Not valid JSON"
        llm.ainvoke = AsyncMock(return_value=response)

        mq = MultiQueryRetriever(retriever=mock_retriever, llm=llm)
        queries = await mq.generate_queries("Python engineer")
        assert queries == []

    async def test_generate_queries_limits_count(self, mock_retriever, mock_llm):
        mq = MultiQueryRetriever(retriever=mock_retriever, llm=mock_llm, num_queries=2)
        queries = await mq.generate_queries("test")
        assert len(queries) <= 2

    def test_retrieve_original_only(self, mock_retriever, mock_llm):
        mq = MultiQueryRetriever(retriever=mock_retriever, llm=mock_llm)
        docs = mq.retrieve("original query")
        assert len(docs) == 2

    def test_retrieve_deduplicates(self, mock_retriever, mock_llm):
        """Same docs returned for multiple queries should be deduplicated."""
        mq = MultiQueryRetriever(retriever=mock_retriever, llm=mock_llm)
        docs = mq.retrieve("query", alternative_queries=["alt1", "alt2"])
        # All 3 queries return the same 2 docs, should be deduplicated
        assert len(docs) == 2

    def test_retrieve_merges_different_docs(self, mock_llm):
        retriever = MagicMock()
        # Return different docs for different calls
        retriever.retrieve.side_effect = [
            [_make_doc("job-001")],
            [_make_doc("job-002")],
        ]
        mq = MultiQueryRetriever(retriever=retriever, llm=mock_llm)
        docs = mq.retrieve("query", alternative_queries=["alt1"])
        assert len(docs) == 2

    def test_retrieve_handles_error(self, mock_llm):
        retriever = MagicMock()
        retriever.retrieve.side_effect = Exception("Retrieval error")
        mq = MultiQueryRetriever(retriever=retriever, llm=mock_llm)
        # Should not raise, just return empty
        docs = mq.retrieve("query")
        assert docs == []
