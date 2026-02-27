"""Tests for MCP resource definitions."""

from unittest.mock import patch

import pytest

from app.config import UserConfig


class TestResourceRegistration:
    """Tests for MCP resource registration."""

    @pytest.mark.asyncio
    async def test_all_resources_registered(self, mcp_server):
        resources = await mcp_server.list_resources()
        uris = [str(r.uri) for r in resources]
        assert "resume://current" in uris
        assert "preferences://job-search" in uris

    @pytest.mark.asyncio
    async def test_exactly_two_resources(self, mcp_server):
        resources = await mcp_server.list_resources()
        assert len(resources) == 2


class TestResumeResource:
    """Tests for resume://current resource."""

    @pytest.mark.asyncio
    async def test_resume_returns_text(self, mcp_server):
        with patch(
            "app.mcp.server._load_resume_text",
            return_value="John Doe\n5 years Python experience",
        ):
            result = await mcp_server.read_resource("resume://current")

        content = result.contents[0].content
        assert "John Doe" in content

    @pytest.mark.asyncio
    async def test_resume_no_file_returns_message(self, mcp_server):
        with patch("app.mcp.server._load_resume_text", return_value=""):
            result = await mcp_server.read_resource("resume://current")

        content = result.contents[0].content
        assert "no resume" in content.lower() or "uploaded" in content.lower()


class TestPreferencesResource:
    """Tests for preferences://job-search resource."""

    @pytest.mark.asyncio
    async def test_preferences_returns_json(self, mcp_server):
        mock_config = UserConfig(
            job_titles=["Software Engineer"],
            locations=["Remote"],
            experience_level="mid",
        )
        with patch("app.mcp.server._load_user_config", return_value=mock_config):
            result = await mcp_server.read_resource("preferences://job-search")

        content = result.contents[0].content
        assert "Software Engineer" in content
        assert "Remote" in content

    @pytest.mark.asyncio
    async def test_preferences_includes_weights(self, mcp_server):
        mock_config = UserConfig()
        with patch("app.mcp.server._load_user_config", return_value=mock_config):
            result = await mcp_server.read_resource("preferences://job-search")

        content = result.contents[0].content
        assert "weights" in content.lower()
