"""Tests for cover letter generation chain."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.reports.cover_letter import (
    COVER_LETTER_PROMPT,
    COVER_LETTER_TEMPERATURE,
    CoverLetterGenerator,
)


class TestCoverLetterPrompt:
    """Tests for the cover letter prompt template."""

    def test_prompt_has_system_and_human_messages(self):
        messages = COVER_LETTER_PROMPT.messages
        assert len(messages) == 2

    def test_prompt_includes_job_title_variable(self):
        formatted = COVER_LETTER_PROMPT.format(
            job_title="Engineer",
            company="ACME",
            job_description="Build stuff",
            resume_text="Resume here",
            strengths="Python",
            missing_skills="Go",
        )
        assert "Engineer" in formatted

    def test_prompt_includes_company_variable(self):
        formatted = COVER_LETTER_PROMPT.format(
            job_title="Engineer",
            company="ACME",
            job_description="Build stuff",
            resume_text="Resume here",
            strengths="Python",
            missing_skills="Go",
        )
        assert "ACME" in formatted

    def test_prompt_includes_resume_variable(self):
        formatted = COVER_LETTER_PROMPT.format(
            job_title="Engineer",
            company="ACME",
            job_description="Build stuff",
            resume_text="John Doe 6 years Python",
            strengths="Python",
            missing_skills="Go",
        )
        assert "John Doe 6 years Python" in formatted


class TestCoverLetterTemperature:
    """Tests for temperature configuration."""

    def test_temperature_is_07(self):
        assert COVER_LETTER_TEMPERATURE == 0.7

    def test_generator_uses_default_temperature(self):
        gen = CoverLetterGenerator()
        assert gen._temperature == 0.7

    def test_generator_accepts_custom_temperature(self):
        gen = CoverLetterGenerator(temperature=0.5)
        assert gen._temperature == 0.5


class TestCoverLetterGenerator:
    """Tests for CoverLetterGenerator.generate()."""

    @pytest.mark.asyncio
    async def test_generate_returns_string(self, sample_cover_letter_input):
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(
            return_value="Dear Hiring Manager, I am writing to express my interest..."
        )

        gen = CoverLetterGenerator()
        with patch.object(gen, "_build_chain", return_value=mock_chain):
            result = await gen.generate(**sample_cover_letter_input)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_passes_all_fields(self, sample_cover_letter_input):
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value="Cover letter text")

        gen = CoverLetterGenerator()
        with patch.object(gen, "_build_chain", return_value=mock_chain):
            await gen.generate(**sample_cover_letter_input)

        call_args = mock_chain.ainvoke.call_args[0][0]
        assert call_args["job_title"] == "Senior Backend Engineer"
        assert call_args["company"] == "TechCorp"
        assert "Build scalable APIs" in call_args["job_description"]
        assert "John Doe" in call_args["resume_text"]

    @pytest.mark.asyncio
    async def test_generate_joins_strengths(self, sample_cover_letter_input):
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value="Cover letter text")

        gen = CoverLetterGenerator()
        with patch.object(gen, "_build_chain", return_value=mock_chain):
            await gen.generate(**sample_cover_letter_input)

        call_args = mock_chain.ainvoke.call_args[0][0]
        assert call_args["strengths"] == "Python, FastAPI, PostgreSQL"

    @pytest.mark.asyncio
    async def test_generate_joins_missing_skills(self, sample_cover_letter_input):
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value="Cover letter text")

        gen = CoverLetterGenerator()
        with patch.object(gen, "_build_chain", return_value=mock_chain):
            await gen.generate(**sample_cover_letter_input)

        call_args = mock_chain.ainvoke.call_args[0][0]
        assert call_args["missing_skills"] == "Kubernetes"

    @pytest.mark.asyncio
    async def test_build_chain_uses_correct_temperature(self):
        gen = CoverLetterGenerator(temperature=0.3)
        with patch("app.services.reports.cover_letter.get_llm") as mock_get_llm:
            mock_get_llm.return_value = MagicMock()
            gen._build_chain()
            mock_get_llm.assert_called_once()
            _, kwargs = mock_get_llm.call_args
            assert kwargs["temperature"] == 0.3
