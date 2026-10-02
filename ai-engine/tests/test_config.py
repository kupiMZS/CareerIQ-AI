import pytest
from pydantic import ValidationError

from app.core.config import (
    Settings,
    get_settings,
)


def test_settings_have_safe_defaults():
    settings = Settings(
        _env_file=None,
    )

    assert settings.ai_provider == "rule_based"
    assert settings.ai_model == "rule-based-v1"
    assert settings.ai_timeout_seconds == 30.0
    assert settings.ai_max_retries == 2
    assert settings.ai_fallback_enabled is True
    assert settings.ai_fallback_provider == "rule_based"


def test_settings_can_be_loaded_from_environment(
    monkeypatch,
):
    monkeypatch.setenv(
        "AI_PROVIDER",
        "local",
    )

    monkeypatch.setenv(
        "AI_MODEL",
        "local-test-model",
    )

    monkeypatch.setenv(
        "AI_TIMEOUT_SECONDS",
        "45",
    )

    monkeypatch.setenv(
        "AI_MAX_RETRIES",
        "3",
    )

    monkeypatch.setenv(
        "AI_FALLBACK_ENABLED",
        "false",
    )

    settings = Settings(
        _env_file=None,
    )

    assert settings.ai_provider == "local"
    assert settings.ai_model == "local-test-model"
    assert settings.ai_timeout_seconds == 45.0
    assert settings.ai_max_retries == 3
    assert settings.ai_fallback_enabled is False


def test_settings_reject_invalid_provider():
    with pytest.raises(ValidationError):
        Settings(
            ai_provider="invalid",
            _env_file=None,
        )


def test_settings_reject_non_positive_timeout():
    with pytest.raises(ValidationError):
        Settings(
            ai_timeout_seconds=0,
            _env_file=None,
        )


def test_settings_reject_negative_retry_count():
    with pytest.raises(ValidationError):
        Settings(
            ai_max_retries=-1,
            _env_file=None,
        )


def test_get_settings_is_cached():
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second

    get_settings.cache_clear()
