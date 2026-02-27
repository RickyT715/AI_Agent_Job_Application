"""Tests for ARQ background task definitions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.worker.tasks import run_agent, run_matching, run_scraping


class TestTaskDefinitions:
    """Tests for ARQ task function signatures and basic behavior."""

    async def test_run_scraping_returns_results(self):
        """run_scraping with mocked scrapers should return stats."""
        from app.services.scraping.orchestrator import OrchestrationResult

        mock_orch_instance = MagicMock()
        mock_orch_instance.run = AsyncMock(
            return_value=OrchestrationResult(total=3, new=3, duplicates=0)
        )

        mock_orch_cls = MagicMock(return_value=mock_orch_instance)

        with (
            patch("app.worker.tasks.JSearchScraper", MagicMock()),
            patch("app.worker.tasks.ScrapingOrchestrator", mock_orch_cls),
            patch("app.worker.tasks.JobDeduplicator", MagicMock()),
            patch("app.worker.tasks._build_scrapers", return_value=[MagicMock()]),
            patch("app.worker.tasks.get_db_session_ctx") as mock_db_ctx,
        ):
            # Mock DB context manager
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await run_scraping(
                ctx={},
                queries=["Software Engineer"],
                location="Remote",
            )

        assert isinstance(result, dict)
        assert "Software Engineer" in result

    async def test_run_matching_returns_status(self):
        """run_matching should return status after matching."""
        mock_user = MagicMock()
        mock_user.resume_text = "Test resume"

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_user)
        # Empty jobs query
        mock_jobs_result = MagicMock()
        mock_jobs_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        mock_session.execute = AsyncMock(return_value=mock_jobs_result)

        with patch("app.worker.tasks.get_db_session_ctx") as mock_db_ctx:
            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await run_matching(ctx={}, user_id=1)

        assert result["status"] == "complete"
        assert result["matches"] == 0

    async def test_run_agent_returns_status(self):
        """run_agent should return status after agent run."""
        mock_job = MagicMock()
        mock_job.apply_url = "https://example.com/apply"
        mock_job.title = "Test Job"
        mock_job.company = "TestCo"

        mock_user = MagicMock()
        mock_user.email = "test@test.com"
        mock_user.full_name = "Test User"
        mock_user.phone = ""
        mock_user.linkedin_url = ""
        mock_user.resume_text = "Test resume"

        mock_app = MagicMock()
        mock_app.id = 1

        mock_session = AsyncMock()

        async def mock_get(model, id):
            if model.__name__ == "Job":
                return mock_job
            elif model.__name__ == "User":
                return mock_user
            elif model.__name__ == "Application":
                return mock_app
            return None

        mock_session.get = AsyncMock(side_effect=mock_get)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={"status": "submitted"})

        with (
            patch("app.worker.tasks.get_db_session_ctx") as mock_db_ctx,
            patch("app.worker.tasks.compile_agent_graph", return_value=mock_graph),
        ):
            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await run_agent(ctx={}, job_id=42, user_id=1)

        assert result["status"] == "submitted"
        assert result["job_id"] == 42

    async def test_run_scraping_multiple_queries(self):
        """Multiple queries should each produce a result entry."""
        from app.services.scraping.orchestrator import OrchestrationResult

        mock_orch_instance = MagicMock()
        mock_orch_instance.run = AsyncMock(
            return_value=OrchestrationResult(total=2, new=2, duplicates=0)
        )

        mock_orch_cls = MagicMock(return_value=mock_orch_instance)

        with (
            patch("app.worker.tasks.JSearchScraper", MagicMock()),
            patch("app.worker.tasks.ScrapingOrchestrator", mock_orch_cls),
            patch("app.worker.tasks.JobDeduplicator", MagicMock()),
            patch("app.worker.tasks._build_scrapers", return_value=[MagicMock()]),
            patch("app.worker.tasks.get_db_session_ctx") as mock_db_ctx,
        ):
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
            mock_db_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await run_scraping(
                ctx={},
                queries=["Python Dev", "ML Engineer"],
            )

        assert "Python Dev" in result
        assert "ML Engineer" in result
