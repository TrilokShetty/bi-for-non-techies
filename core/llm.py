"""Chat model factory.

Why a factory: nodes and tools should not care whether the model runs locally
(Ollama) or on a hosted free tier (Groq). One config line switches providers.
"""
from langchain_core.language_models.chat_models import BaseChatModel

from app.config import settings


def get_llm() -> BaseChatModel:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq

        if not settings.GROQ_API_KEY:
            raise ValueError("LLM_PROVIDER=groq but GROQ_API_KEY is not set in .env")
        return ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0,
            # Free tier rate-limits (HTTP 429); retry with backoff instead of failing.
            max_retries=3,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER!r} (use 'groq' or 'ollama')")


def model_name() -> str:
    """Model id for API responses / CLI display."""
    if settings.LLM_PROVIDER.lower() == "groq":
        return settings.GROQ_MODEL
    return settings.OLLAMA_MODEL
