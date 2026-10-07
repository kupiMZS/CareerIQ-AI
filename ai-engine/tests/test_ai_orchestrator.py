import logging
from collections.abc import Callable

import pytest

from app.providers.base import ResumeAnalysisProvider
from app.providers.errors import (
    ProviderConnectionError,
    ProviderError,
    ProviderHTTPError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.schemas.resume import (
    Candidate,
    ResumeIntelligence,
)
from app.services import AIOrchestrator


class SuccessfulProvider(ResumeAnalysisProvider):
    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        return ResumeIntelligence(
            candidate=Candidate(
                name="Primary Provider Candidate",
            )
        )


class FailingProvider(ResumeAnalysisProvider):
    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        raise ProviderConnectionError("Primary provider failed")


class UnexpectedBugProvider(ResumeAnalysisProvider):
    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        raise RuntimeError("Unexpected programming bug")


class FallbackProvider(ResumeAnalysisProvider):
    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        return ResumeIntelligence(
            candidate=Candidate(
                name="Fallback Candidate",
            )
        )


class FlakyProvider(ResumeAnalysisProvider):
    def __init__(
        self,
        failures_before_success: int,
        error_factory: Callable[
            [],
            ProviderError,
        ],
    ):
        self.failures_before_success = failures_before_success
        self.error_factory = error_factory
        self.attempts = 0

    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        self.attempts += 1

        if self.attempts <= self.failures_before_success:
            raise self.error_factory()

        return ResumeIntelligence(
            candidate=Candidate(
                name="Recovered Candidate",
            )
        )


class RecordingSleeper:
    def __init__(self):
        self.delays: list[float] = []

    async def __call__(
        self,
        delay: float,
    ) -> None:
        self.delays.append(delay)


@pytest.mark.anyio
async def test_orchestrator_uses_primary_provider():
    orchestrator = AIOrchestrator(
        primary_provider=SuccessfulProvider(),
        fallback_provider=FallbackProvider(),
    )

    result = await orchestrator.analyze_resume("John Doe Software Engineer")

    assert result.candidate.name == "Primary Provider Candidate"


@pytest.mark.anyio
async def test_orchestrator_uses_fallback_when_primary_fails():
    orchestrator = AIOrchestrator(
        primary_provider=FailingProvider(),
        fallback_provider=FallbackProvider(),
    )

    result = await orchestrator.analyze_resume("John Doe Software Engineer")

    assert result.candidate.name == "Fallback Candidate"


@pytest.mark.anyio
async def test_orchestrator_reraises_when_no_fallback_exists():
    orchestrator = AIOrchestrator(primary_provider=FailingProvider())

    with pytest.raises(
        ProviderConnectionError,
        match="Primary provider failed",
    ):
        await orchestrator.analyze_resume("John Doe Software Engineer")


@pytest.mark.anyio
async def test_orchestrator_does_not_swallow_unexpected_errors():
    orchestrator = AIOrchestrator(
        primary_provider=UnexpectedBugProvider(),
        fallback_provider=FallbackProvider(),
        max_retries=2,
    )

    with pytest.raises(
        RuntimeError,
        match="Unexpected programming bug",
    ):
        await orchestrator.analyze_resume("John Doe Software Engineer")


@pytest.mark.anyio
async def test_orchestrator_retries_connection_error():
    provider = FlakyProvider(
        failures_before_success=2,
        error_factory=lambda: ProviderConnectionError("Connection failed"),
    )

    orchestrator = AIOrchestrator(
        primary_provider=provider,
        max_retries=2,
    )

    result = await orchestrator.analyze_resume("John Doe Software Engineer")

    assert provider.attempts == 3

    assert result.candidate.name == "Recovered Candidate"


@pytest.mark.anyio
async def test_orchestrator_retries_timeout_error():
    provider = FlakyProvider(
        failures_before_success=1,
        error_factory=lambda: ProviderTimeoutError("Request timed out"),
    )

    orchestrator = AIOrchestrator(
        primary_provider=provider,
        max_retries=2,
    )

    result = await orchestrator.analyze_resume("John Doe Software Engineer")

    assert provider.attempts == 2

    assert result.candidate.name == "Recovered Candidate"


@pytest.mark.anyio
async def test_orchestrator_retries_retryable_http_error():
    provider = FlakyProvider(
        failures_before_success=1,
        error_factory=lambda: ProviderHTTPError(
            "Service unavailable",
            status_code=503,
        ),
    )

    orchestrator = AIOrchestrator(
        primary_provider=provider,
        max_retries=2,
    )

    result = await orchestrator.analyze_resume("John Doe Software Engineer")

    assert provider.attempts == 2

    assert result.candidate.name == "Recovered Candidate"


@pytest.mark.anyio
async def test_orchestrator_does_not_retry_non_retryable_http_error():
    provider = FlakyProvider(
        failures_before_success=10,
        error_factory=lambda: ProviderHTTPError(
            "Bad request",
            status_code=400,
        ),
    )

    orchestrator = AIOrchestrator(
        primary_provider=provider,
        fallback_provider=FallbackProvider(),
        max_retries=2,
    )

    result = await orchestrator.analyze_resume("John Doe Software Engineer")

    assert provider.attempts == 1

    assert result.candidate.name == "Fallback Candidate"


@pytest.mark.anyio
async def test_orchestrator_does_not_retry_response_error():
    provider = FlakyProvider(
        failures_before_success=10,
        error_factory=lambda: ProviderResponseError("Invalid provider response"),
    )

    sleeper = RecordingSleeper()

    orchestrator = AIOrchestrator(
        primary_provider=provider,
        fallback_provider=FallbackProvider(),
        max_retries=2,
        retry_backoff_seconds=0.5,
        sleep_func=sleeper,
    )

    result = await orchestrator.analyze_resume("John Doe Software Engineer")

    assert provider.attempts == 1
    assert sleeper.delays == []

    assert result.candidate.name == "Fallback Candidate"


@pytest.mark.anyio
async def test_orchestrator_falls_back_after_retries_exhausted():
    provider = FlakyProvider(
        failures_before_success=10,
        error_factory=lambda: ProviderConnectionError("Connection failed"),
    )

    orchestrator = AIOrchestrator(
        primary_provider=provider,
        fallback_provider=FallbackProvider(),
        max_retries=2,
    )

    result = await orchestrator.analyze_resume("John Doe Software Engineer")

    assert provider.attempts == 3

    assert result.candidate.name == "Fallback Candidate"


@pytest.mark.anyio
async def test_orchestrator_uses_exponential_retry_backoff(
    caplog: pytest.LogCaptureFixture,
):
    provider = FlakyProvider(
        failures_before_success=2,
        error_factory=lambda: ProviderConnectionError("Connection failed"),
    )

    sleeper = RecordingSleeper()

    orchestrator = AIOrchestrator(
        primary_provider=provider,
        max_retries=2,
        retry_backoff_seconds=0.5,
        sleep_func=sleeper,
    )

    caplog.set_level(
        logging.INFO,
        logger=("app.services.ai_orchestrator"),
    )

    result = await orchestrator.analyze_resume("John Doe Software Engineer")

    assert provider.attempts == 3

    assert sleeper.delays == [
        0.5,
        1.0,
    ]

    assert result.candidate.name == "Recovered Candidate"

    messages = [record.getMessage() for record in caplog.records]

    assert any(
        "attempt=1" in message
        and "retrying=True" in message
        and "retry_delay_seconds=0.50" in message
        for message in messages
    )

    assert any(
        "attempt=2" in message
        and "retrying=True" in message
        and "retry_delay_seconds=1.00" in message
        for message in messages
    )

    assert any(
        "AI primary provider succeeded" in message and "attempt=3" in message
        for message in messages
    )
