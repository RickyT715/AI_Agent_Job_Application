"""Tests for human-in-the-loop interrupt/resume flow.

Uses LangGraph's MemorySaver checkpointer to test the interrupt/resume
cycle without a real database.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.services.agent.graph import compile_agent_graph
from app.services.agent.state import make_initial_state


def _mock_browser_use():
    """Create patches for browser_use Agent and Browser."""
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock(return_value=None)
    mock_browser = MagicMock()
    mock_browser.close = AsyncMock()
    return (
        patch("app.services.agent.nodes.Agent", return_value=mock_agent),
        patch("app.services.agent.nodes.Browser", return_value=mock_browser),
        patch("app.services.agent.nodes.get_llm", return_value=MagicMock()),
    )


class TestInterruptResume:
    """Tests for the review_node interrupt and resume cycle."""

    def _make_graph(self):
        """Compile graph with MemorySaver for interrupt support."""
        return compile_agent_graph(checkpointer=MemorySaver())

    def _make_config(self, thread_id: str = "test-thread"):
        return {"configurable": {"thread_id": thread_id}}

    async def test_review_node_interrupts(self):
        """Graph pauses at review_node for generic ATS."""
        graph = self._make_graph()
        config = self._make_config("interrupt-test")

        state = make_initial_state(
            job_id=1,
            apply_url="https://careers.example.com/apply",
            user_profile={"first_name": "Alice", "email": "alice@test.com"},
        )

        p1, p2, p3 = _mock_browser_use()
        with p1, p2, p3:
            result = await graph.ainvoke(state, config)

        assert result is not None

    async def test_resume_with_approve(self):
        """Resume graph with approve → reaches submit_application."""
        graph = self._make_graph()
        config = self._make_config("approve-test")

        state = make_initial_state(
            job_id=1,
            apply_url="https://careers.example.com/apply",
            user_profile={"first_name": "Bob", "email": "bob@test.com"},
        )

        p1, p2, p3 = _mock_browser_use()
        with p1, p2, p3:
            await graph.ainvoke(state, config)
            result = await graph.ainvoke(
                Command(resume={"action": "approve"}),
                config,
            )

        assert result["status"] == "submitted"

    async def test_resume_with_reject(self):
        """Resume with reject → reaches abort_application."""
        graph = self._make_graph()
        config = self._make_config("reject-test")

        state = make_initial_state(
            job_id=2,
            apply_url="https://careers.example.com/apply",
            user_profile={"first_name": "Carol", "email": "carol@test.com"},
        )

        p1, p2, p3 = _mock_browser_use()
        with p1, p2, p3:
            await graph.ainvoke(state, config)
            result = await graph.ainvoke(
                Command(resume={"action": "reject"}),
                config,
            )

        assert result["status"] == "aborted"

    async def test_state_persists_across_interrupt(self):
        """Fields filled before interrupt are preserved after resume."""
        graph = self._make_graph()
        config = self._make_config("persist-test")

        state = make_initial_state(
            job_id=3,
            apply_url="https://careers.example.com/apply",
            user_profile={"first_name": "Dave", "email": "dave@test.com"},
        )

        p1, p2, p3 = _mock_browser_use()
        with p1, p2, p3:
            paused_result = await graph.ainvoke(state, config)
            assert "fields_filled" in paused_result
            assert paused_result["job_id"] == 3

            result = await graph.ainvoke(
                Command(resume={"action": "approve"}),
                config,
            )
            assert result["job_id"] == 3
            assert "fields_filled" in result

    async def test_api_platform_skips_review(self):
        """Greenhouse/Lever URLs go to api_submit, no interrupt."""
        graph = self._make_graph()
        config = self._make_config("api-skip-test")

        state = make_initial_state(
            job_id=4,
            apply_url="https://boards.greenhouse.io/testco/jobs/123",
        )

        # Mock the GreenhouseSubmitter for api_submit
        mock_submitter = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.message = "OK"
        mock_submitter.submit = AsyncMock(return_value=mock_result)

        with patch("app.services.agent.nodes.GreenhouseSubmitter", return_value=mock_submitter):
            result = await graph.ainvoke(state, config)

        assert result["status"] == "submitted"
        assert result["current_step"] == "api_submit"
