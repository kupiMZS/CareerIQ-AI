import pytest

from app.providers.base import (
    ResumeAnalysisProvider,
)
from app.providers.errors import (
    ProviderConnectionError,
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
                name=("Primary Provider Candidate"),
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
    )

    with pytest.raises(
        RuntimeError,
        match="Unexpected programming bug",
    ):
        await orchestrator.analyze_resume("John Doe Software Engineer")
