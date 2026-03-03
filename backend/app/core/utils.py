"""Shared utility functions."""


def escape_like(value: str) -> str:
    """Escape SQL LIKE special characters in user input."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
