import pytest

from app.providers.base import ResumeAnalysisProvider
from app.schemas.resume import (
    Candidate,
    ResumeIntelligence,
    Skill,
)
from evals.runner import run_resume_benchmark
from evals.schemas import (
    ExpectedResumeExtraction,
    ResumeEvalCase,
)


class StaticProvider(ResumeAnalysisProvider):
    def __init__(
        self,
        result: ResumeIntelligence,
    ):
        self.result = result
        self.calls = 0

    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        self.calls += 1

        return self.result


def build_case(
    case_id: str,
    expected: ExpectedResumeExtraction,
) -> ResumeEvalCase:
    return ResumeEvalCase(
        case_id=case_id,
        description="Synthetic benchmark case.",
        resume_text="Synthetic resume",
        expected=expected,
    )


@pytest.mark.anyio
async def test_runner_produces_perfect_aggregate_score():
    provider = StaticProvider(
        ResumeIntelligence(
            candidate=Candidate(
                name="John Doe",
                email="john@example.com",
            ),
            skills=[
                Skill(name="Python"),
            ],
        )
    )

    cases = [
        build_case(
            "case-one",
            ExpectedResumeExtraction(
                name="John Doe",
                email="john@example.com",
                skills=[
                    "Python",
                ],
            ),
        ),
        build_case(
            "case-two",
            ExpectedResumeExtraction(
                name="John Doe",
                email="john@example.com",
                skills=[
                    "Python",
                ],
            ),
        ),
    ]

    summary = await run_resume_benchmark(
        provider_name="test",
        provider=provider,
        cases=cases,
    )

    assert provider.calls == 2
    assert summary.case_count == 2
    assert summary.name_accuracy == 1.0
    assert summary.email_accuracy == 1.0
    assert summary.skills_f1 == 1.0
    assert summary.education_f1 == 1.0
    assert summary.experience_f1 == 1.0
    assert summary.overall_mean == 1.0


@pytest.mark.anyio
async def test_runner_averages_case_scores():
    provider = StaticProvider(
        ResumeIntelligence(
            candidate=Candidate(
                name="John Doe",
            )
        )
    )

    cases = [
        build_case(
            "match",
            ExpectedResumeExtraction(
                name="John Doe",
            ),
        ),
        build_case(
            "mismatch",
            ExpectedResumeExtraction(
                name="Jane Doe",
            ),
        ),
    ]

    summary = await run_resume_benchmark(
        provider_name="test",
        provider=provider,
        cases=cases,
    )

    assert summary.name_accuracy == 0.5


@pytest.mark.anyio
async def test_runner_preserves_case_ids():
    provider = StaticProvider(ResumeIntelligence())

    cases = [
        build_case(
            "first-case",
            ExpectedResumeExtraction(),
        ),
        build_case(
            "second-case",
            ExpectedResumeExtraction(),
        ),
    ]

    summary = await run_resume_benchmark(
        provider_name="test",
        provider=provider,
        cases=cases,
    )

    assert [result.case_id for result in summary.cases] == [
        "first-case",
        "second-case",
    ]


@pytest.mark.anyio
async def test_runner_rejects_empty_dataset():
    provider = StaticProvider(ResumeIntelligence())

    with pytest.raises(
        ValueError,
        match="at least one evaluation case",
    ):
        await run_resume_benchmark(
            provider_name="test",
            provider=provider,
            cases=[],
        )
