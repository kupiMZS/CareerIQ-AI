import pytest

from app.providers.base import ResumeAnalysisProvider
from app.schemas.resume import (
    Candidate,
    Experience,
    ResumeIntelligence,
)
from evals.providers import EnrichedResumeProvider


class RawProvider(ResumeAnalysisProvider):
    def __init__(self):
        self.calls = 0

    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        self.calls += 1

        return ResumeIntelligence(
            candidate=Candidate(
                name="John Doe",
                email=None,
            ),
            experience=[
                Experience(
                    job_title="Software Engineer",
                    company=None,
                )
            ],
        )


@pytest.mark.anyio
async def test_enriched_provider_applies_deterministic_enrichment():
    raw_provider = RawProvider()

    provider = EnrichedResumeProvider(raw_provider)

    result = await provider.analyze_resume(
        "John Doe\n"
        "john.doe@example.com\n\n"
        "Experience\n"
        "Software Engineer at ABC Technologies"
    )

    assert raw_provider.calls == 1

    assert result.candidate.email == "john.doe@example.com"

    assert len(result.experience) == 1

    assert result.experience[0].job_title == "Software Engineer"

    assert result.experience[0].company == "ABC Technologies"


@pytest.mark.anyio
async def test_enriched_provider_preserves_existing_values():
    class ExistingProvider(ResumeAnalysisProvider):
        async def analyze_resume(
            self,
            resume_text: str,
        ) -> ResumeIntelligence:
            return ResumeIntelligence(
                candidate=Candidate(
                    name="John Doe",
                    email="existing@example.com",
                )
            )

    provider = EnrichedResumeProvider(ExistingProvider())

    result = await provider.analyze_resume("John Doe\nbaseline@example.com")

    assert result.candidate.email == "existing@example.com"
