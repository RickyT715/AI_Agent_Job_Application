"""Tests for two-stage retrieval (vector + FlashRank reranking)."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.services.matching.retriever import TwoStageRetriever


def _make_docs(n: int) -> list[Document]:
    """Create n dummy documents with metadata."""
    return [
        Document(
            page_content=f"Job posting {i}: Software Engineer at Company{i}",
            metadata={"job_id": f"job-{i:03d}", "source": "test", "company": f"Company{i}"},
        )
        for i in range(n)
    ]


@pytest.fixture
def mock_vectorstore():
    """Create a mock vectorstore that returns configurable results."""
    vs = MagicMock()
    retriever = MagicMock()
    retriever.invoke.return_value = _make_docs(30)
    vs.as_retriever.return_value = retriever
    return vs


@pytest.fixture(autouse=True)
def _patch_deps():
    """Patch FlashrankRerank and ContextualCompressionRetriever for all tests."""
    with (
        patch("app.services.matching.retriever.FlashrankRerank") as mock_fr,
        patch("app.services.matching.retriever.ContextualCompressionRetriever") as mock_ccr,
    ):
        mock_fr.return_value = MagicMock()
        mock_ccr.return_value = MagicMock()
        yield {"flashrank": mock_fr, "ccr": mock_ccr}


class TestTwoStageRetriever:
    """Tests for the two-stage retriever."""

    def test_base_retriever_created_with_k(self, mock_vectorstore):
        TwoStageRetriever(mock_vectorstore, initial_k=30, final_k=10)
        mock_vectorstore.as_retriever.assert_called_once_with(search_kwargs={"k": 30})

    def test_compression_retriever_exists(self, mock_vectorstore):
        retriever = TwoStageRetriever(mock_vectorstore, initial_k=30, final_k=10)
        assert retriever.compression_retriever is not None

    def test_base_retriever_accessible(self, mock_vectorstore):
        retriever = TwoStageRetriever(mock_vectorstore)
        assert retriever.base_retriever is not None

    def test_reranker_configured_with_top_n(self, mock_vectorstore, _patch_deps):
        TwoStageRetriever(mock_vectorstore, initial_k=30, final_k=10)
        _patch_deps["flashrank"].assert_called_once_with(top_n=10)

    def test_retrieve_invokes_compression_retriever(self, mock_vectorstore, _patch_deps):
        mock_cr_instance = MagicMock()
        mock_cr_instance.invoke.return_value = _make_docs(10)
        _patch_deps["ccr"].return_value = mock_cr_instance

        retriever = TwoStageRetriever(mock_vectorstore, initial_k=30, final_k=10)
        results = retriever.retrieve("Python engineer resume")

        mock_cr_instance.invoke.assert_called_once_with("Python engineer resume")
        assert len(results) == 10

    def test_retrieve_returns_documents(self, mock_vectorstore, _patch_deps):
        expected_docs = _make_docs(5)
        mock_cr_instance = MagicMock()
        mock_cr_instance.invoke.return_value = expected_docs
        _patch_deps["ccr"].return_value = mock_cr_instance

        retriever = TwoStageRetriever(mock_vectorstore, initial_k=30, final_k=5)
        results = retriever.retrieve("query")

        assert results == expected_docs
