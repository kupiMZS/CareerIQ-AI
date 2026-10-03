import pytest
from pydantic import ValidationError

from app.core.config import (
    Settings,
    get_settings,
)

AI_ENV_VARS = (
    "AI_PROVIDER",
    "AI_MODEL",
    "AI_BASE_URL",
    "AI_REQUEST_PATH",
    "AI_TIMEOUT_SECONDS",
    "AI_MAX_RETRIES",
    "AI_FALLBACK_ENABLED",
    "AI_FALLBACK_PROVIDER",
    "AI_RETRY_BACKOFF_SECONDS",
)


def clear_ai_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for variable in AI_ENV_VARS:
        monkeypatch.delenv(
            variable,
            raising=False,
        )


def test_settings_have_safe_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    clear_ai_environment(monkeypatch)

    settings = Settings()

    assert settings.ai_base_url == "http://localhost:11434"

    assert settings.ai_request_path == "/api/chat"

    assert settings.ai_provider == "rule_based"

    assert settings.ai_model == "rule-based-v1"

    assert settings.ai_timeout_seconds == 30.0

    assert settings.ai_max_retries == 2

    assert settings.ai_retry_backoff_seconds == 0.5

    assert settings.ai_fallback_enabled is True

    assert settings.ai_fallback_provider == "rule_based"


def test_settings_can_be_loaded_from_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    clear_ai_environment(monkeypatch)

    monkeypatch.setenv(
        "AI_PROVIDER",
        "local",
    )

    monkeypatch.setenv(
        "AI_MODEL",
        "local-test-model",
    )

    monkeypatch.setenv(
        "AI_BASE_URL",
        "http://ollama.test:11434",
    )

    monkeypatch.setenv(
        "AI_REQUEST_PATH",
        "/api/chat",
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
        "AI_RETRY_BACKOFF_SECONDS",
        "0.25",
    )

    monkeypatch.setenv(
        "AI_FALLBACK_ENABLED",
        "false",
    )

    monkeypatch.setenv(
        "AI_FALLBACK_PROVIDER",
        "rule_based",
    )

    settings = Settings()

    assert settings.ai_provider == "local"

    assert settings.ai_model == "local-test-model"

    assert settings.ai_base_url == "http://ollama.test:11434"

    assert settings.ai_request_path == "/api/chat"

    assert settings.ai_timeout_seconds == 45.0

    assert settings.ai_max_retries == 3

    assert settings.ai_retry_backoff_seconds == 0.25

    assert settings.ai_fallback_enabled is False

    assert settings.ai_fallback_provider == "rule_based"


def test_settings_reject_invalid_provider(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    clear_ai_environment(monkeypatch)

    monkeypatch.setenv(
        "AI_PROVIDER",
        "invalid",
    )

    with pytest.raises(ValidationError):
        Settings()


def test_settings_reject_non_positive_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    clear_ai_environment(monkeypatch)

    monkeypatch.setenv(
        "AI_TIMEOUT_SECONDS",
        "0",
    )

    with pytest.raises(ValidationError):
        Settings()


def test_settings_reject_negative_retry_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    clear_ai_environment(monkeypatch)

    monkeypatch.setenv(
        "AI_MAX_RETRIES",
        "-1",
    )

    with pytest.raises(ValidationError):
        Settings()


def test_get_settings_is_cached(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    clear_ai_environment(monkeypatch)

    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second

    get_settings.cache_clear()


def test_settings_reject_negative_retry_backoff(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    clear_ai_environment(monkeypatch)

    monkeypatch.setenv(
        "AI_RETRY_BACKOFF_SECONDS",
        "-0.1",
    )

    with pytest.raises(ValidationError):
        Settings()
