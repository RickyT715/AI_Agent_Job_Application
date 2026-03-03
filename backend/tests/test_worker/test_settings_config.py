"""Tests for ARQ WorkerSettings configuration."""

from app.worker.settings import WorkerSettings


class TestWorkerSettings:
    """Tests for WorkerSettings class attributes."""

    def test_max_tries(self):
        """Worker should retry up to 3 times."""
        assert WorkerSettings.max_tries == 3

    def test_retry_delay(self):
        """Retry delay should be 30 seconds."""
        assert WorkerSettings.retry_delay == 30

    def test_max_jobs(self):
        """Max concurrent jobs should be 5."""
        assert WorkerSettings.max_jobs == 5

    def test_job_timeout(self):
        """Job timeout should be 600 seconds (10 minutes)."""
        assert WorkerSettings.job_timeout == 600

    def test_health_check_interval(self):
        """Health check interval should be 30 seconds."""
        assert WorkerSettings.health_check_interval == 30

    def test_functions_registered(self):
        """Worker should have 3 registered task functions."""
        assert len(WorkerSettings.functions) == 3
        func_names = [f.__name__ if callable(f) else str(f) for f in WorkerSettings.functions]
        assert "run_scraping" in func_names
        assert "run_matching" in func_names
        assert "run_agent" in func_names

    def test_lifecycle_hooks(self):
        """Worker should have startup and shutdown hooks."""
        assert WorkerSettings.on_startup is not None
        assert WorkerSettings.on_shutdown is not None
