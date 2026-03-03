"""HTTP client for the external Resume Generator microservice."""

import logging
from pathlib import Path

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_resumes_dir() -> Path:
    """Return the resumes directory derived from settings.data_dir."""
    return get_settings().data_dir / "resumes"


class ResumeGeneratorError(Exception):
    """Error communicating with the resume generator service."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"ResumeGenerator {status_code}: {detail}")


class ResumeGeneratorClient:
    """Async client wrapping the resume-generator REST API."""

    def __init__(self, base_url: str | None = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or get_settings().resume_generator_url).rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the shared httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying httpx client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> dict:
        """GET /health — check if the service is reachable."""
        client = await self._get_client()
        resp = await client.get("/health")
        if resp.status_code != 200:
            raise ResumeGeneratorError(resp.status_code, resp.text)
        return resp.json()

    async def sync_user_info(self, resume_text: str) -> dict:
        """PUT /api/prompts/user_information — upload user resume text."""
        client = await self._get_client()
        resp = await client.put(
            "/api/prompts/user_information",
            json={"content": resume_text},
        )
        if resp.status_code not in (200, 201):
            raise ResumeGeneratorError(resp.status_code, resp.text)
        return resp.json()

    async def create_task(
        self,
        job_description: str,
        *,
        generate_cover_letter: bool = True,
        template_id: str | None = None,
        language: str = "en",
        experience_level: str = "mid",
        provider: str = "anthropic",
    ) -> dict:
        """POST /api/tasks — create a new generation task."""
        payload: dict = {
            "job_description": job_description,
            "generate_cover_letter": generate_cover_letter,
            "language": language,
            "experience_level": experience_level,
            "provider": provider,
        }
        if template_id:
            payload["template_id"] = template_id
        client = await self._get_client()
        resp = await client.post("/api/tasks", json=payload)
        if resp.status_code not in (200, 201):
            raise ResumeGeneratorError(resp.status_code, resp.text)
        return resp.json()

    async def start_pipeline(self, task_id: str) -> dict:
        """POST /api/tasks/{id}/start-v3 — kick off the LangGraph pipeline."""
        client = await self._get_client()
        resp = await client.post(f"/api/tasks/{task_id}/start-v3")
        if resp.status_code not in (200, 202):
            raise ResumeGeneratorError(resp.status_code, resp.text)
        return resp.json()

    async def get_task_status(self, task_id: str) -> dict:
        """GET /api/tasks/{id} — poll task status."""
        client = await self._get_client()
        resp = await client.get(f"/api/tasks/{task_id}")
        if resp.status_code != 200:
            raise ResumeGeneratorError(resp.status_code, resp.text)
        return resp.json()

    async def download_resume_pdf(self, task_id: str) -> bytes:
        """GET /api/tasks/{id}/resume — download resume PDF bytes."""
        client = await self._get_client()
        resp = await client.get(f"/api/tasks/{task_id}/resume")
        if resp.status_code != 200:
            raise ResumeGeneratorError(resp.status_code, resp.text)
        return resp.content

    async def download_cover_letter_pdf(self, task_id: str) -> bytes:
        """GET /api/tasks/{id}/cover-letter — download cover letter PDF bytes."""
        client = await self._get_client()
        resp = await client.get(f"/api/tasks/{task_id}/cover-letter")
        if resp.status_code != 200:
            raise ResumeGeneratorError(resp.status_code, resp.text)
        return resp.content

    async def get_cover_letter_text(self, task_id: str) -> str:
        """GET /api/tasks/{id}/cover-letter-text — get cover letter plain text."""
        client = await self._get_client()
        resp = await client.get(f"/api/tasks/{task_id}/cover-letter-text")
        if resp.status_code != 200:
            raise ResumeGeneratorError(resp.status_code, resp.text)
        data = resp.json()
        return data.get("content", data.get("text", ""))

    async def create_and_start(
        self,
        job_description: str,
        *,
        generate_cover_letter: bool = True,
        template_id: str | None = None,
        language: str = "en",
        experience_level: str = "mid",
        provider: str = "anthropic",
    ) -> dict:
        """Convenience: create task -> start pipeline -> return task with id."""
        task = await self.create_task(
            job_description,
            generate_cover_letter=generate_cover_letter,
            template_id=template_id,
            language=language,
            experience_level=experience_level,
            provider=provider,
        )
        task_id = task["id"]
        await self.start_pipeline(str(task_id))
        return await self.get_task_status(str(task_id))


def save_pdf_to_disk(content: bytes, filename: str) -> Path:
    """Save PDF bytes to the resumes directory and return the path."""
    resumes_dir = _get_resumes_dir()
    resumes_dir.mkdir(parents=True, exist_ok=True)
    path = resumes_dir / filename
    path.write_bytes(content)
    return path
