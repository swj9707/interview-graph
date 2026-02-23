from __future__ import annotations

import pytest

from casts.resume_ingestor.modules import models


def test_openai_provider_requires_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert models._has_provider_credentials("openai") is False


def test_ollama_provider_does_not_require_key() -> None:
    assert models._has_provider_credentials("ollama") is True


def test_ollama_model_name_prefers_dedicated_env(monkeypatch) -> None:
    monkeypatch.setenv("INTERVIEWGRAPH_OLLAMA_MODEL", "llama3.2:latest")
    monkeypatch.setenv("INTERVIEWGRAPH_LLM_MODEL", "ignored-model")
    assert models._ollama_model_name() == "llama3.2:latest"


def test_generation_model_returns_none_without_required_key(monkeypatch) -> None:
    monkeypatch.setenv("INTERVIEWGRAPH_LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert models.get_generation_model() is None


def test_generation_model_builds_ollama_instance(monkeypatch) -> None:
    pytest.importorskip("langchain_ollama")
    monkeypatch.setenv("INTERVIEWGRAPH_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("INTERVIEWGRAPH_OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setenv("INTERVIEWGRAPH_OLLAMA_BASE_URL", "http://127.0.0.1:11434")

    model = models.get_generation_model()
    assert model is not None
