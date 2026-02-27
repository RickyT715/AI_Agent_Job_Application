"""Tests for configuration loading and validation."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from app.config import (
    MatchingWeights,
    Settings,
    UserConfig,
    load_user_config,
    reset_settings,
)


class TestSettings:
    """Tests for infrastructure settings."""

    def setup_method(self):
        reset_settings()

    def test_settings_loads_defaults(self):
        with patch.dict("os.environ", {}, clear=False):
            settings = Settings()
        assert settings.gemini_model == "gemini-3.1-pro-preview"
        assert settings.claude_model == "claude-sonnet-4-6"
        assert settings.embedding_model == "gemini-embedding-001"

    def test_settings_loads_from_env(self):
        env = {
            "GOOGLE_API_KEY": "test-key-123",
            "GEMINI_MODEL": "gemini-pro",
        }
        with patch.dict("os.environ", env, clear=False):
            settings = Settings()
        assert settings.google_api_key.get_secret_value() == "test-key-123"
        assert settings.gemini_model == "gemini-pro"

    def test_secret_str_masks_keys(self):
        env = {"GOOGLE_API_KEY": "super-secret-key"}
        with patch.dict("os.environ", env, clear=False):
            settings = Settings()
        # SecretStr should not reveal the value in repr
        repr_str = repr(settings.google_api_key)
        assert "super-secret-key" not in repr_str
        assert "**" in repr_str

    def test_database_url_default(self):
        settings = Settings()
        assert "postgresql" in settings.database_url

    def test_langsmith_tracing_default_false(self):
        settings = Settings()
        assert settings.langsmith_tracing is False


class TestMatchingWeights:
    """Tests for matching weight validation."""

    def test_default_weights_sum_to_one(self):
        weights = MatchingWeights()
        total = weights.skills + weights.experience + weights.education + weights.location + weights.salary
        assert abs(total - 1.0) < 0.01

    def test_valid_custom_weights(self):
        weights = MatchingWeights(
            skills=0.4, experience=0.3, education=0.1, location=0.1, salary=0.1
        )
        assert weights.skills == 0.4

    def test_invalid_weights_sum_rejected(self):
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            MatchingWeights(
                skills=0.5, experience=0.5, education=0.5, location=0.5, salary=0.5
            )

    def test_negative_weight_rejected(self):
        with pytest.raises(ValueError):
            MatchingWeights(
                skills=-0.1, experience=0.4, education=0.3, location=0.2, salary=0.2
            )


class TestUserConfig:
    """Tests for user configuration from YAML."""

    def test_default_user_config(self):
        config = UserConfig()
        assert "Software Engineer" in config.job_titles
        assert "Remote" in config.locations

    def test_valid_experience_levels(self):
        for level in ["entry", "mid", "senior", "lead", "executive"]:
            config = UserConfig(experience_level=level)
            assert config.experience_level == level

    def test_invalid_experience_level_rejected(self):
        with pytest.raises(ValueError, match="experience_level"):
            UserConfig(experience_level="intern")

    def test_yaml_config_loads_valid(self):
        data = {
            "job_titles": ["ML Engineer", "Data Scientist"],
            "locations": ["Remote"],
            "salary_min": 150000,
            "salary_max": 250000,
            "experience_level": "senior",
            "weights": {
                "skills": 0.4,
                "experience": 0.3,
                "education": 0.1,
                "location": 0.1,
                "salary": 0.1,
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            path = Path(f.name)

        config = load_user_config(path)
        assert config.job_titles == ["ML Engineer", "Data Scientist"]
        assert config.salary_min == 150000
        assert config.weights.skills == 0.4
        path.unlink()

    def test_yaml_config_rejects_invalid(self):
        data = {
            "weights": {
                "skills": 0.9,
                "experience": 0.9,
                "education": 0.9,
                "location": 0.9,
                "salary": 0.9,
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            path = Path(f.name)

        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            load_user_config(path)
        path.unlink()

    def test_missing_yaml_returns_defaults(self, tmp_path):
        config = load_user_config(tmp_path / "nonexistent.yaml")
        assert config.job_titles == ["Software Engineer"]

    def test_empty_yaml_returns_defaults(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            path = Path(f.name)

        config = load_user_config(path)
        assert config.job_titles == ["Software Engineer"]
        path.unlink()
