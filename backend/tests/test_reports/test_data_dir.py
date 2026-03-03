"""Tests for data_dir path derivation in reports and resume client."""

from pathlib import Path
from unittest.mock import patch

from app.routers.reports import _get_reports_dir
from app.services.resume_generator.client import _get_resumes_dir


class TestReportsDir:
    """Tests for _get_reports_dir() using settings.data_dir."""

    def test_reports_dir_uses_settings_data_dir(self, tmp_path: Path):
        """_get_reports_dir should return data_dir / 'reports'."""
        mock_settings = type("S", (), {"data_dir": tmp_path})()
        with patch("app.routers.reports.get_settings", return_value=mock_settings):
            result = _get_reports_dir()
        assert result == tmp_path / "reports"

    def test_reports_dir_returns_path_object(self, tmp_path: Path):
        """_get_reports_dir should return a Path instance."""
        mock_settings = type("S", (), {"data_dir": tmp_path})()
        with patch("app.routers.reports.get_settings", return_value=mock_settings):
            result = _get_reports_dir()
        assert isinstance(result, Path)

    def test_reports_dir_changes_with_data_dir(self, tmp_path: Path):
        """Different data_dir values should produce different reports paths."""
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"

        with patch("app.routers.reports.get_settings", return_value=type("S", (), {"data_dir": dir_a})()):
            result_a = _get_reports_dir()
        with patch("app.routers.reports.get_settings", return_value=type("S", (), {"data_dir": dir_b})()):
            result_b = _get_reports_dir()

        assert result_a != result_b
        assert result_a == dir_a / "reports"
        assert result_b == dir_b / "reports"


class TestResumesDir:
    """Tests for _get_resumes_dir() using settings.data_dir."""

    def test_resumes_dir_uses_settings_data_dir(self, tmp_path: Path):
        """_get_resumes_dir should return data_dir / 'resumes'."""
        mock_settings = type("S", (), {"data_dir": tmp_path})()
        with patch("app.services.resume_generator.client.get_settings", return_value=mock_settings):
            result = _get_resumes_dir()
        assert result == tmp_path / "resumes"

    def test_resumes_dir_returns_path_object(self, tmp_path: Path):
        """_get_resumes_dir should return a Path instance."""
        mock_settings = type("S", (), {"data_dir": tmp_path})()
        with patch("app.services.resume_generator.client.get_settings", return_value=mock_settings):
            result = _get_resumes_dir()
        assert isinstance(result, Path)

    def test_resumes_dir_changes_with_data_dir(self, tmp_path: Path):
        """Different data_dir values should produce different resumes paths."""
        dir_a = tmp_path / "x"
        dir_b = tmp_path / "y"

        with patch("app.services.resume_generator.client.get_settings", return_value=type("S", (), {"data_dir": dir_a})()):
            result_a = _get_resumes_dir()
        with patch("app.services.resume_generator.client.get_settings", return_value=type("S", (), {"data_dir": dir_b})()):
            result_b = _get_resumes_dir()

        assert result_a != result_b
        assert result_a == dir_a / "resumes"
        assert result_b == dir_b / "resumes"


class TestSavePdfToDisk:
    """Tests for save_pdf_to_disk using data_dir."""

    def test_save_creates_file_in_resumes_dir(self, tmp_path: Path):
        """save_pdf_to_disk should write bytes to data_dir/resumes/filename."""
        from app.services.resume_generator.client import save_pdf_to_disk

        mock_settings = type("S", (), {"data_dir": tmp_path})()
        with patch("app.services.resume_generator.client.get_settings", return_value=mock_settings):
            path = save_pdf_to_disk(b"fake-pdf-content", "test_resume.pdf")

        assert path == tmp_path / "resumes" / "test_resume.pdf"
        assert path.exists()
        assert path.read_bytes() == b"fake-pdf-content"

    def test_save_creates_resumes_directory(self, tmp_path: Path):
        """save_pdf_to_disk should create the resumes directory if it doesn't exist."""
        from app.services.resume_generator.client import save_pdf_to_disk

        data_dir = tmp_path / "new_data"
        mock_settings = type("S", (), {"data_dir": data_dir})()
        with patch("app.services.resume_generator.client.get_settings", return_value=mock_settings):
            path = save_pdf_to_disk(b"content", "resume.pdf")

        assert (data_dir / "resumes").is_dir()
        assert path.exists()
