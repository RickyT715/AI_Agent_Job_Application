"""Tests for core utility functions."""

from app.core.utils import escape_like


class TestEscapeLike:
    """Tests for the escape_like SQL helper."""

    def test_percent_escaped(self):
        assert escape_like("100%") == "100\\%"

    def test_underscore_escaped(self):
        assert escape_like("job_title") == "job\\_title"

    def test_backslash_escaped(self):
        assert escape_like("path\\to") == "path\\\\to"

    def test_normal_string_unchanged(self):
        assert escape_like("hello world") == "hello world"

    def test_empty_string(self):
        assert escape_like("") == ""

    def test_combined_special_chars(self):
        assert escape_like("100%_data\\end") == "100\\%\\_data\\\\end"

    def test_multiple_percents(self):
        assert escape_like("%%") == "\\%\\%"

    def test_multiple_underscores(self):
        assert escape_like("__init__") == "\\_\\_init\\_\\_"

    def test_backslash_before_percent(self):
        """Backslash must be escaped first to avoid double-escaping."""
        result = escape_like("\\%")
        assert result == "\\\\\\%"

    def test_only_special_chars(self):
        assert escape_like("%_\\") == "\\%\\_\\\\"
