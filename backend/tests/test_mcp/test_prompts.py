"""Tests for MCP prompt definitions."""

from unittest.mock import patch

import pytest


class TestPromptRegistration:
    """Tests for MCP prompt registration."""

    @pytest.mark.asyncio
    async def test_prompts_registered(self, mcp_server):
        prompts = await mcp_server.list_prompts()
        prompt_names = [p.name for p in prompts]
        assert "cover_letter_prompt" in prompt_names

    @pytest.mark.asyncio
    async def test_exactly_one_prompt(self, mcp_server):
        prompts = await mcp_server.list_prompts()
        assert len(prompts) == 1


class TestCoverLetterPrompt:
    """Tests for cover_letter_prompt."""

    @pytest.mark.asyncio
    async def test_prompt_includes_job_title(self, mcp_server):
        with patch("app.mcp.server._load_resume_text", return_value="Test resume"):
            result = await mcp_server.render_prompt(
                "cover_letter_prompt",
                {"job_title": "Backend Engineer", "company": "ACME Corp"},
            )

        # render_prompt returns list of messages
        content = str(result)
        assert "Backend Engineer" in content

    @pytest.mark.asyncio
    async def test_prompt_includes_company(self, mcp_server):
        with patch("app.mcp.server._load_resume_text", return_value="Test resume"):
            result = await mcp_server.render_prompt(
                "cover_letter_prompt",
                {"job_title": "Engineer", "company": "TechCorp"},
            )

        content = str(result)
        assert "TechCorp" in content

    @pytest.mark.asyncio
    async def test_prompt_includes_resume(self, mcp_server):
        with patch(
            "app.mcp.server._load_resume_text",
            return_value="John Doe, Senior Engineer, 10 years experience",
        ):
            result = await mcp_server.render_prompt(
                "cover_letter_prompt",
                {"job_title": "Engineer", "company": "ACME"},
            )

        content = str(result)
        assert "John Doe" in content
