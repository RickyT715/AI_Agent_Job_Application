"""Shared fixtures for MCP tests."""

import pytest

from app.mcp.server import mcp


@pytest.fixture
def mcp_server():
    """Return the configured MCP server instance."""
    return mcp
