"""Greenhouse ATS direct API submission.

Submits applications directly via the Greenhouse Harvest API,
bypassing the need for browser automation.

API docs: https://developers.greenhouse.io/job-board.html#submit-application
"""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"


@dataclass
class GreenhouseSubmitResult:
    """Result of a Greenhouse API submission."""

    success: bool
    status_code: int
    message: str
    response_data: dict | None = None


class GreenhouseSubmitter:
    """Submits job applications via the Greenhouse Boards API."""

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    async def submit(
        self,
        board_token: str,
        job_id: str,
        fields: dict[str, str],
        resume_path: str | None = None,
    ) -> GreenhouseSubmitResult:
        """Submit an application to a Greenhouse job.

        Args:
            board_token: The company's Greenhouse board token.
            job_id: The Greenhouse job ID.
            fields: Form field values (first_name, last_name, email, etc.).
            resume_path: Optional path to resume file for upload.

        Returns:
            GreenhouseSubmitResult with success status.
        """
        url = f"{GREENHOUSE_API_BASE}/{board_token}/jobs/{job_id}"

        # Build multipart form data
        data: dict[str, str] = {}
        for key, value in fields.items():
            data[key] = value

        files = None
        if resume_path:
            try:
                with open(resume_path, "rb") as f:
                    file_content = f.read()
                files = {"resume": ("resume.pdf", file_content, "application/pdf")}
            except FileNotFoundError:
                logger.warning(f"Resume file not found: {resume_path}")

        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Basic {self._api_key}"

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    url,
                    data=data,
                    files=files,
                    headers=headers,
                    timeout=30.0,
                )

                if resp.status_code == 200:
                    return GreenhouseSubmitResult(
                        success=True,
                        status_code=200,
                        message="Application submitted successfully",
                        response_data=resp.json() if resp.content else None,
                    )
                else:
                    return GreenhouseSubmitResult(
                        success=False,
                        status_code=resp.status_code,
                        message=f"Submission failed: {resp.text}",
                        response_data=resp.json() if resp.content else None,
                    )
            except httpx.HTTPError as e:
                return GreenhouseSubmitResult(
                    success=False,
                    status_code=0,
                    message=f"HTTP error: {e}",
                )

    def build_payload(
        self,
        fields: dict[str, str],
        job_id: str,
    ) -> dict[str, str]:
        """Build the submission payload for validation/dry-run.

        Maps standard field names to Greenhouse API field names.

        Args:
            fields: User profile fields.
            job_id: Greenhouse job ID.

        Returns:
            Dict ready for form submission.
        """
        payload: dict[str, str] = {"id": job_id}

        field_mapping = {
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "email",
            "phone": "phone",
            "linkedin_url": "social_url_0",
            "website": "website_url",
            "location": "location",
        }

        for profile_key, api_key in field_mapping.items():
            if profile_key in fields:
                payload[api_key] = fields[profile_key]

        return payload
