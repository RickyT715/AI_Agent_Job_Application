"""FastAPI dependency injection providers."""

from app.config import Settings, get_settings


def get_app_settings() -> Settings:
    """Provide application settings as a dependency."""
    return get_settings()
