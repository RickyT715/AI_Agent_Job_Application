"""Tests for upload size limits on resume and linkedin-profile endpoints."""

import pytest
from httpx import AsyncClient


class TestUploadSizeLimits:
    """Tests for 10MB upload size limit on config endpoints."""

    async def test_resume_upload_within_limit(self, client: AsyncClient):
        """A small text resume upload succeeds."""
        content = b"This is my resume text content."
        resp = await client.post(
            "/api/config/resume",
            files={"file": ("resume.txt", content, "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Resume uploaded successfully"
        assert data["character_count"] == len(content.decode("utf-8"))

    async def test_resume_upload_exceeds_limit(self, client: AsyncClient):
        """Resume upload over 10MB returns 413."""
        # Create content slightly over 10MB
        content = b"X" * (10 * 1024 * 1024 + 1)
        resp = await client.post(
            "/api/config/resume",
            files={"file": ("resume.txt", content, "text/plain")},
        )
        assert resp.status_code == 413
        assert "File too large" in resp.json()["detail"]

    async def test_resume_upload_exactly_at_limit(self, client: AsyncClient):
        """Resume upload at exactly 10MB succeeds."""
        content = b"A" * (10 * 1024 * 1024)
        resp = await client.post(
            "/api/config/resume",
            files={"file": ("resume.txt", content, "text/plain")},
        )
        assert resp.status_code == 200

    async def test_linkedin_upload_exceeds_limit(self, client: AsyncClient):
        """LinkedIn PDF upload over 10MB returns 413."""
        content = b"X" * (10 * 1024 * 1024 + 1)
        resp = await client.post(
            "/api/config/linkedin-profile",
            files={"file": ("profile.pdf", content, "application/pdf")},
        )
        assert resp.status_code == 413
        assert "File too large" in resp.json()["detail"]

    async def test_resume_upload_no_file_provided(self, client: AsyncClient):
        """Resume upload without a filename returns an error (400 or 422)."""
        resp = await client.post(
            "/api/config/resume",
            files={"file": ("", b"", "text/plain")},
        )
        assert resp.status_code in (400, 422)

    async def test_linkedin_requires_pdf(self, client: AsyncClient):
        """LinkedIn endpoint rejects non-PDF files."""
        resp = await client.post(
            "/api/config/linkedin-profile",
            files={"file": ("profile.txt", b"some text", "text/plain")},
        )
        assert resp.status_code == 400
        assert "PDF" in resp.json()["detail"]
