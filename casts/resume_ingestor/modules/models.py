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
    """Returns a configured LangChain chat model, or None if unavailable.

    Configuration (all optional):
    - INTERVIEWGRAPH_LLM_PROVIDER (default: openai)
    - INTERVIEWGRAPH_LLM_MODEL (default: gpt-4o-mini)
    - INTERVIEWGRAPH_LLM_TEMPERATURE (default: 0.2)
    """

    provider = os.getenv("INTERVIEWGRAPH_LLM_PROVIDER", "openai").strip().lower()
    model = os.getenv("INTERVIEWGRAPH_LLM_MODEL", "gpt-4o-mini").strip()
    temp_raw = os.getenv("INTERVIEWGRAPH_LLM_TEMPERATURE", "0.2").strip()

    if not _has_provider_credentials(provider):
        return None

    try:
        temperature = float(temp_raw)
    except ValueError:
        temperature = 0.2

    try:
        from langchain.chat_models import init_chat_model

        return init_chat_model(
            model=model,
            model_provider=provider,
            temperature=temperature,
        )
    except Exception:
        return None


def _has_provider_credentials(provider: str) -> bool:
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY", "").strip())
    if provider == "anthropic":
        return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    return False
