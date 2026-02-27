"""Tests for ChromaDB job embedder."""

import uuid

import chromadb
import pytest

from app.schemas.matching import JobPosting
from app.services.matching.embedder import JobEmbedder


class FakeEmbeddings:
    """Deterministic fake embeddings for testing."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t) % 10) / 10.0] * 384 for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text) % 10) / 10.0] * 384


@pytest.fixture
def fake_embeddings():
    return FakeEmbeddings()


@pytest.fixture
def embedder(fake_embeddings):
    """Create an embedder with a fresh ephemeral ChromaDB client and unique collection."""
    client = chromadb.EphemeralClient()
    # Use a unique collection name per test to avoid cross-test contamination
    unique_name = f"test_{uuid.uuid4().hex[:8]}"
    emb = JobEmbedder(
        embeddings=fake_embeddings,
        chroma_client=client,
    )
    # Override collection name to be unique
    emb.COLLECTION_NAME = unique_name
    emb._vectorstore = chromadb.__path__  # force re-init below

    # Re-initialize with unique name
    from langchain_chroma import Chroma

    emb._vectorstore = Chroma(
        client=client,
        collection_name=unique_name,
        embedding_function=fake_embeddings,
    )
    return emb


@pytest.fixture
def five_jobs(sample_jobs) -> list[JobPosting]:
    return sample_jobs[:5]


class TestIndexJobs:
    """Tests for job indexing."""

    def test_index_jobs_stores_documents(self, fake_embeddings, five_jobs):
        client = chromadb.EphemeralClient()
        name = f"test_{uuid.uuid4().hex[:8]}"
        embedder = _make_embedder(client, name, fake_embeddings)
        embedder.index_jobs(five_jobs)
        assert embedder.get_collection_count() == 5

    def test_index_jobs_stores_metadata(self, fake_embeddings, five_jobs):
        client = chromadb.EphemeralClient()
        name = f"test_{uuid.uuid4().hex[:8]}"
        embedder = _make_embedder(client, name, fake_embeddings)
        embedder.index_jobs(five_jobs)
        collection = client.get_or_create_collection(name)
        result = collection.get(include=["metadatas"])
        companies = {m["company"] for m in result["metadatas"]}
        assert "AI Startup Co" in companies
        assert "DataTech Inc" in companies

    def test_duplicate_job_not_reindexed(self, fake_embeddings, sample_jobs):
        client = chromadb.EphemeralClient()
        name = f"test_{uuid.uuid4().hex[:8]}"
        embedder = _make_embedder(client, name, fake_embeddings)
        job = sample_jobs[0]
        embedder.index_jobs([job])
        assert embedder.get_collection_count() == 1
        new_count = embedder.index_jobs([job])
        assert new_count == 0
        assert embedder.get_collection_count() == 1

    def test_index_returns_new_count(self, fake_embeddings, five_jobs):
        client = chromadb.EphemeralClient()
        name = f"test_{uuid.uuid4().hex[:8]}"
        embedder = _make_embedder(client, name, fake_embeddings)
        count = embedder.index_jobs(five_jobs)
        assert count == 5

    def test_incremental_indexing(self, fake_embeddings, sample_jobs):
        client = chromadb.EphemeralClient()
        name = f"test_{uuid.uuid4().hex[:8]}"
        embedder = _make_embedder(client, name, fake_embeddings)
        embedder.index_jobs(sample_jobs[:3])
        assert embedder.get_collection_count() == 3
        new_count = embedder.index_jobs(sample_jobs[3:6])
        assert new_count == 3
        assert embedder.get_collection_count() == 6


class TestSimilaritySearch:
    """Tests for similarity search."""

    def test_similarity_search_returns_results(self, fake_embeddings, five_jobs):
        client = chromadb.EphemeralClient()
        name = f"test_{uuid.uuid4().hex[:8]}"
        embedder = _make_embedder(client, name, fake_embeddings)
        embedder.index_jobs(five_jobs)
        results = embedder.similarity_search("Python backend engineer", k=3)
        assert len(results) <= 3
        assert len(results) > 0

    def test_similarity_search_returns_documents(self, fake_embeddings, five_jobs):
        client = chromadb.EphemeralClient()
        name = f"test_{uuid.uuid4().hex[:8]}"
        embedder = _make_embedder(client, name, fake_embeddings)
        embedder.index_jobs(five_jobs)
        results = embedder.similarity_search("software engineer", k=2)
        for doc in results:
            assert doc.page_content
            assert "job_id" in doc.metadata
            assert "company" in doc.metadata

    def test_empty_collection_search(self, fake_embeddings):
        client = chromadb.EphemeralClient()
        name = f"test_{uuid.uuid4().hex[:8]}"
        embedder = _make_embedder(client, name, fake_embeddings)
        results = embedder.similarity_search("anything", k=5)
        assert results == []


def _make_embedder(
    client: chromadb.ClientAPI,
    collection_name: str,
    embeddings: FakeEmbeddings,
) -> JobEmbedder:
    """Create an embedder with a unique collection name for test isolation."""
    from langchain_chroma import Chroma

    embedder = JobEmbedder.__new__(JobEmbedder)
    embedder.COLLECTION_NAME = collection_name
    embedder._client = client
    embedder._vectorstore = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings,
    )
    return embedder
