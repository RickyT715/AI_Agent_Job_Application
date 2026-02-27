"""Custom exceptions for the job application agent."""


class JobAgentError(Exception):
    """Base exception for all job agent errors."""


class ConfigurationError(JobAgentError):
    """Raised when configuration is invalid or missing."""


class LLMError(JobAgentError):
    """Raised when an LLM call fails."""


class EmbeddingError(JobAgentError):
    """Raised when embedding generation or indexing fails."""


class ScrapingError(JobAgentError):
    """Raised when job scraping fails."""


class MatchingError(JobAgentError):
    """Raised when the matching pipeline fails."""


class AgentError(JobAgentError):
    """Raised when the browser agent encounters an error."""
