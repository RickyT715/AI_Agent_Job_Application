"""Tests for the config/preferences API router."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from httpx import AsyncClient

from app.config import Settings


class TestPreferences:
    """Tests for preferences endpoints."""

    async def test_get_preferences(self, client: AsyncClient):
        resp = await client.get("/api/config/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert "job_titles" in data
        assert "locations" in data
        assert "weights" in data

    async def test_update_preferences(self, client: AsyncClient):
        # Create a temp YAML file to avoid modifying real config
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump({"job_titles": ["Engineer"], "experience_level": "mid"}, f)
            tmp_path = Path(f.name)

        mock_settings = Settings(user_config_path=tmp_path)
        with patch("app.routers.config.get_settings", return_value=mock_settings):
            resp = await client.put(
                "/api/config/preferences",
                json={"job_titles": ["ML Engineer", "Data Engineer"]},
            )
        assert resp.status_code == 200
        assert "ML Engineer" in resp.json()["job_titles"]
        tmp_path.unlink()

    async def test_reject_invalid_preferences(self, client: AsyncClient):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump({"experience_level": "mid"}, f)
            tmp_path = Path(f.name)

        mock_settings = Settings(user_config_path=tmp_path)
        with patch("app.routers.config.get_settings", return_value=mock_settings):
            resp = await client.put(
                "/api/config/preferences",
                json={
                    "weights": {
                        "skills": 0.9,
                        "experience": 0.9,
                        "education": 0.9,
                        "location": 0.9,
                        "salary": 0.9,
                    }
                },
            )
        assert resp.status_code == 422
        tmp_path.unlink()


class TestResumeUpload:
    """Tests for resume upload."""

    async def test_upload_resume(self, client: AsyncClient):
        resp = await client.post(
            "/api/config/resume",
            files={"file": ("resume.txt", b"John Doe\nSoftware Engineer\n5 years experience")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Resume uploaded successfully"
        assert data["character_count"] > 0
