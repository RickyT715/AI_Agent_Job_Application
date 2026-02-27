"""Tests for MCP tool definitions and execution."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.mcp.server import mcp


class TestToolRegistration:
    """Tests for MCP tool registration."""

    @pytest.mark.asyncio
    async def test_all_tools_registered(self, mcp_server):
        tools = await mcp_server.list_tools()
        tool_names = [t.name for t in tools]
        assert "search_jobs" in tool_names
        assert "match_resume_to_jobs" in tool_names
        assert "fill_application" in tool_names
        assert "generate_cover_letter" in tool_names
        assert "generate_report" in tool_names

    @pytest.mark.asyncio
    async def test_exactly_five_tools(self, mcp_server):
        tools = await mcp_server.list_tools()
        assert len(tools) == 5

    @pytest.mark.asyncio
    async def test_search_jobs_has_description(self, mcp_server):
        tool = await mcp_server.get_tool("search_jobs")
        assert tool is not None
        assert "search" in tool.description.lower() or "job" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_fill_application_has_description(self, mcp_server):
        tool = await mcp_server.get_tool("fill_application")
        assert tool is not None
        assert "application" in tool.description.lower() or "fill" in tool.description.lower()


class TestSearchJobsTool:
    """Tests for search_jobs tool execution."""

    @pytest.mark.asyncio
    async def test_search_jobs_calls_orchestrator(self, mcp_server):
        mock_result = MagicMock()
        mock_result.total = 3
        mock_result.new = 3
        mock_result.duplicates = 0
        mock_result.errors = []
        mock_result.jobs = []

        mock_orch = MagicMock()
        mock_orch.run = AsyncMock(return_value=mock_result)

        with (
            patch(
                "app.services.scraping.api.jsearch.JSearchScraper",
                return_value=MagicMock(),
            ),
            patch(
                "app.services.scraping.deduplicator.JobDeduplicator",
                return_value=MagicMock(),
            ),
            patch(
                "app.services.scraping.orchestrator.ScrapingOrchestrator",
                return_value=mock_orch,
            ),
        ):
            result = await mcp_server.call_tool(
                "search_jobs",
                {"query": "Python Developer", "location": "Remote", "limit": 10},
            )

        # ToolResult has .content list of TextContent
        assert result.content is not None
        text = result.content[0].text
        assert "total_found" in text

    @pytest.mark.asyncio
    async def test_search_jobs_with_filters(self, mcp_server):
        mock_result = MagicMock()
        mock_result.total = 0
        mock_result.new = 0
        mock_result.duplicates = 0
        mock_result.errors = []
        mock_result.jobs = []

        mock_orch = MagicMock()
        mock_orch.run = AsyncMock(return_value=mock_result)

        with (
            patch(
                "app.services.scraping.api.jsearch.JSearchScraper",
                return_value=MagicMock(),
            ),
            patch(
                "app.services.scraping.deduplicator.JobDeduplicator",
                return_value=MagicMock(),
            ),
            patch(
                "app.services.scraping.orchestrator.ScrapingOrchestrator",
                return_value=mock_orch,
            ),
        ):
            result = await mcp_server.call_tool(
                "search_jobs",
                {"query": "ML Engineer", "location": "San Francisco", "limit": 5},
            )

        mock_orch.run.assert_called_once_with("ML Engineer", location="San Francisco")


class TestFillApplicationTool:
    """Tests for fill_application tool execution."""

    @pytest.mark.asyncio
    async def test_fill_application_dry_run_default(self, mcp_server):
        with (
            patch("app.mcp.server._load_resume_text", return_value="Test resume"),
            patch("app.mcp.server._load_user_config"),
        ):
            result = await mcp_server.call_tool(
                "fill_application",
                {"apply_url": "https://boards.greenhouse.io/test/jobs/123"},
            )

        text = result.content[0].text
        assert "dry_run" in text or "preview" in text.lower()

    @pytest.mark.asyncio
    async def test_fill_application_detects_greenhouse(self, mcp_server):
        with (
            patch("app.mcp.server._load_resume_text", return_value="Test resume"),
            patch("app.mcp.server._load_user_config"),
        ):
            result = await mcp_server.call_tool(
                "fill_application",
                {"apply_url": "https://boards.greenhouse.io/company/jobs/123"},
            )

        text = result.content[0].text
        assert "greenhouse" in text.lower()


class TestGenerateReportTool:
    """Tests for generate_report tool execution."""

    @pytest.mark.asyncio
    async def test_generate_report_returns_html(self, mcp_server):
        result = await mcp_server.call_tool(
            "generate_report",
            {
                "job_title": "Software Engineer",
                "company": "TestCorp",
                "overall_score": 8.5,
                "breakdown": {"skills": 9, "experience": 8},
                "reasoning": "Strong match.",
                "strengths": ["Python", "FastAPI"],
                "missing_skills": ["Kubernetes"],
            },
        )

        text = result.content[0].text
        assert "html" in text.lower()


class TestGenerateCoverLetterTool:
    """Tests for generate_cover_letter tool execution."""

    @pytest.mark.asyncio
    async def test_cover_letter_no_resume_returns_error(self, mcp_server):
        with patch("app.mcp.server._load_resume_text", return_value=""):
            result = await mcp_server.call_tool(
                "generate_cover_letter",
                {
                    "job_title": "Engineer",
                    "company": "ACME",
                    "job_description": "Build stuff",
                },
            )

        text = result.content[0].text
        assert "error" in text.lower() or "resume" in text.lower()

    @pytest.mark.asyncio
    async def test_cover_letter_with_resume(self, mcp_server):
        mock_gen = MagicMock()
        mock_gen.generate = AsyncMock(return_value="Dear Hiring Manager, I am excited...")

        with (
            patch("app.mcp.server._load_resume_text", return_value="John Doe, 5 years Python"),
            patch(
                "app.services.reports.cover_letter.CoverLetterGenerator",
                return_value=mock_gen,
            ),
        ):
            result = await mcp_server.call_tool(
                "generate_cover_letter",
                {
                    "job_title": "Engineer",
                    "company": "ACME",
                    "job_description": "Build stuff",
                },
            )

        text = result.content[0].text
        assert "cover_letter" in text.lower() or "Dear" in text
