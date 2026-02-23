"""[Optional] Model configuration helpers for the Resume Ingestor graph.

Guidelines:
    - Provide factory functions for LLMs or embeddings.
    - Accept environment variables or configuration values when necessary.

Official document URL:
    - Models: https://docs.langchain.com/oss/python/langchain/models
    - Chat Models: https://docs.langchain.com/oss/python/integrations/chat
    - Embedding Models: https://docs.langchain.com/oss/python/integrations/text_embedding
"""

from __future__ import annotations

import os
from typing import Any


def get_generation_model() -> Any | None:
    model, _reason = get_generation_model_with_reason()
    return model


def get_generation_model_with_reason() -> tuple[Any | None, str]:
    """Returns a configured LangChain chat model, or None if unavailable.

    Configuration (all optional):
    - INTERVIEWGRAPH_LLM_PROVIDER (default: openai)
    - INTERVIEWGRAPH_LLM_MODEL (default: gpt-4o-mini)
    - INTERVIEWGRAPH_LLM_TEMPERATURE (default: 0.2)
    """

    provider = _provider_name()
    temp_raw = os.getenv("INTERVIEWGRAPH_LLM_TEMPERATURE", "0.2").strip()

    if not _has_provider_credentials(provider):
        return None, "missing_credentials"

    try:
        temperature = float(temp_raw)
    except ValueError:
        temperature = 0.2

    if provider == "ollama":
        ollama_model = _ollama_model_name()
        base_url = os.getenv("INTERVIEWGRAPH_OLLAMA_BASE_URL", "").strip()
        try:
            from langchain_ollama import ChatOllama

            kwargs: dict[str, object] = {
                "model": ollama_model,
                "temperature": temperature,
            }
            if base_url:
                kwargs["base_url"] = base_url
            return ChatOllama(**kwargs), "ready"
        except Exception as exc:
            return None, f"ollama_init_error:{type(exc).__name__}"

    model = os.getenv("INTERVIEWGRAPH_LLM_MODEL", "gpt-4o-mini").strip()
    try:
        from langchain.chat_models import init_chat_model

        model_obj = init_chat_model(
            model=model,
            model_provider=provider,
            temperature=temperature,
        )
        return model_obj, "ready"
    except Exception as exc:
        return None, f"provider_init_error:{type(exc).__name__}"


def _provider_name() -> str:
    return os.getenv("INTERVIEWGRAPH_LLM_PROVIDER", "openai").strip().lower()


def _ollama_model_name() -> str:
    explicit = os.getenv("INTERVIEWGRAPH_OLLAMA_MODEL", "").strip()
    if explicit:
        return explicit

    generic = os.getenv("INTERVIEWGRAPH_LLM_MODEL", "").strip()
    if generic:
        return generic

    return "llama3.1:8b"


def _has_provider_credentials(provider: str) -> bool:
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY", "").strip())
    if provider == "anthropic":
        return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    if provider == "ollama":
        return True
    return False
