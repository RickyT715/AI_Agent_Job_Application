"""Tests for individual LangGraph node functions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent.nodes import (
    abort_application,
    answer_questions,
    api_submit,
    detect_ats,
    fill_form_fields,
    navigate_to_form,
    submit_application,
    upload_resume,
)
from app.services.agent.state import ApplicationState


class TestDetectATS:
    """Tests for ATS platform detection from URL."""

    def test_detects_greenhouse_url(self):
        state: ApplicationState = {
            "apply_url": "https://boards.greenhouse.io/testco/jobs/12345",
        }
        result = detect_ats(state)
        assert result["ats_platform"] == "greenhouse"

    def test_detects_greenhouse_short_url(self):
        state: ApplicationState = {"apply_url": "https://grnh.se/abc123"}
        result = detect_ats(state)
        assert result["ats_platform"] == "greenhouse"

    def test_detects_lever_url(self):
        state: ApplicationState = {
            "apply_url": "https://jobs.lever.co/company/posting-id",
        }
        result = detect_ats(state)
        assert result["ats_platform"] == "lever"

    def test_detects_workday_url(self):
        state: ApplicationState = {
            "apply_url": "https://company.myworkdayjobs.com/en-US/careers/job/12345",
        }
        result = detect_ats(state)
        assert result["ats_platform"] == "workday"

    def test_generic_for_unknown_url(self):
        state: ApplicationState = {
            "apply_url": "https://careers.somecompany.com/apply",
        }
        result = detect_ats(state)
        assert result["ats_platform"] == "generic"

    def test_case_insensitive_detection(self):
        state: ApplicationState = {
            "apply_url": "https://BOARDS.GREENHOUSE.IO/test/jobs/123",
        }
        result = detect_ats(state)
        assert result["ats_platform"] == "greenhouse"

    def test_sets_status_in_progress(self):
        state: ApplicationState = {"apply_url": "https://example.com"}
        result = detect_ats(state)
        assert result["status"] == "in_progress"


class TestNavigateToForm:
    """Tests for navigate_to_form node."""

    @patch("app.services.agent.nodes.get_llm")
    async def test_returns_navigating_status(self, mock_get_llm):
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=None)
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()

        with patch("app.services.agent.nodes.Agent", return_value=mock_agent) as mock_agent_cls, \
             patch("app.services.agent.nodes.Browser", return_value=mock_browser):
            state: ApplicationState = {"apply_url": "https://example.com/apply"}
            result = await navigate_to_form(state)
            assert result["status"] == "navigating"
            assert result["current_step"] == "navigate"


class TestFillFormFields:
    """Tests for fill_form_fields node."""

    @patch("app.services.agent.nodes.get_llm")
    async def test_fills_from_user_profile(self, mock_get_llm, initial_state):
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=None)
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()

        with patch("app.services.agent.nodes.Agent", return_value=mock_agent), \
             patch("app.services.agent.nodes.Browser", return_value=mock_browser):
            result = await fill_form_fields(initial_state)
            assert result["status"] == "filling"
            assert "first_name" in result["fields_filled"]
            assert result["fields_filled"]["first_name"] == "John"

    @patch("app.services.agent.nodes.get_llm")
    async def test_fills_email(self, mock_get_llm, initial_state):
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=None)
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()

        with patch("app.services.agent.nodes.Agent", return_value=mock_agent), \
             patch("app.services.agent.nodes.Browser", return_value=mock_browser):
            result = await fill_form_fields(initial_state)
            assert result["fields_filled"]["email"] == "john.doe@example.com"

    @patch("app.services.agent.nodes.get_llm")
    async def test_fills_phone(self, mock_get_llm, initial_state):
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=None)
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()

        with patch("app.services.agent.nodes.Agent", return_value=mock_agent), \
             patch("app.services.agent.nodes.Browser", return_value=mock_browser):
            result = await fill_form_fields(initial_state)
            assert result["fields_filled"]["phone"] == "+1-555-123-4567"

    @patch("app.services.agent.nodes.get_llm")
    async def test_empty_profile_returns_empty_fields(self, mock_get_llm):
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=None)
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()

        with patch("app.services.agent.nodes.Agent", return_value=mock_agent), \
             patch("app.services.agent.nodes.Browser", return_value=mock_browser):
            state: ApplicationState = {"user_profile": {}, "fields_to_fill": {}}
            result = await fill_form_fields(state)
            assert result["fields_filled"] == {}


class TestUploadResume:
    """Tests for upload_resume node."""

    @patch("app.services.agent.nodes.get_llm")
    async def test_returns_upload_step(self, mock_get_llm):
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=None)
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()

        with patch("app.services.agent.nodes.Agent", return_value=mock_agent), \
             patch("app.services.agent.nodes.Browser", return_value=mock_browser):
            state: ApplicationState = {"resume_path": "/path/to/resume.pdf"}
            result = await upload_resume(state)
            assert result["current_step"] == "upload_resume"


class TestAnswerQuestions:
    """Tests for answer_questions node."""

    async def test_no_questions_returns_empty(self):
        state: ApplicationState = {"screening_questions": []}
        result = await answer_questions(state)
        assert result["screening_answers"] == {}

    @patch("app.services.agent.nodes.get_llm")
    async def test_answers_provided_questions(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "I have 5 years of experience."
        mock_llm.__or__ = MagicMock(return_value=mock_llm)
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm.return_value = mock_llm

        # Mock the LCEL chain: prompt | llm
        with patch("app.services.agent.nodes.SCREENING_ANSWER_PROMPT") as mock_prompt:
            mock_chain = MagicMock()
            mock_chain.ainvoke = AsyncMock(return_value=mock_response)
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            state: ApplicationState = {
                "screening_questions": [
                    {"question": "Why do you want to work here?"},
                    {"question": "Years of experience?"},
                ],
                "resume_text": "Test resume",
                "job_title": "Engineer",
                "company": "TestCo",
            }
            result = await answer_questions(state)
            assert len(result["screening_answers"]) == 2


class TestSubmitApplication:
    """Tests for submit_application node."""

    @patch("app.services.agent.nodes.get_llm")
    async def test_returns_submitted_status(self, mock_get_llm):
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=None)
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()

        with patch("app.services.agent.nodes.Agent", return_value=mock_agent), \
             patch("app.services.agent.nodes.Browser", return_value=mock_browser):
            state: ApplicationState = {}
            result = await submit_application(state)
            assert result["status"] == "submitted"
            assert result["current_step"] == "submit"


class TestAbortApplication:
    """Tests for abort_application node."""

    def test_returns_aborted_status(self):
        state: ApplicationState = {}
        result = abort_application(state)
        assert result["status"] == "aborted"
        assert result["current_step"] == "abort"


class TestAPISubmit:
    """Tests for api_submit node."""

    async def test_returns_submitted_status(self):
        """api_submit with greenhouse but no valid URL parts returns failed."""
        state: ApplicationState = {
            "ats_platform": "greenhouse",
            "apply_url": "https://boards.greenhouse.io/testco/jobs/123",
            "fields_filled": {"first_name": "Test"},
            "resume_path": "",
        }
        with patch("app.services.agent.nodes.GreenhouseSubmitter") as mock_cls:
            mock_submitter = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "OK"
            mock_submitter.submit = AsyncMock(return_value=mock_result)
            mock_cls.return_value = mock_submitter

            result = await api_submit(state)
            assert result["status"] == "submitted"
            assert result["current_step"] == "api_submit"
