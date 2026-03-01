"""Tests for the ATS keyword scorer — Chinese language support."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.matching import ATSKeywordScore
from app.services.matching.ats_scorer import (
    SOFT_SKILL_KEYWORDS_ZH,
    TECHNICAL_KEYWORDS_ZH,
    _extract_keywords_zh,
    _tokenize_zh,
    compute_ats_score,
    compute_ats_score_llm,
)


class TestTokenizeZh:
    """Tests for Chinese tokenizer."""

    def test_segments_chinese_text(self):
        tokens = _tokenize_zh("我们需要Python和机器学习经验")
        assert "python" in tokens
        assert "机器" in tokens or "机器学习" in tokens

    def test_extracts_english_inline(self):
        tokens = _tokenize_zh("精通Python、React和Docker")
        assert "python" in tokens
        assert "react" in tokens
        assert "docker" in tokens

    def test_bigrams_created(self):
        tokens = _tokenize_zh("深度学习")
        # jieba may output "深度" + "学习" or "深度学习"
        assert "深度学习" in tokens or ("深度" in tokens and "学习" in tokens)

    def test_empty_string(self):
        tokens = _tokenize_zh("")
        # Should not raise
        assert isinstance(tokens, set)


class TestExtractKeywordsZh:
    """Tests for Chinese keyword extraction."""

    def test_extracts_chinese_technical_keywords(self):
        text = "要求熟悉机器学习、深度学习和分布式系统，精通Python和Docker"
        tech, soft = _extract_keywords_zh(text)
        assert "机器学习" in tech
        assert "python" in tech
        assert "docker" in tech

    def test_extracts_chinese_soft_skills(self):
        text = "需要良好的沟通能力和团队合作精神，具备领导力"
        tech, soft = _extract_keywords_zh(text)
        assert any(kw in soft for kw in ["沟通", "沟通能力"])
        assert any(kw in soft for kw in ["团队合作", "团队协作"])

    def test_separates_technical_and_soft(self):
        text = "精通Python，具备沟通能力"
        tech, soft = _extract_keywords_zh(text)
        assert "python" in tech
        assert "python" not in soft

    def test_chinese_cloud_keywords(self):
        text = "有阿里云或腾讯云使用经验"
        tech, soft = _extract_keywords_zh(text)
        assert "阿里云" in tech or "腾讯云" in tech


class TestComputeAtsScoreZh:
    """Tests for ATS scoring with Chinese text."""

    def test_chinese_job_detected_auto(self):
        result = compute_ats_score(
            resume_text="Python开发工程师，熟悉机器学习和深度学习",
            job_description="要求精通Python，有机器学习项目经验",
            ats_mode="auto",
        )
        assert isinstance(result, ATSKeywordScore)
        assert result.score > 0.0
        assert "python" in result.matched_keywords or "机器学习" in result.matched_keywords

    def test_skip_mode_returns_none(self):
        result = compute_ats_score(
            resume_text="Any resume",
            job_description="Any job",
            ats_mode="skip",
        )
        assert result is None

    def test_chinese_keyword_overlap(self):
        resume = "精通Python、Docker、Kubernetes、机器学习、分布式系统，具备沟通能力"
        jd = "要求Python、Docker、机器学习经验，需要沟通能力和团队合作"
        result = compute_ats_score(resume, jd, ats_mode="auto")
        assert result is not None
        assert result.score > 30.0
        assert len(result.matched_keywords) > 0

    def test_english_fallback_when_english_text(self):
        result = compute_ats_score(
            resume_text="Python developer with Docker experience",
            job_description="Looking for Python and Docker skills",
            ats_mode="auto",
        )
        assert isinstance(result, ATSKeywordScore)
        assert "python" in result.matched_keywords

    def test_curated_zh_sets_not_empty(self):
        assert len(TECHNICAL_KEYWORDS_ZH) >= 50
        assert len(SOFT_SKILL_KEYWORDS_ZH) >= 15


class TestComputeAtsScoreLlm:
    """Tests for LLM-based ATS scoring."""

    async def test_llm_mode_calls_llm(self):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"technical": ["python", "docker"], "soft": ["communication"]}'
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        result = await compute_ats_score_llm(
            resume_text="Python developer with Docker",
            job_description="Need Python, Docker, and communication skills",
            llm=mock_llm,
        )
        assert isinstance(result, ATSKeywordScore)
        assert mock_llm.ainvoke.call_count == 2  # once for job, once for resume

    async def test_llm_mode_computes_overlap(self):
        mock_llm = MagicMock()

        job_resp = MagicMock()
        job_resp.content = '{"technical": ["python", "docker", "aws"], "soft": ["leadership"]}'
        resume_resp = MagicMock()
        resume_resp.content = '{"technical": ["python", "docker"], "soft": ["leadership"]}'

        mock_llm.ainvoke = AsyncMock(side_effect=[job_resp, resume_resp])

        result = await compute_ats_score_llm(
            resume_text="...", job_description="...", llm=mock_llm
        )
        assert "python" in result.matched_keywords
        assert "docker" in result.matched_keywords
        assert "aws" in result.missing_keywords
