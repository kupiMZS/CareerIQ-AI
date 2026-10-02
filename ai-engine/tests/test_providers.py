import pytest

from app.providers import (
    LLMProvider,
    ResumeAnalysisProvider,
)
from app.schemas.resume import (
    Candidate,
    ResumeIntelligence,
    Skill,
)


class TestProvider(LLMProvider):
    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        return ResumeIntelligence(
            candidate=Candidate(
                name="John Doe",
                email="john.doe@example.com",
                headline="Software Engineer",
            ),
            skills=[
                Skill(
                    name="Python",
                    confidence=0.95,
                )
            ],
        )


def test_resume_analysis_provider_is_abstract():
    with pytest.raises(TypeError):
        ResumeAnalysisProvider()


def test_llm_provider_is_abstract():
    with pytest.raises(TypeError):
        LLMProvider()


@pytest.mark.anyio
async def test_concrete_provider_returns_resume_intelligence():
    provider = TestProvider()

    result = await provider.analyze_resume("John Doe Python Software Engineer")

    assert isinstance(
        result,
        ResumeIntelligence,
    )

    assert result.candidate.name == "John Doe"

    assert len(result.skills) == 1

    assert result.skills[0].name == "Python"

    assert result.skills[0].confidence == 0.95
