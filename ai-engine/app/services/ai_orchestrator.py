import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

from app.providers.base import ResumeAnalysisProvider
from app.providers.errors import (
    ProviderError,
    is_retryable_provider_error,
)
from app.schemas.resume import ResumeIntelligence

logger = logging.getLogger(__name__)

SleepFunction = Callable[
    [float],
    Awaitable[None],
]


class AIOrchestrator:
    """
    Coordinates resume analysis providers.

    Retryable failures from the primary provider
    are retried with exponential backoff before
    the configured fallback provider is used.

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
        retry_backoff_seconds: float = 0.0,
        sleep_func: SleepFunction = asyncio.sleep,
    ):
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.sleep_func = sleep_func

    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        max_attempts = self.max_retries + 1

        primary_name = type(self.primary_provider).__name__

        for attempt in range(
            1,
            max_attempts + 1,
        ):
            started_at = time.perf_counter()

            try:
                result = await self.primary_provider.analyze_resume(resume_text)

            except ProviderError as exception:
                latency_ms = (time.perf_counter() - started_at) * 1000

                retrying = (
                    is_retryable_provider_error(exception) and attempt < max_attempts
                )

                retry_delay = 0.0

                if retrying:
                    retry_delay = self.retry_backoff_seconds * (2 ** (attempt - 1))

                logger.warning(
                    "AI primary provider failed "
                    "provider=%s "
                    "error=%s "
                    "attempt=%d "
                    "max_attempts=%d "
                    "latency_ms=%.2f "
                    "retrying=%s "
                    "retry_delay_seconds=%.2f",
                    primary_name,
                    type(exception).__name__,
                    attempt,
                    max_attempts,
                    latency_ms,
                    retrying,
                    retry_delay,
                )

                if retrying:
                    if retry_delay > 0:
                        await self.sleep_func(retry_delay)

                    continue

                if self.fallback_provider is None:
                    raise

                fallback_name = type(self.fallback_provider).__name__

                logger.warning(
                    "AI fallback provider activated "
                    "primary_provider=%s "
                    "fallback_provider=%s "
                    "error=%s",
                    primary_name,
                    fallback_name,
                    type(exception).__name__,
                )

                fallback_started_at = time.perf_counter()

                fallback_result = await self.fallback_provider.analyze_resume(
                    resume_text
                )

                fallback_latency_ms = (time.perf_counter() - fallback_started_at) * 1000

                logger.info(
                    "AI fallback provider succeeded provider=%s latency_ms=%.2f",
                    fallback_name,
                    fallback_latency_ms,
                )

                return fallback_result

            latency_ms = (time.perf_counter() - started_at) * 1000

            logger.info(
                "AI primary provider succeeded provider=%s attempt=%d latency_ms=%.2f",
                primary_name,
                attempt,
                latency_ms,
            )

            return result

        raise RuntimeError("AI orchestration reached an unreachable state.")
