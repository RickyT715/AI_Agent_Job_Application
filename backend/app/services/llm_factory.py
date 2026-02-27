"""Central model routing: Gemini (cheap tasks) + Claude (reasoning tasks).

Usage:
    from app.services.llm_factory import LLMTask, get_llm, get_embeddings

    llm = get_llm(LLMTask.PARSE)        # → Gemini 3 Flash
    llm = get_llm(LLMTask.SCORE)        # → Claude Sonnet 4.6
    embeddings = get_embeddings()         # → Gemini embedding-001
"""

from enum import Enum

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.config import get_settings


class LLMTask(str, Enum):
    """Task categories that determine which model to use."""

    # Gemini Flash tasks (cheap / free tier)
    PARSE = "parse"
    EXTRACT = "extract"
    CLASSIFY = "classify"

    # Claude Sonnet tasks (higher quality reasoning)
    SCORE = "score"
    COVER_LETTER = "cover_letter"
    BROWSER_AGENT = "browser_agent"


# Tasks routed to Gemini Flash
_GEMINI_TASKS = {LLMTask.PARSE, LLMTask.EXTRACT, LLMTask.CLASSIFY}

# Tasks routed to Claude Sonnet
_CLAUDE_TASKS = {LLMTask.SCORE, LLMTask.COVER_LETTER, LLMTask.BROWSER_AGENT}


def get_llm(task: LLMTask, temperature: float = 0.0) -> BaseChatModel:
    """Get the appropriate LLM for a given task.

    Args:
        task: The LLMTask enum value determining model selection.
        temperature: Model temperature. Defaults to 0.0 for determinism.

    Returns:
        A configured BaseChatModel instance.

    Raises:
        ValueError: If the task is not recognized.
    """
    settings = get_settings()

    if task in _GEMINI_TASKS:
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key.get_secret_value(),
            temperature=temperature,
        )
    elif task in _CLAUDE_TASKS:
        return ChatAnthropic(
            model=settings.claude_model,
            api_key=settings.anthropic_api_key.get_secret_value(),
            temperature=temperature,
            max_tokens=4096,
        )
    else:
        msg = f"Unknown LLM task: {task}"
        raise ValueError(msg)


def get_embeddings(task_type: str = "retrieval_document") -> GoogleGenerativeAIEmbeddings:
    """Get Gemini embedding model.

    Args:
        task_type: Either "retrieval_document" for indexing or
                   "retrieval_query" for search queries.

    Returns:
        Configured GoogleGenerativeAIEmbeddings instance.
    """
    settings = get_settings()
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key.get_secret_value(),
        task_type=task_type,
    )
