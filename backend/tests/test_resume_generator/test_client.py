"""Tests for the ResumeGeneratorClient."""

import pytest
from pytest_httpx import HTTPXMock

from app.services.resume_generator.client import (
    ResumeGeneratorClient,
    ResumeGeneratorError,
    save_pdf_to_disk,
)

BASE = "http://resume-gen:8000"


@pytest.fixture
def client():
    return ResumeGeneratorClient(base_url=BASE)


class TestInit:
    def test_strips_trailing_slash(self):
        c = ResumeGeneratorClient(base_url="http://example.com/")
        assert c.base_url == "http://example.com"

    def test_stores_base_url(self):
        c = ResumeGeneratorClient(base_url=BASE)
        assert c.base_url == BASE


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_success(self, client, httpx_mock: HTTPXMock, health_response):
        httpx_mock.add_response(url=f"{BASE}/health", json=health_response)
        result = await client.health_check()
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_failure(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=f"{BASE}/health", status_code=500, text="down")
        with pytest.raises(ResumeGeneratorError) as exc_info:
            await client.health_check()
        assert exc_info.value.status_code == 500


class TestSyncUserInfo:
    @pytest.mark.asyncio
    async def test_success(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/api/prompts/user_information",
            json={"status": "updated"},
        )
        result = await client.sync_user_info("My resume text")
        assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_error(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/api/prompts/user_information",
            status_code=400,
            text="bad request",
        )
        with pytest.raises(ResumeGeneratorError):
            await client.sync_user_info("")


class TestCreateTask:
    @pytest.mark.asyncio
    async def test_success(self, client, httpx_mock: HTTPXMock, sample_task_response):
        httpx_mock.add_response(url=f"{BASE}/api/tasks", json=sample_task_response)
        result = await client.create_task("Build microservices")
        assert result["id"] == "task-abc-123"

    @pytest.mark.asyncio
    async def test_with_template(self, client, httpx_mock: HTTPXMock, sample_task_response):
        httpx_mock.add_response(url=f"{BASE}/api/tasks", json=sample_task_response)
        result = await client.create_task("JD", template_id="modern")
        assert result["id"] == "task-abc-123"

    @pytest.mark.asyncio
    async def test_error(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=f"{BASE}/api/tasks", status_code=422, text="invalid")
        with pytest.raises(ResumeGeneratorError):
            await client.create_task("JD")


class TestStartPipeline:
    @pytest.mark.asyncio
    async def test_success(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/start-v3",
            json={"status": "started"},
        )
        result = await client.start_pipeline("task-abc-123")
        assert result["status"] == "started"

    @pytest.mark.asyncio
    async def test_error(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/start-v3",
            status_code=404,
            text="not found",
        )
        with pytest.raises(ResumeGeneratorError):
            await client.start_pipeline("task-abc-123")


class TestGetTaskStatus:
    @pytest.mark.asyncio
    async def test_success(self, client, httpx_mock: HTTPXMock, completed_task_response):
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123",
            json=completed_task_response,
        )
        result = await client.get_task_status("task-abc-123")
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_error(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123",
            status_code=404,
            text="not found",
        )
        with pytest.raises(ResumeGeneratorError):
            await client.get_task_status("task-abc-123")


class TestDownloadResumePdf:
    @pytest.mark.asyncio
    async def test_success(self, client, httpx_mock: HTTPXMock):
        pdf_bytes = b"%PDF-1.4 fake resume content"
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/resume",
            content=pdf_bytes,
        )
        result = await client.download_resume_pdf("task-abc-123")
        assert result == pdf_bytes

    @pytest.mark.asyncio
    async def test_error(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/resume",
            status_code=404,
            text="no resume",
        )
        with pytest.raises(ResumeGeneratorError):
            await client.download_resume_pdf("task-abc-123")


class TestDownloadCoverLetterPdf:
    @pytest.mark.asyncio
    async def test_success(self, client, httpx_mock: HTTPXMock):
        pdf_bytes = b"%PDF-1.4 fake cover letter"
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/cover-letter",
            content=pdf_bytes,
        )
        result = await client.download_cover_letter_pdf("task-abc-123")
        assert result == pdf_bytes


class TestGetCoverLetterText:
    @pytest.mark.asyncio
    async def test_success_content_key(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/cover-letter-text",
            json={"content": "Dear Hiring Manager..."},
        )
        result = await client.get_cover_letter_text("task-abc-123")
        assert result == "Dear Hiring Manager..."

    @pytest.mark.asyncio
    async def test_success_text_key(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/cover-letter-text",
            json={"text": "Dear Hiring Manager..."},
        )
        result = await client.get_cover_letter_text("task-abc-123")
        assert result == "Dear Hiring Manager..."

    @pytest.mark.asyncio
    async def test_error(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/cover-letter-text",
            status_code=404,
            text="not found",
        )
        with pytest.raises(ResumeGeneratorError):
            await client.get_cover_letter_text("task-abc-123")


