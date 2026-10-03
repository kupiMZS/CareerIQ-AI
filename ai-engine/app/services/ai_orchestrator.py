from app.providers.base import ResumeAnalysisProvider
from app.providers.errors import (
    ProviderError,
    is_retryable_provider_error,
)
from app.schemas.resume import ResumeIntelligence


class AIOrchestrator:
    """
    Coordinates resume analysis providers.

    Retryable failures from the primary provider
    are retried before the configured fallback
    provider is used.

    Non-retryable provider failures may trigger
    fallback immediately.

    Unexpected application errors are allowed
    to propagate.
    """

    def __init__(
        self,
        primary_provider: ResumeAnalysisProvider,
        fallback_provider: (ResumeAnalysisProvider | None) = None,
        max_retries: int = 0,
    ):
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.max_retries = max_retries

    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        retry_count = 0

        while True:
            try:
                return await self.primary_provider.analyze_resume(resume_text)

            except ProviderError as exception:
                should_retry = (
                    is_retryable_provider_error(exception)
                    and retry_count < self.max_retries
                )

                if should_retry:
                    retry_count += 1
                    continue

                if self.fallback_provider is None:
                    raise

                return await self.fallback_provider.analyze_resume(resume_text)
