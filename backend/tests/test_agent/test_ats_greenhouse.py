"""Tests for Greenhouse ATS direct API submission."""

from pytest_httpx import HTTPXMock

from app.services.agent.ats.greenhouse import GreenhouseSubmitter


class TestGreenhouseSubmitter:
    """Tests for Greenhouse API submission."""

    async def test_submit_sends_to_correct_url(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="https://boards-api.greenhouse.io/v1/boards/testco/jobs/12345",
            status_code=200,
            json={"status": "ok"},
        )
        submitter = GreenhouseSubmitter()
        result = await submitter.submit(
            board_token="testco",
            job_id="12345",
            fields={"first_name": "John", "email": "john@test.com"},
        )
        assert result.success is True
        assert result.status_code == 200

    async def test_submit_returns_success(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=200, json={"id": "app-123"})
        submitter = GreenhouseSubmitter()
        result = await submitter.submit(
            board_token="co", job_id="1", fields={"email": "test@test.com"},
        )
        assert result.success is True
        assert result.message == "Application submitted successfully"

    async def test_submit_handles_400(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            status_code=400,
            json={"errors": ["Email is required"]},
        )
        submitter = GreenhouseSubmitter()
        result = await submitter.submit(
            board_token="co", job_id="1", fields={},
        )
        assert result.success is False
        assert result.status_code == 400

    async def test_auth_header_included(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=200, json={})
        submitter = GreenhouseSubmitter(api_key="test-key-123")
        await submitter.submit(
            board_token="co", job_id="1", fields={"email": "x@x.com"},
        )
        request = httpx_mock.get_request()
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Basic test-key-123"


class TestGreenhousePayload:
    """Tests for payload building."""

    def test_build_payload_maps_standard_fields(self):
        submitter = GreenhouseSubmitter()
        payload = submitter.build_payload(
            fields={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "phone": "555-1234",
                "linkedin_url": "https://linkedin.com/in/johndoe",
            },
            job_id="12345",
        )
        assert payload["id"] == "12345"
        assert payload["first_name"] == "John"
        assert payload["last_name"] == "Doe"
        assert payload["email"] == "john@test.com"
        assert payload["social_url_0"] == "https://linkedin.com/in/johndoe"

    def test_build_payload_skips_missing_fields(self):
        submitter = GreenhouseSubmitter()
        payload = submitter.build_payload(
            fields={"email": "john@test.com"},
            job_id="99",
        )
        assert "first_name" not in payload
        assert "phone" not in payload
        assert payload["email"] == "john@test.com"
