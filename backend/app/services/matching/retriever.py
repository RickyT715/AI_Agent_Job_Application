"""Two-stage retrieval: vector similarity + FlashRank reranking.

Stage 1: ChromaDB cosine similarity → top-30 candidates
Stage 2: FlashRank cross-encoder reranking → top-10 final candidates
"""

from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import FlashrankRerank
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore


class TwoStageRetriever:
    """Combines vector retrieval with FlashRank reranking."""

    def __init__(
        self,
        vectorstore: VectorStore,
        initial_k: int = 30,
        final_k: int = 10,
    ) -> None:
        self._vectorstore = vectorstore
        self._initial_k = initial_k
        self._final_k = final_k

        # Base retriever: vector similarity search
        self._base_retriever = vectorstore.as_retriever(
            search_kwargs={"k": initial_k},
        )

        # FlashRank reranker: narrows candidates using cross-encoder
        self._reranker = FlashrankRerank(top_n=final_k)

        # Combined retriever: base → rerank
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
