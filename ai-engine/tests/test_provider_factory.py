import pytest

from app.core import Settings
from app.providers.factory import (
    ProviderFactoryError,
    create_orchestrator,
    create_provider,
)
from app.providers.ollama import OllamaProvider
from app.providers.rule_based import RuleBasedProvider


def build_settings(
    **overrides,
) -> Settings:
    values = {
        "ai_provider": "rule_based",
        "ai_model": "test-model",
        "ai_base_url": "http://ollama.test:11434",
        "ai_request_path": "/api/chat",
        "ai_timeout_seconds": 30,
        "ai_max_retries": 2,
        "ai_retry_backoff_seconds": 0.5,
        "ai_fallback_enabled": True,
        "ai_fallback_provider": "rule_based",
    }

    values.update(overrides)

    return Settings(**values)


def test_factory_creates_rule_based_provider():
    settings = build_settings()

    provider = create_provider(
        "rule_based",
        settings,
    )

    assert isinstance(
        provider,
        RuleBasedProvider,
    )


def test_factory_creates_local_ollama_provider():
    settings = build_settings(
        ai_provider="local",
    )

    provider = create_provider(
        "local",
        settings,
    )

    assert isinstance(
        provider,
        OllamaProvider,
    )

    assert provider.base_url == "http://ollama.test:11434"

    assert provider.model == "test-model"
    assert provider.request_path == "/api/chat"
    assert provider.timeout_seconds == 30


def test_factory_rejects_unimplemented_cloud_provider():
    settings = build_settings()

    with pytest.raises(
        ProviderFactoryError,
        match="not implemented yet",
    ):
        create_provider(
            "cloud",
            settings,
        )


def test_factory_creates_default_orchestrator():
    settings = build_settings()

    orchestrator = create_orchestrator(settings)

    assert isinstance(
        orchestrator.primary_provider,
        RuleBasedProvider,
    )

    assert orchestrator.fallback_provider is None
    assert orchestrator.max_retries == 2

    assert orchestrator.retry_backoff_seconds == 0.5


def test_factory_creates_local_provider_with_rule_fallback():
    settings = build_settings(
        ai_provider="local",
        ai_fallback_enabled=True,
        ai_fallback_provider="rule_based",
    )

    orchestrator = create_orchestrator(settings)

    assert isinstance(
        orchestrator.primary_provider,
        OllamaProvider,
    )

    assert isinstance(
        orchestrator.fallback_provider,
        RuleBasedProvider,
    )


def test_factory_disables_fallback_when_configured():
    settings = build_settings(
        ai_provider="local",
        ai_fallback_enabled=False,
    )

    orchestrator = create_orchestrator(settings)

    assert isinstance(
        orchestrator.primary_provider,
        OllamaProvider,
    )

    assert orchestrator.fallback_provider is None
