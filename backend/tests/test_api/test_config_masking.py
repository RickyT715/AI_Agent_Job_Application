"""Tests for sensitive field masking in the config preferences endpoint."""

import tempfile
from pathlib import Path

import yaml
from httpx import AsyncClient

from app.config import get_settings, reset_settings


class TestSensitiveFieldMasking:
    """Test that sensitive fields are masked in GET /api/config/preferences."""

    async def test_alibaba_key_masked_when_set(self, client: AsyncClient, tmp_path: Path):
        """alibaba_app_key should be '***' when a value is configured."""
        config_data = {
            "job_titles": ["Engineer"],
            "locations": ["Remote"],
            "alibaba_app_key": "my-secret-alibaba-key-12345",
            "boss_zhipin_cookie": "",
        }
        config_file = tmp_path / "user_config.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        settings = get_settings()
        original_path = settings.user_config_path
        try:
            settings.user_config_path = config_file
            resp = await client.get("/api/config/preferences")
        finally:
            settings.user_config_path = original_path

        assert resp.status_code == 200
        data = resp.json()
        assert data["alibaba_app_key"] == "***"

    async def test_boss_cookie_masked_when_set(self, client: AsyncClient, tmp_path: Path):
        """boss_zhipin_cookie should be '***' when a value is configured."""
        config_data = {
            "job_titles": ["Engineer"],
            "locations": ["Remote"],
            "alibaba_app_key": "",
            "boss_zhipin_cookie": "session-cookie-abc123-secret",
        }
        config_file = tmp_path / "user_config.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        settings = get_settings()
        original_path = settings.user_config_path
        try:
            settings.user_config_path = config_file
            resp = await client.get("/api/config/preferences")
        finally:
            settings.user_config_path = original_path

        assert resp.status_code == 200
        data = resp.json()
        assert data["boss_zhipin_cookie"] == "***"

    async def test_empty_secrets_not_masked(self, client: AsyncClient, tmp_path: Path):
        """Empty secret fields should remain empty, not '***'."""
        config_data = {
            "job_titles": ["Engineer"],
            "locations": ["Remote"],
            "alibaba_app_key": "",
            "boss_zhipin_cookie": "",
        }
        config_file = tmp_path / "user_config.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        settings = get_settings()
        original_path = settings.user_config_path
        try:
            settings.user_config_path = config_file
            resp = await client.get("/api/config/preferences")
        finally:
            settings.user_config_path = original_path

        assert resp.status_code == 200
        data = resp.json()
        assert data["alibaba_app_key"] == ""
        assert data["boss_zhipin_cookie"] == ""

    async def test_both_secrets_masked_when_both_set(self, client: AsyncClient, tmp_path: Path):
        """Both sensitive fields should be masked simultaneously."""
        config_data = {
            "job_titles": ["Engineer"],
            "locations": ["Remote"],
            "alibaba_app_key": "key-123",
            "boss_zhipin_cookie": "cookie-456",
        }
        config_file = tmp_path / "user_config.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        settings = get_settings()
        original_path = settings.user_config_path
        try:
            settings.user_config_path = config_file
            resp = await client.get("/api/config/preferences")
        finally:
            settings.user_config_path = original_path

        assert resp.status_code == 200
        data = resp.json()
        assert data["alibaba_app_key"] == "***"
        assert data["boss_zhipin_cookie"] == "***"
        # Non-sensitive fields should still show real values
        assert data["job_titles"] == ["Engineer"]
        assert data["locations"] == ["Remote"]

    async def test_raw_secret_value_not_in_response(self, client: AsyncClient, tmp_path: Path):
        """The actual secret value must never appear in the response body."""
        secret_value = "super-secret-key-never-expose-this"
        config_data = {
            "job_titles": ["Engineer"],
            "locations": ["Remote"],
            "alibaba_app_key": secret_value,
            "boss_zhipin_cookie": "",
        }
        config_file = tmp_path / "user_config.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        settings = get_settings()
        original_path = settings.user_config_path
        try:
            settings.user_config_path = config_file
            resp = await client.get("/api/config/preferences")
        finally:
            settings.user_config_path = original_path

        assert resp.status_code == 200
        # Verify the secret never appears anywhere in the response text
        assert secret_value not in resp.text
