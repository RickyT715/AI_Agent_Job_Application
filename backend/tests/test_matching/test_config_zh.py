"""Tests for Chinese pipeline config fields."""

import pytest

from app.config import UserConfig


class TestAtsMode:
    """Tests for ats_mode config field."""

    def test_default_auto(self):
        config = UserConfig()
        assert config.ats_mode == "auto"

    def test_valid_skip(self):
        config = UserConfig(ats_mode="skip")
        assert config.ats_mode == "skip"

    def test_valid_llm(self):
        config = UserConfig(ats_mode="llm")
        assert config.ats_mode == "llm"

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="ats_mode"):
            UserConfig(ats_mode="invalid")


class TestRerankerMode:
    """Tests for reranker_mode config field."""

    def test_default_auto(self):
        config = UserConfig()
        assert config.reranker_mode == "auto"

    def test_valid_bge(self):
        config = UserConfig(reranker_mode="bge")
        assert config.reranker_mode == "bge"

    def test_valid_flashrank(self):
        config = UserConfig(reranker_mode="flashrank")
        assert config.reranker_mode == "flashrank"

    def test_valid_flashrank_multilingual(self):
        config = UserConfig(reranker_mode="flashrank-multilingual")
        assert config.reranker_mode == "flashrank-multilingual"

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="reranker_mode"):
            UserConfig(reranker_mode="invalid")


class TestEmbeddingModelChoice:
    """Tests for embedding_model_choice config field."""

    def test_default_gemini(self):
        config = UserConfig()
        assert config.embedding_model_choice == "gemini"

    def test_valid_bge_m3(self):
        config = UserConfig(embedding_model_choice="bge-m3")
        assert config.embedding_model_choice == "bge-m3"

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="embedding_model_choice"):
            UserConfig(embedding_model_choice="invalid")


class TestRecruitmentType:
    """Tests for recruitment_type config field."""

    def test_default_social(self):
        config = UserConfig()
        assert config.recruitment_type == "social"

    def test_valid_campus(self):
        config = UserConfig(recruitment_type="campus")
        assert config.recruitment_type == "campus"

    def test_valid_both(self):
        config = UserConfig(recruitment_type="both")
        assert config.recruitment_type == "both"

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="recruitment_type"):
            UserConfig(recruitment_type="invalid")


class TestGraduationYear:
    """Tests for graduation_year config field."""

    def test_default_none(self):
        config = UserConfig()
        assert config.graduation_year is None

    def test_set_year(self):
        config = UserConfig(graduation_year=2026)
        assert config.graduation_year == 2026


class TestMokahrOrgIds:
    """Tests for mokahr_org_ids config field."""

    def test_default_empty(self):
        config = UserConfig()
        assert config.mokahr_org_ids == []

    def test_set_ids(self):
        config = UserConfig(mokahr_org_ids=["org1", "org2"])
        assert config.mokahr_org_ids == ["org1", "org2"]
