from app.core import ProviderName, Settings
from app.providers.base import ResumeAnalysisProvider
from app.providers.rule_based import RuleBasedProvider
from app.services.ai_orchestrator import AIOrchestrator


class ProviderFactoryError(RuntimeError):
    """
    Raised when CareerIQ cannot create a configured
    resume-analysis provider.
    """


def create_provider(
    provider_name: ProviderName,
) -> ResumeAnalysisProvider:
    if provider_name == "rule_based":
        return RuleBasedProvider()

    raise ProviderFactoryError(f"Provider '{provider_name}' is not implemented yet.")


def create_orchestrator(
    settings: Settings,
) -> AIOrchestrator:
    primary_provider = create_provider(settings.ai_provider)

    fallback_provider = None

    if (
        settings.ai_fallback_enabled
        and settings.ai_fallback_provider != settings.ai_provider
    ):
        fallback_provider = create_provider(settings.ai_fallback_provider)

    return AIOrchestrator(
        primary_provider=primary_provider,
        fallback_provider=fallback_provider,
    )
