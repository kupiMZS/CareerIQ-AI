from app.core import ProviderName, Settings
from app.providers.base import ResumeAnalysisProvider
from app.providers.ollama import OllamaProvider
from app.providers.rule_based import RuleBasedProvider
from app.services.ai_orchestrator import AIOrchestrator


class ProviderFactoryError(RuntimeError):
    """
    Raised when CareerIQ cannot create a configured
    resume-analysis provider.
    """


def create_provider(
    provider_name: ProviderName,
    settings: Settings,
) -> ResumeAnalysisProvider:
    if provider_name == "rule_based":
        return RuleBasedProvider()

    if provider_name == "local":
        return OllamaProvider(
            base_url=settings.ai_base_url,
            model=settings.ai_model,
            request_path=settings.ai_request_path,
            timeout_seconds=settings.ai_timeout_seconds,
        )

    raise ProviderFactoryError(f"Provider '{provider_name}' is not implemented yet.")


def create_orchestrator(
    settings: Settings,
) -> AIOrchestrator:
    primary_provider = create_provider(
        settings.ai_provider,
        settings,
    )

    fallback_provider = None

    if (
        settings.ai_fallback_enabled
        and settings.ai_fallback_provider != settings.ai_provider
    ):
        fallback_provider = create_provider(
            settings.ai_fallback_provider,
            settings,
        )

    return AIOrchestrator(
        primary_provider=primary_provider,
        fallback_provider=fallback_provider,
        max_retries=settings.ai_max_retries,
        retry_backoff_seconds=(settings.ai_retry_backoff_seconds),
    )
