import pytest

from app.core import Settings
from app.providers.factory import (
    ProviderFactoryError,
    create_orchestrator,
    create_provider,
)
from app.providers.rule_based import RuleBasedProvider


def test_factory_creates_rule_based_provider():
    provider = create_provider("rule_based")

    assert isinstance(
        provider,
        RuleBasedProvider,
    )


def test_factory_rejects_unimplemented_local_provider():
    with pytest.raises(
        ProviderFactoryError,
        match="not implemented yet",
    ):
        create_provider("local")


def test_factory_rejects_unimplemented_cloud_provider():
    with pytest.raises(
        ProviderFactoryError,
        match="not implemented yet",
    ):
        create_provider("cloud")


def test_factory_creates_default_orchestrator():
    settings = Settings(
        _env_file=None,
    )

    orchestrator = create_orchestrator(settings)

    assert isinstance(
        orchestrator.primary_provider,
        RuleBasedProvider,
    )

    assert orchestrator.fallback_provider is None


def test_factory_disables_fallback_when_configured():
    settings = Settings(
        ai_provider="rule_based",
        ai_fallback_enabled=False,
        _env_file=None,
    )

    orchestrator = create_orchestrator(settings)

    assert isinstance(
        orchestrator.primary_provider,
        RuleBasedProvider,
    )

    assert orchestrator.fallback_provider is None
