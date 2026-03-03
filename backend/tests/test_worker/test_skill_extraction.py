"""Tests for skill extraction during the scraping worker task.

Verifies that run_scraping correctly tracks new job IDs and only calls
extract_and_persist_skills for freshly inserted jobs.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.matching import JobPosting
from app.worker.tasks import run_scraping


def _make_posting(**overrides) -> JobPosting:
    """Create a minimal JobPosting for testing."""
    defaults = {
        "external_id": "ext-001",
        "source": "test",
        "title": "Engineer",
        "company": "TestCo",
        "description": "Build stuff",
    }
    defaults.update(overrides)
    return JobPosting(**defaults)


def _mock_db_session_ctx():
    """Create a mock for get_db_session_ctx that acts as async context manager."""
    mock_ctx = MagicMock()
    mock_session = AsyncMock()
    mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx, mock_session


class TestSkillExtractionInScraping:
    """Tests for the skill extraction step at the end of run_scraping."""

    async def test_new_jobs_trigger_skill_extraction(self):
        """Skills should be extracted for each newly persisted job."""
        from app.services.scraping.orchestrator import OrchestrationResult

        posting = _make_posting(external_id="new-001")

        mock_orch = MagicMock()
        mock_orch.run = AsyncMock(
            return_value=OrchestrationResult(total=1, new=1, duplicates=0, jobs=[posting])
        )

        # First DB context: persist jobs
        persist_ctx = MagicMock()
        persist_session = AsyncMock()
        persist_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        # Simulate flush assigning an id
        mock_job_obj = MagicMock()
        mock_job_obj.id = 42

        def capture_add(obj):
            obj.id = 42

        persist_session.add = MagicMock(side_effect=capture_add)
        persist_session.flush = AsyncMock()

        # Second DB context: skill extraction
        skill_ctx = MagicMock()
        skill_session = AsyncMock()
        skill_job = MagicMock()
        skill_job.id = 42
        skill_session.get = AsyncMock(return_value=skill_job)

        # Track which context manager call we're on
        call_count = {"n": 0}
        contexts = [
            (persist_ctx, persist_session),
            (skill_ctx, skill_session),
        ]

        def db_ctx_side_effect():
            idx = min(call_count["n"], len(contexts) - 1)
            call_count["n"] += 1
            ctx = MagicMock()
            ctx.__aenter__ = AsyncMock(return_value=contexts[idx][1])
            ctx.__aexit__ = AsyncMock(return_value=False)
            return ctx

        with (
            patch("app.worker.tasks._build_scrapers", return_value=[MagicMock()]),
            patch("app.worker.tasks.ScrapingOrchestrator", return_value=mock_orch),
            patch("app.worker.tasks.JobDeduplicator", MagicMock()),
            patch("app.worker.tasks.get_db_session_ctx", side_effect=db_ctx_side_effect),
            patch("app.worker.tasks.extract_and_persist_skills") as mock_extract,
        ):
            mock_extract.return_value = None  # async but we mock it
            mock_extract = AsyncMock()
            with patch("app.worker.tasks.extract_and_persist_skills", mock_extract):
                result = await run_scraping(ctx={}, queries=["Python Dev"])

        # extract_and_persist_skills should have been called for the new job
        assert mock_extract.call_count == 1

    async def test_duplicate_jobs_skip_skill_extraction(self):
        """When all scraped jobs already exist in DB, no skills should be extracted."""
        from app.services.scraping.orchestrator import OrchestrationResult

        posting = _make_posting(external_id="dup-001")

        mock_orch = MagicMock()
        mock_orch.run = AsyncMock(
            return_value=OrchestrationResult(total=1, new=0, duplicates=1, jobs=[posting])
        )

        # DB session returns existing job for dedup check
        mock_ctx = MagicMock()
        mock_session = AsyncMock()
        existing_job = MagicMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=existing_job))
        )

        def db_ctx_side_effect():
            ctx = MagicMock()
            ctx.__aenter__ = AsyncMock(return_value=mock_session)
            ctx.__aexit__ = AsyncMock(return_value=False)
            return ctx

        with (
            patch("app.worker.tasks._build_scrapers", return_value=[MagicMock()]),
            patch("app.worker.tasks.ScrapingOrchestrator", return_value=mock_orch),
            patch("app.worker.tasks.JobDeduplicator", MagicMock()),
            patch("app.worker.tasks.get_db_session_ctx", side_effect=db_ctx_side_effect),
            patch("app.worker.tasks.extract_and_persist_skills") as mock_extract,
        ):
            result = await run_scraping(ctx={}, queries=["Python Dev"])

        # Skill extraction should never be called since all jobs are duplicates
        mock_extract.assert_not_called()

    async def test_empty_scraping_results_skip_skill_extraction(self):
        """When scraping returns no jobs, skill extraction is skipped."""
        from app.services.scraping.orchestrator import OrchestrationResult

        mock_orch = MagicMock()
        mock_orch.run = AsyncMock(
            return_value=OrchestrationResult(total=0, new=0, duplicates=0, jobs=[])
        )

        mock_ctx = MagicMock()
        mock_session = AsyncMock()

        def db_ctx_side_effect():
            ctx = MagicMock()
            ctx.__aenter__ = AsyncMock(return_value=mock_session)
            ctx.__aexit__ = AsyncMock(return_value=False)
            return ctx

        with (
            patch("app.worker.tasks._build_scrapers", return_value=[MagicMock()]),
            patch("app.worker.tasks.ScrapingOrchestrator", return_value=mock_orch),
            patch("app.worker.tasks.JobDeduplicator", MagicMock()),
            patch("app.worker.tasks.get_db_session_ctx", side_effect=db_ctx_side_effect),
            patch("app.worker.tasks.extract_and_persist_skills") as mock_extract,
        ):
            result = await run_scraping(ctx={}, queries=["Niche Role"])

        mock_extract.assert_not_called()

    async def test_new_job_ids_populated_after_flush(self):
        """new_job_ids should contain the ID assigned during db.flush()."""
        from app.services.scraping.orchestrator import OrchestrationResult

        postings = [
            _make_posting(external_id="new-a"),
            _make_posting(external_id="new-b"),
        ]

        mock_orch = MagicMock()
        mock_orch.run = AsyncMock(
            return_value=OrchestrationResult(total=2, new=2, duplicates=0, jobs=postings)
        )

        # Track IDs assigned via flush
        id_counter = {"val": 100}

        def assign_id(obj):
            obj.id = id_counter["val"]
            id_counter["val"] += 1

        persist_session = AsyncMock()
        persist_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        persist_session.add = MagicMock(side_effect=assign_id)
        persist_session.flush = AsyncMock()

        skill_session = AsyncMock()
        skill_job = MagicMock()
        skill_session.get = AsyncMock(return_value=skill_job)

        call_count = {"n": 0}

        def db_ctx_side_effect():
            idx = call_count["n"]
            call_count["n"] += 1
            ctx = MagicMock()
            if idx == 0:
                ctx.__aenter__ = AsyncMock(return_value=persist_session)
            else:
                ctx.__aenter__ = AsyncMock(return_value=skill_session)
            ctx.__aexit__ = AsyncMock(return_value=False)
            return ctx

        mock_extract = AsyncMock()

        with (
            patch("app.worker.tasks._build_scrapers", return_value=[MagicMock()]),
            patch("app.worker.tasks.ScrapingOrchestrator", return_value=mock_orch),
            patch("app.worker.tasks.JobDeduplicator", MagicMock()),
            patch("app.worker.tasks.get_db_session_ctx", side_effect=db_ctx_side_effect),
            patch("app.worker.tasks.extract_and_persist_skills", mock_extract),
        ):
            result = await run_scraping(ctx={}, queries=["Dev"])

        # Should have been called twice (once per new job)
        assert mock_extract.call_count == 2

    async def test_mixed_new_and_duplicate_only_extracts_for_new(self):
        """When some jobs are new and some are duplicates, only new ones get skill extraction."""
        from app.services.scraping.orchestrator import OrchestrationResult

        postings = [
            _make_posting(external_id="existing-1"),
            _make_posting(external_id="brand-new-1"),
        ]

        mock_orch = MagicMock()
        mock_orch.run = AsyncMock(
            return_value=OrchestrationResult(total=2, new=1, duplicates=1, jobs=postings)
        )

        existing_mock = MagicMock()  # non-None means job exists
        call_idx = {"execute": 0}

        def execute_side_effect(*args, **kwargs):
            idx = call_idx["execute"]
            call_idx["execute"] += 1
            result = MagicMock()
            if idx == 0:
                # First job exists
                result.scalar_one_or_none = MagicMock(return_value=existing_mock)
            else:
                # Second job is new
                result.scalar_one_or_none = MagicMock(return_value=None)
            return result

        id_counter = {"val": 50}

        def assign_id(obj):
            obj.id = id_counter["val"]
            id_counter["val"] += 1

        persist_session = AsyncMock()
        persist_session.execute = AsyncMock(side_effect=execute_side_effect)
        persist_session.add = MagicMock(side_effect=assign_id)
        persist_session.flush = AsyncMock()

        skill_session = AsyncMock()
        skill_session.get = AsyncMock(return_value=MagicMock())

        call_count = {"n": 0}

        def db_ctx_side_effect():
            idx = call_count["n"]
            call_count["n"] += 1
            ctx = MagicMock()
            if idx == 0:
                ctx.__aenter__ = AsyncMock(return_value=persist_session)
            else:
                ctx.__aenter__ = AsyncMock(return_value=skill_session)
            ctx.__aexit__ = AsyncMock(return_value=False)
            return ctx

        mock_extract = AsyncMock()

        with (
            patch("app.worker.tasks._build_scrapers", return_value=[MagicMock()]),
            patch("app.worker.tasks.ScrapingOrchestrator", return_value=mock_orch),
            patch("app.worker.tasks.JobDeduplicator", MagicMock()),
            patch("app.worker.tasks.get_db_session_ctx", side_effect=db_ctx_side_effect),
            patch("app.worker.tasks.extract_and_persist_skills", mock_extract),
        ):
            result = await run_scraping(ctx={}, queries=["Dev"])

        # Only 1 new job, so skill extraction called once
        assert mock_extract.call_count == 1
