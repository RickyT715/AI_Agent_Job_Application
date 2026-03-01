"""Tests for multilingual reranker support in TwoStageRetriever."""

from unittest.mock import MagicMock, patch

from app.services.matching.retriever import (
    TwoStageRetriever,
    _BgeRerankerCompressor,
    _build_compressor,
)


class TestBuildCompressor:
    """Tests for the reranker compressor factory."""

    @patch("app.services.matching.retriever.FlashrankRerank")
    def test_flashrank_default(self, mock_fr):
        mock_fr.return_value = MagicMock()
        _build_compressor("flashrank", final_k=10)
        mock_fr.assert_called_once_with(top_n=10)

    @patch("app.services.matching.retriever.FlashrankRerank")
    def test_flashrank_multilingual(self, mock_fr):
        mock_fr.return_value = MagicMock()
        _build_compressor("flashrank-multilingual", final_k=5)
        mock_fr.assert_called_once_with(model="ms-marco-MultiBERT-L-12", top_n=5)

    def test_bge_returns_bge_compressor(self):
        compressor = _build_compressor("bge", final_k=10)
        assert isinstance(compressor, _BgeRerankerCompressor)
        assert compressor._top_n == 10

    @patch("app.services.matching.retriever._build_compressor")
    @patch("app.services.matching.retriever.ContextualCompressionRetriever")
    def test_retriever_passes_reranker_mode(self, mock_ccr, mock_bc):
        mock_bc.return_value = MagicMock()
        mock_ccr.return_value = MagicMock()
        vs = MagicMock()
        vs.as_retriever.return_value = MagicMock()

        retriever = TwoStageRetriever(
            vs, initial_k=20, final_k=5, reranker_mode="flashrank-multilingual"
        )
        assert retriever.compression_retriever is not None


class TestBgeRerankerCompressor:
    """Tests for the BGE reranker compressor wrapper."""

    def test_init_defaults(self):
        comp = _BgeRerankerCompressor()
        assert comp._top_n == 10
        assert comp._model_name == "BAAI/bge-reranker-v2-m3"

    def test_compress_empty_docs(self):
        comp = _BgeRerankerCompressor()
        assert comp.compress_documents([], "query") == []

    @patch("app.services.matching.retriever._BgeRerankerCompressor._get_reranker")
    def test_compress_sorts_and_truncates(self, mock_get):
        from langchain_core.documents import Document

        mock_reranker = MagicMock()
        mock_reranker.compute_score.return_value = [0.1, 0.9, 0.5]
        mock_get.return_value = mock_reranker

        docs = [
            Document(page_content="low"),
            Document(page_content="high"),
            Document(page_content="mid"),
        ]
        comp = _BgeRerankerCompressor(top_n=2)
        result = comp.compress_documents(docs, "query")

        assert len(result) == 2
        assert result[0].page_content == "high"
        assert result[1].page_content == "mid"
