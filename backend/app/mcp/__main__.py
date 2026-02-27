"""Entry point for running the MCP server.

Usage:
    # stdio transport (for Claude Desktop / Cursor)
    uv run python -m app.mcp

    # Streamable HTTP transport (for remote clients)
    uv run python -m app.mcp --transport streamable-http --port 8001
"""


from app.mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
