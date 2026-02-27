"""Tests for LLM factory model routing."""

from unittest.mock import patch

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.services.llm_factory import LLMTask, get_embeddings, get_llm


@pytest.fixture(autouse=True)
def _mock_settings():
    """Mock settings so tests don't need real API keys."""
    with patch("app.services.llm_factory.get_settings") as mock:
        settings = mock.return_value
        settings.gemini_model = "gemini-3.1-pro-preview"
        settings.claude_model = "claude-sonnet-4-6"
        settings.embedding_model = "gemini-embedding-001"
        settings.google_api_key.get_secret_value.return_value = "test-google-key"
        settings.anthropic_api_key.get_secret_value.return_value = "test-anthropic-key"
        yield mock


class TestGetLLM:
    """Tests for get_llm() model routing."""

    def test_parse_task_returns_gemini(self):
        llm = get_llm(LLMTask.PARSE)
        assert isinstance(llm, ChatGoogleGenerativeAI)

    def test_extract_task_returns_gemini(self):
        llm = get_llm(LLMTask.EXTRACT)
        assert isinstance(llm, ChatGoogleGenerativeAI)

    def test_classify_task_returns_gemini(self):
        llm = get_llm(LLMTask.CLASSIFY)
        assert isinstance(llm, ChatGoogleGenerativeAI)

    def test_score_task_returns_claude(self):
        llm = get_llm(LLMTask.SCORE)
        assert isinstance(llm, ChatAnthropic)

    def test_cover_letter_task_returns_claude(self):
        llm = get_llm(LLMTask.COVER_LETTER)
        assert isinstance(llm, ChatAnthropic)

    def test_browser_agent_task_returns_claude(self):
        llm = get_llm(LLMTask.BROWSER_AGENT)
        assert isinstance(llm, ChatAnthropic)

    def test_invalid_task_raises(self):
        with pytest.raises(ValueError, match="Unknown LLM task"):
            get_llm("nonexistent_task")

    def test_default_temperature_is_zero(self):
        llm = get_llm(LLMTask.PARSE)
        assert llm.temperature == 0.0

    def test_custom_temperature(self):
        llm = get_llm(LLMTask.COVER_LETTER, temperature=0.7)
        assert llm.temperature == 0.7


class TestGetEmbeddings:
    """Tests for get_embeddings()."""

    def test_embeddings_returns_google(self):
        emb = get_embeddings()
        assert isinstance(emb, GoogleGenerativeAIEmbeddings)

    def test_embeddings_default_task_type(self):
        emb = get_embeddings()
        assert emb.task_type == "retrieval_document"

    def test_embeddings_query_task_type(self):
        emb = get_embeddings(task_type="retrieval_query")
        assert emb.task_type == "retrieval_query"
