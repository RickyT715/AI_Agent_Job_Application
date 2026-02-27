"""ChromaDB vector store management with Gemini embeddings.

Handles indexing job postings and performing similarity search.
"""

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.config import get_settings
from app.schemas.matching import JobPosting


def _job_to_document(job: JobPosting) -> Document:
    """Convert a JobPosting to a LangChain Document for indexing."""
    text_parts = [
        f"Title: {job.title}",
        f"Company: {job.company}",
    ]
    if job.location:
        text_parts.append(f"Location: {job.location}")
    if job.workplace_type:
        text_parts.append(f"Workplace: {job.workplace_type}")
    text_parts.append(f"Description: {job.description}")
    if job.requirements:
        text_parts.append(f"Requirements: {job.requirements}")

    return Document(
        page_content="\n".join(text_parts),
        metadata={
            "job_id": job.external_id,
            "source": job.source,
            "company": job.company,
            "title": job.title,
            "location": job.location or "",
            "workplace_type": job.workplace_type or "",
        },
    )


class JobEmbedder:
    """Manages ChromaDB vector store for job postings."""

    COLLECTION_NAME = "job_postings"

    def __init__(
        self,
        embeddings: Embeddings,
        chroma_client: chromadb.ClientAPI | None = None,
        persist_directory: str | None = None,
    ) -> None:
        if chroma_client is not None:
            self._client = chroma_client
        elif persist_directory:
            self._client = chromadb.PersistentClient(path=persist_directory)
        else:
            settings = get_settings()
            self._client = chromadb.PersistentClient(
                path=str(settings.chroma_db_dir),
            )

        self._vectorstore = Chroma(
            client=self._client,
            collection_name=self.COLLECTION_NAME,
            embedding_function=embeddings,
        )

    @property
    def vectorstore(self) -> Chroma:
        """Access the underlying Chroma vectorstore."""
        return self._vectorstore

    def get_collection_count(self) -> int:
        """Return the number of documents in the collection."""
        collection = self._client.get_or_create_collection(self.COLLECTION_NAME)
        return collection.count()

    def index_jobs(self, jobs: list[JobPosting]) -> int:
        """Index job postings into ChromaDB, skipping duplicates.

        Args:
            jobs: List of job postings to index.

        Returns:
            Number of newly indexed jobs.
        """
        collection = self._client.get_or_create_collection(self.COLLECTION_NAME)
        existing_ids = set(collection.get()["ids"])

        new_docs: list[Document] = []
        new_ids: list[str] = []

        for job in jobs:
            doc_id = f"{job.source}:{job.external_id}"
            if doc_id not in existing_ids:
                new_docs.append(_job_to_document(job))
                new_ids.append(doc_id)

        if new_docs:
            self._vectorstore.add_documents(new_docs, ids=new_ids)

        return len(new_docs)

    def similarity_search(self, query: str, k: int = 30) -> list[Document]:
        """Search for similar jobs using vector similarity.

        Args:
            query: The search query (typically resume text).
            k: Number of results to return.

        Returns:
            List of matching Documents sorted by similarity.
        """
        return self._vectorstore.similarity_search(query, k=k)
