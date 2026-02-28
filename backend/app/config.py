"""Application configuration with two-tier config system.

Tier 1: Infrastructure config via .env + pydantic-settings (API keys, DB URLs, model names)
Tier 2: User preferences via data/user_config.yaml + Pydantic validation
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Tier 1: Infrastructure settings from environment / .env
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    """Infrastructure configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    google_api_key: SecretStr = SecretStr("")
    anthropic_api_key: SecretStr = SecretStr("")
    jsearch_api_key: SecretStr = SecretStr("")
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/job_agent"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Model names
    gemini_model: str = "gemini-3.1-pro-preview"
    claude_model: str = "claude-sonnet-4-6"
    embedding_model: str = "gemini-embedding-001"

    # Claude proxy (e.g., claude-code-proxy at http://localhost:42069)
    anthropic_base_url: str = ""

    # LangSmith
    langsmith_tracing: bool = False
    langsmith_api_key: SecretStr = SecretStr("")
    langsmith_project: str = "job-application-agent"

    # Paths
    data_dir: Path = Path("data")
    chroma_db_dir: Path = Path("data/chroma_db")
    user_config_path: Path = Path("data/user_config.yaml")


# ---------------------------------------------------------------------------
# Tier 2: User preferences from YAML
# ---------------------------------------------------------------------------

class MatchingWeights(BaseModel):
    """Weights for scoring dimensions. Must sum to 1.0."""

    skills: float = Field(default=0.35, ge=0.0, le=1.0)
    experience: float = Field(default=0.25, ge=0.0, le=1.0)
    education: float = Field(default=0.15, ge=0.0, le=1.0)
    location: float = Field(default=0.15, ge=0.0, le=1.0)
    salary: float = Field(default=0.10, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "MatchingWeights":
        total = self.skills + self.experience + self.education + self.location + self.salary
        if abs(total - 1.0) > 0.01:
            msg = f"Weights must sum to 1.0, got {total:.2f}"
            raise ValueError(msg)
        return self


class UserConfig(BaseModel):
    """User preferences for job search and matching."""

    # Job search preferences
    job_titles: list[str] = Field(default_factory=lambda: ["Software Engineer"])
    locations: list[str] = Field(default_factory=lambda: ["Remote"])
    salary_min: int | None = None
    salary_max: int | None = None
    workplace_types: list[str] = Field(
        default_factory=lambda: ["remote", "hybrid"],
    )
    experience_level: str = "mid"

    # Matching weights
    weights: MatchingWeights = Field(default_factory=MatchingWeights)

    # Resume
    resume_path: Path | None = None

    # --- Enhanced search settings ---
    employment_types: list[str] = Field(
        default_factory=lambda: ["FULLTIME"],
        description="FULLTIME, PARTTIME, CONTRACT, INTERNSHIP, TEMPORARY",
    )
    date_posted: str = Field(
        default="month",
        description="Filter: today, 3days, week, month, all",
    )
    salary_currency: str = "USD"
    final_results_count: int = Field(
        default=10, ge=1, le=200,
        description="How many final matched jobs to return",
    )
    num_pages_per_source: int = Field(
        default=1, ge=1, le=10,
        description="How many pages to fetch from each scraper source",
    )
    enabled_sources: list[str] = Field(
        default_factory=lambda: ["jsearch"],
        description="Which scrapers to use: jsearch, greenhouse, lever, workday, adzuna, arbeitnow",
    )

    # Company-specific scraper config
    greenhouse_board_tokens: list[str] = Field(
        default_factory=list,
        description="Greenhouse board tokens (e.g., 'stripe', 'airbnb')",
    )
    lever_companies: list[str] = Field(
        default_factory=list,
        description="Lever company slugs (e.g., 'netflix', 'figma')",
    )
    workday_urls: list[str] = Field(
        default_factory=list,
        description="Workday base URLs",
    )

    @field_validator("experience_level")
    @classmethod
    def validate_experience_level(cls, v: str) -> str:
        allowed = {"entry", "mid", "senior", "lead", "executive"}
        if v not in allowed:
            msg = f"experience_level must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return v

    @field_validator("date_posted")
    @classmethod
    def validate_date_posted(cls, v: str) -> str:
        allowed = {"today", "3days", "week", "month", "all"}
        if v not in allowed:
            msg = f"date_posted must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return v


def load_user_config(path: Path) -> UserConfig:
    """Load and validate user config from a YAML file."""
    if not path.exists():
        return UserConfig()
    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}
    return UserConfig(**data)


# ---------------------------------------------------------------------------
# Singleton access
# ---------------------------------------------------------------------------

_settings: Settings | None = None


def get_settings() -> Settings:
    """Get cached application settings."""
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset cached settings (for testing)."""
    global _settings  # noqa: PLW0603
    _settings = None
