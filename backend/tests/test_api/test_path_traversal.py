"""Tests for path traversal protection in the reports download endpoint."""

from httpx import AsyncClient


class TestPathTraversalProtection:
    """Test that report download rejects path traversal attempts."""

    async def test_valid_report_id_accepted(self, client: AsyncClient):
        """A clean alphanumeric report ID should pass validation (404 = not found, not 400)."""
        resp = await client.get("/api/reports/report-123/download")
        assert resp.status_code == 404  # Passes regex but file doesn't exist

    async def test_simple_traversal_rejected(self, client: AsyncClient):
        """../etc/passwd style traversal should be rejected with 400."""
        resp = await client.get("/api/reports/../../etc/passwd/download")
        # FastAPI route won't even match with slashes, but test the regex guard
        # by URL-encoding or using the direct pattern
        resp = await client.get("/api/reports/..%2F..%2Fetc%2Fpasswd/download")
        assert resp.status_code in (400, 404, 422)

    async def test_dot_dot_in_id_rejected(self, client: AsyncClient):
        """Report ID containing '..' should be rejected."""
        resp = await client.get("/api/reports/report..123/download")
        assert resp.status_code == 400

    async def test_slash_in_id_rejected(self, client: AsyncClient):
        """Report ID containing '/' should be rejected."""
        # A literal slash in the path segment triggers 404 from routing,
        # but the regex pattern should also reject it if it reaches the handler.
        resp = await client.get("/api/reports/report%2F123/download")
        assert resp.status_code in (400, 404, 422)

    async def test_backslash_in_id_rejected(self, client: AsyncClient):
        """Report ID containing backslash should be rejected."""
        resp = await client.get("/api/reports/report%5C123/download")
        assert resp.status_code in (400, 404, 422)

    async def test_null_byte_in_id_rejected(self, client: AsyncClient):
        """Report ID containing null byte should be rejected."""
        resp = await client.get("/api/reports/report%00123/download")
        assert resp.status_code in (400, 404, 422)

    async def test_alphanumeric_with_dash_underscore_accepted(self, client: AsyncClient):
        """Valid IDs (alphanumeric, dash, underscore) should pass the regex guard (not 400)."""
        for rid in ["report-1", "report_2", "abc123", "A-Z_0-9"]:
            resp = await client.get(f"/api/reports/{rid}/download")
            # Should NOT be rejected by the regex (400); may be 200 or 404
            assert resp.status_code != 400, f"Valid ID '{rid}' was incorrectly rejected"

    async def test_empty_report_id_returns_error(self, client: AsyncClient):
        """Empty report ID should not match the route."""
        resp = await client.get("/api/reports//download")
        assert resp.status_code in (404, 405, 307)

    async def test_special_chars_rejected(self, client: AsyncClient):
        """Report IDs with special characters like ; or & should be rejected."""
        for rid in ["report;rm", "report&cmd", "report|cat"]:
            resp = await client.get(f"/api/reports/{rid}/download")
            assert resp.status_code == 400, f"Expected 400 for '{rid}'"
