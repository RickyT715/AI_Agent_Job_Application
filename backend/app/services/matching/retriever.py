"""Two-stage retrieval: vector similarity + cross-encoder reranking.

Stage 1: ChromaDB cosine similarity -> top-k candidates
Stage 2: Cross-encoder reranking -> top-n final candidates

Supports multiple reranker backends:
- ``"flashrank"`` — default English FlashRank (fast, ~50 MB)
- ``"flashrank-multilingual"`` — FlashRank MultiBERT for Chinese (~150 MB)
- ``"bge"`` — BAAI bge-reranker-v2-m3 via HuggingFace (best quality, ~1 GB)
- ``"auto"`` — picks ``bge`` when language is Chinese, ``flashrank`` otherwise
"""

import logging

from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import FlashrankRerank
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

logger = logging.getLogger(__name__)


def compute_dynamic_k(
    collection_size: int,
    initial_k_ratio: float = 0.3,
    final_k_ratio: float = 0.1,
    min_initial_k: int = 20,
    max_initial_k: int = 200,
    min_final_k: int = 5,
    max_final_k: int = 50,
) -> tuple[int, int]:
    """Scale retrieval k proportionally to collection size.

    Examples:
        20 jobs -> (20, 5)
        100 jobs -> (30, 10)
        500 jobs -> (150, 50)
        1000+ jobs -> (200, 50)
    """
    initial_k = max(min_initial_k, min(max_initial_k, int(collection_size * initial_k_ratio)))
    final_k = max(min_final_k, min(max_final_k, int(collection_size * final_k_ratio)))
    # final_k can't exceed initial_k
    final_k = min(final_k, initial_k)
    return initial_k, final_k


def _build_compressor(reranker_mode: str, final_k: int):
    """Build the appropriate reranker compressor based on mode.

    Args:
        reranker_mode: One of ``"flashrank"``, ``"flashrank-multilingual"``,
                       ``"bge"``, or ``"auto"``.
        final_k: Number of top documents to keep after reranking.

    Returns:
        A LangChain document compressor instance.
    """
    if reranker_mode == "bge":
        return _BgeRerankerCompressor(
            model_name="BAAI/bge-reranker-v2-m3", top_n=final_k,
        )

    if reranker_mode == "flashrank-multilingual":
        return FlashrankRerank(model="ms-marco-MultiBERT-L-12", top_n=final_k)

    # Default: English FlashRank
    return FlashrankRerank(top_n=final_k)


class _BgeRerankerCompressor:
    """Lightweight LangChain-compatible document compressor using FlagReranker.

    Wraps ``FlagEmbedding.FlagReranker`` so it can be used as a drop-in
    replacement for ``FlashrankRerank`` in ``ContextualCompressionRetriever``.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", top_n: int = 10) -> None:
        self._top_n = top_n
        self._model_name = model_name
        self._reranker = None  # lazy init

    def _get_reranker(self):
        if self._reranker is None:
            from FlagEmbedding import FlagReranker
            self._reranker = FlagReranker(self._model_name, use_fp16=False)
        return self._reranker

    def compress_documents(self, documents: list[Document], query: str, **kwargs) -> list[Document]:
        """Rerank documents using BGE cross-encoder and return top_n."""
        if not documents:
            return []
        reranker = self._get_reranker()
        pairs = [[query, doc.page_content] for doc in documents]
        scores = reranker.compute_score(pairs)
        if isinstance(scores, float):
            scores = [scores]

        scored_docs = list(zip(scores, documents))
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[: self._top_n]]


class TwoStageRetriever:
    """Combines vector retrieval with cross-encoder reranking."""

    def __init__(
        self,
        vectorstore: VectorStore,
        initial_k: int = 30,
        final_k: int = 10,
        reranker_mode: str = "flashrank",
    ) -> None:
        self._vectorstore = vectorstore
        self._initial_k = initial_k
        self._final_k = final_k

        # Base retriever: vector similarity search
        self._base_retriever = vectorstore.as_retriever(
            search_kwargs={"k": initial_k},
        )

        # Build reranker based on mode
        self._reranker = _build_compressor(reranker_mode, final_k)

        # Combined retriever: base -> rerank
        self._compression_retriever = ContextualCompressionRetriever(
            base_compressor=self._reranker,
            base_retriever=self._base_retriever,
        )

    @property
    def base_retriever(self):
        """Access the base vector retriever."""
        return self._base_retriever

    @property
    def compression_retriever(self) -> ContextualCompressionRetriever:
        """Access the full compression retriever."""
        return self._compression_retriever

    def retrieve(self, query: str) -> list[Document]:
        """Run two-stage retrieval.

        Args:
            query: Search query (typically resume text or summary).

        Returns:
            Top-k reranked documents.
        """
        return self._compression_retriever.invoke(query)