class TestCreateAndStart:
    @pytest.mark.asyncio
    async def test_success(self, client, httpx_mock: HTTPXMock, sample_task_response, completed_task_response):
        # create_task
        httpx_mock.add_response(url=f"{BASE}/api/tasks", json=sample_task_response)
        # start_pipeline
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/start-v3",
            json={"status": "started"},
        )
        # get_task_status
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123",
            json=completed_task_response,
        )
        result = await client.create_and_start("Senior Python dev needed")
        assert result["status"] == "completed"


class TestCreateAndStartErrorPropagation:
    @pytest.mark.asyncio
    async def test_create_task_failure_propagates(self, client, httpx_mock: HTTPXMock):
        """If create_task fails, create_and_start should raise."""
        httpx_mock.add_response(url=f"{BASE}/api/tasks", status_code=500, text="server error")
        with pytest.raises(ResumeGeneratorError) as exc_info:
            await client.create_and_start("Some JD")
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_start_pipeline_failure_propagates(self, client, httpx_mock: HTTPXMock, sample_task_response):
        """If start_pipeline fails, create_and_start should raise."""
        httpx_mock.add_response(url=f"{BASE}/api/tasks", json=sample_task_response)
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/start-v3",
            status_code=500,
            text="pipeline error",
        )
        with pytest.raises(ResumeGeneratorError) as exc_info:
            await client.create_and_start("Some JD")
        assert exc_info.value.status_code == 500


class TestCustomTimeout:
    def test_custom_timeout_stored(self):
        c = ResumeGeneratorClient(base_url=BASE, timeout=30.0)
        assert c.timeout == 30.0

    def test_default_timeout(self):
        c = ResumeGeneratorClient(base_url=BASE)
        assert c.timeout == 120.0


class TestCreateTaskAllParams:
    @pytest.mark.asyncio
    async def test_all_optional_params(self, client, httpx_mock: HTTPXMock, sample_task_response):
        httpx_mock.add_response(url=f"{BASE}/api/tasks", json=sample_task_response)
        result = await client.create_task(
            "Build microservices",
            generate_cover_letter=False,
            template_id="academic",
            language="zh",
            experience_level="senior",
            provider="openai",
        )
        assert result["id"] == "task-abc-123"

    @pytest.mark.asyncio
    async def test_no_cover_letter(self, client, httpx_mock: HTTPXMock, sample_task_response):
        httpx_mock.add_response(url=f"{BASE}/api/tasks", json=sample_task_response)
        result = await client.create_task("JD", generate_cover_letter=False)
        assert result["id"] == "task-abc-123"


class TestDownloadCoverLetterPdfError:
    @pytest.mark.asyncio
    async def test_error(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/cover-letter",
            status_code=404,
            text="no cover letter",
        )
        with pytest.raises(ResumeGeneratorError):
            await client.download_cover_letter_pdf("task-abc-123")


class TestCoverLetterTextEmptyResponse:
    @pytest.mark.asyncio
    async def test_empty_keys(self, client, httpx_mock: HTTPXMock):
        """When neither content nor text key exists, returns empty string."""
        httpx_mock.add_response(
            url=f"{BASE}/api/tasks/task-abc-123/cover-letter-text",
            json={"other": "data"},
        )
        result = await client.get_cover_letter_text("task-abc-123")
        assert result == ""


class TestResumeGeneratorErrorRepr:
    def test_str_representation(self):
        err = ResumeGeneratorError(502, "Bad Gateway")
        assert "502" in str(err)
        assert "Bad Gateway" in str(err)

    def test_attributes(self):
        err = ResumeGeneratorError(404, "Not Found")
        assert err.status_code == 404
        assert err.detail == "Not Found"


class TestSyncUserInfoCreated:
    @pytest.mark.asyncio
    async def test_201_accepted(self, client, httpx_mock: HTTPXMock):
        """sync_user_info should accept 201 status code too."""
        httpx_mock.add_response(
            url=f"{BASE}/api/prompts/user_information",
            status_code=201,
            json={"status": "created"},
        )
        result = await client.sync_user_info("My resume")
        assert result["status"] == "created"


class TestSavePdfToDisk:
    def test_saves_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "app.services.resume_generator.client._get_resumes_dir", lambda: tmp_path
        )
        content = b"%PDF-1.4 test content"
        path = save_pdf_to_disk(content, "test-resume.pdf")
        assert path.exists()
        assert path.read_bytes() == content
        assert path.name == "test-resume.pdf"

    def test_creates_directory(self, tmp_path, monkeypatch):
        target_dir = tmp_path / "nested" / "dir"
        monkeypatch.setattr(
            "app.services.resume_generator.client._get_resumes_dir", lambda: target_dir
        )
        save_pdf_to_disk(b"pdf", "out.pdf")
        assert (target_dir / "out.pdf").exists()

    def test_overwrites_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "app.services.resume_generator.client._get_resumes_dir", lambda: tmp_path
        )
        save_pdf_to_disk(b"old", "file.pdf")
        save_pdf_to_disk(b"new", "file.pdf")
        assert (tmp_path / "file.pdf").read_bytes() == b"new"
