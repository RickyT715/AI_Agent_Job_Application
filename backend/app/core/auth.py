"""Simple API key authentication."""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """Validate the API key from the X-API-Key header.

    If ``settings.api_key`` is empty, authentication is disabled (dev mode).
    """
    settings = get_settings()
    configured_key = settings.api_key.get_secret_value()
    if not configured_key:
        # No key configured = auth disabled (development mode)
        return "dev"
    if not api_key or api_key != configured_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
