"""Lever ATS direct API submission.

Submits applications via Lever's postings API.
API docs: https://github.com/lever/postings-api
"""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

LEVER_API_BASE = "https://api.lever.co/v0/postings"


@dataclass
class LeverSubmitResult:
    """Result of a Lever API submission."""

    success: bool
    status_code: int
    message: str
    application_id: str | None = None


class LeverSubmitter:
    """Submits job applications via the Lever Postings API."""

    async def submit(
        self,
        company: str,
        posting_id: str,
        fields: dict[str, str],
        resume_path: str | None = None,
    ) -> LeverSubmitResult:
        """Submit an application to a Lever job posting.

        Args:
            company: The Lever company slug.
            posting_id: The Lever posting ID.
            fields: Form field values.
            resume_path: Optional path to resume file.

        Returns:
            LeverSubmitResult with success status.
        """
        url = f"{LEVER_API_BASE}/{company}/{posting_id}/apply"

        data = self.build_payload(fields)

        files = None
        if resume_path:
            try:
                with open(resume_path, "rb") as f:
                    file_content = f.read()
                files = {"resume": ("resume.pdf", file_content, "application/pdf")}
            except FileNotFoundError:
                logger.warning(f"Resume file not found: {resume_path}")

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    url,
                    data=data,
                    files=files,
                    timeout=30.0,
                )

                if resp.status_code == 200:
                    resp_data = resp.json() if resp.content else {}
                    return LeverSubmitResult(
                        success=True,
                        status_code=200,
                        message="Application submitted successfully",
                        application_id=resp_data.get("applicationId"),
                    )
                else:
                    return LeverSubmitResult(
                        success=False,
                        status_code=resp.status_code,
                        message=f"Submission failed: {resp.text}",
                    )
            except httpx.HTTPError as e:
                return LeverSubmitResult(
                    success=False,
                    status_code=0,
                    message=f"HTTP error: {e}",
                )

    def build_payload(self, fields: dict[str, str]) -> dict[str, str]:
        """Build the submission payload for Lever's API.

        Args:
            fields: User profile fields.

        Returns:
            Dict ready for form submission.
        """
        payload: dict[str, str] = {}

        field_mapping = {
            "first_name": "name",  # Lever uses single "name" field
            "email": "email",
            "phone": "phone",
            "linkedin_url": "urls[LinkedIn]",
            "website": "urls[Portfolio]",
            "location": "location",
        }

        # Handle name: combine first + last
        first = fields.get("first_name", "")
        last = fields.get("last_name", "")
        if first or last:
            payload["name"] = f"{first} {last}".strip()

        for profile_key, api_key in field_mapping.items():
            if profile_key in fields and api_key not in payload:
                payload[api_key] = fields[profile_key]

        return payload
