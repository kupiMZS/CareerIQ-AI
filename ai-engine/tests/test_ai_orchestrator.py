import pytest

from app.providers.base import ResumeAnalysisProvider
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
        raise RuntimeError("Primary provider failed")


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
        RuntimeError,
        match="Primary provider failed",
    ):
        await orchestrator.analyze_resume("John Doe Software Engineer")
