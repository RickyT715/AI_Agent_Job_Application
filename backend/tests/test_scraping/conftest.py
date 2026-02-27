"""Shared fixtures for scraping tests."""

import json
from pathlib import Path

import pytest

SCRAPING_FIXTURES = Path(__file__).parent.parent / "fixtures" / "scraping"


@pytest.fixture
def greenhouse_response() -> dict:
    """Load Greenhouse API response fixture."""
    return json.loads((SCRAPING_FIXTURES / "greenhouse_response.json").read_text())


@pytest.fixture
def lever_response() -> list[dict]:
    """Load Lever API response fixture."""
    return json.loads((SCRAPING_FIXTURES / "lever_response.json").read_text())


@pytest.fixture
def jsearch_response() -> dict:
    """Load JSearch API response fixture."""
    return json.loads((SCRAPING_FIXTURES / "jsearch_response.json").read_text())


@pytest.fixture
def workday_xhr_response() -> dict:
    """Load Workday XHR response fixture."""
    return json.loads((SCRAPING_FIXTURES / "workday_xhr_response.json").read_text())


@pytest.fixture
def page_with_jsonld() -> str:
    """Load HTML page with JSON-LD fixture."""
    return (SCRAPING_FIXTURES / "page_with_jsonld.html").read_text()


@pytest.fixture
def page_without_jsonld() -> str:
    """Load HTML page without JSON-LD fixture."""
    return (SCRAPING_FIXTURES / "page_without_jsonld.html").read_text()


@pytest.fixture
def adzuna_response() -> dict:
    """Load Adzuna API response fixture."""
    return json.loads((SCRAPING_FIXTURES / "adzuna_response.json").read_text())


@pytest.fixture
def arbeitnow_response() -> dict:
    """Load Arbeitnow API response fixture."""
    return json.loads((SCRAPING_FIXTURES / "arbeitnow_response.json").read_text())
