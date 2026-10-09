import pytest

from app.providers.base import ResumeAnalysisProvider
from app.schemas.resume import (
    Candidate,
    Language,
    Publication,
    ResumeIntelligence,
    Skill,
)
from evals.runner import run_resume_benchmark
from evals.schemas import (
    ExpectedExtendedResumeExtraction,
    ExpectedLanguage,
    ExpectedPhase2ResumeExtraction,
    ExpectedPublication,
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
    extended_expected: ExpectedExtendedResumeExtraction | None = None,
    phase2_expected: ExpectedPhase2ResumeExtraction | None = None,
) -> ResumeEvalCase:
    return ResumeEvalCase(
        case_id=case_id,
        description="Synthetic benchmark case.",
        resume_text="Synthetic resume",
        expected=expected,
        extended_expected=extended_expected,
        phase2_expected=phase2_expected,
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
                skills=["Python"],
            ),
        ),
        build_case(
            "case-two",
            ExpectedResumeExtraction(
                name="John Doe",
                email="john@example.com",
                skills=["Python"],
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
    assert summary.extended is None
    assert summary.phase2 is None


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


@pytest.mark.anyio
async def test_runner_scores_only_extended_cases():
    provider = StaticProvider(
        ResumeIntelligence(
            candidate=Candidate(
                headline="Backend Engineer",
            )
        )
    )

    cases = [
        build_case(
            "extended",
            ExpectedResumeExtraction(),
            ExpectedExtendedResumeExtraction(
                headline="Backend Engineer",
            ),
        ),
        build_case(
            "core-only",
            ExpectedResumeExtraction(),
        ),
    ]

    summary = await run_resume_benchmark(
        provider_name="test",
        provider=provider,
        cases=cases,
    )

    assert summary.case_count == 2
    assert summary.extended is not None
    assert summary.extended.case_count == 1
    assert summary.extended.headline_accuracy == 1.0
    assert summary.cases[0].extended_score is not None
    assert summary.cases[1].extended_score is None


@pytest.mark.anyio
async def test_runner_averages_extended_scores_separately():
    provider = StaticProvider(
        ResumeIntelligence(
            candidate=Candidate(
                headline="Backend Engineer",
            )
        )
    )

    cases = [
        build_case(
            "match",
            ExpectedResumeExtraction(),
            ExpectedExtendedResumeExtraction(
                headline="Backend Engineer",
            ),
        ),
        build_case(
            "mismatch",
            ExpectedResumeExtraction(),
            ExpectedExtendedResumeExtraction(
                headline="Frontend Engineer",
            ),
        ),
    ]

    summary = await run_resume_benchmark(
        provider_name="test",
        provider=provider,
        cases=cases,
    )

    assert summary.extended is not None
    assert summary.extended.case_count == 2
    assert summary.extended.headline_accuracy == 0.5

    # Core scoring remains independent.
    assert summary.overall_mean == 1.0


@pytest.mark.anyio
async def test_runner_scores_only_phase2_cases():
    provider = StaticProvider(
        ResumeIntelligence(
            publications=[
                Publication(
                    title="Example Publication",
                    authors=["Jane Smith"],
                    venue="Example Journal",
                    date="2025",
                )
            ]
        )
    )

    cases = [
        build_case(
            "phase2-case",
            ExpectedResumeExtraction(),
            phase2_expected=ExpectedPhase2ResumeExtraction(
                publications=[
                    ExpectedPublication(
                        title="Example Publication",
                        authors=["Jane Smith"],
                        venue="Example Journal",
                        date="2025",
                    )
                ]
            ),
        ),
        build_case(
            "core-only-case",
            ExpectedResumeExtraction(),
        ),
    ]

    summary = await run_resume_benchmark(
        provider_name="test",
        provider=provider,
        cases=cases,
    )

    assert summary.phase2 is not None
    assert summary.phase2.scorer_version == "phase2-v1"
    assert summary.phase2.case_count == 1
    assert summary.phase2.publications_f1 == 1.0
    assert summary.phase2.languages_f1 is None
    assert summary.phase2.overall_mean == 1.0

    assert summary.cases[0].phase2_score is not None
    assert summary.cases[1].phase2_score is None

    assert summary.overall_mean == 1.0


@pytest.mark.anyio
async def test_runner_averages_phase2_scores():
    provider = StaticProvider(
        ResumeIntelligence(
            publications=[
                Publication(
                    title="Matched Publication",
                )
            ]
        )
    )

    cases = [
        build_case(
            "phase2-match",
            ExpectedResumeExtraction(),
            phase2_expected=ExpectedPhase2ResumeExtraction(
                publications=[
                    ExpectedPublication(
                        title="Matched Publication",
                    )
                ]
            ),
        ),
        build_case(
            "phase2-mismatch",
            ExpectedResumeExtraction(),
            phase2_expected=ExpectedPhase2ResumeExtraction(
                publications=[
                    ExpectedPublication(
                        title="Different Publication",
                    )
                ]
            ),
        ),
    ]

    summary = await run_resume_benchmark(
        provider_name="test",
        provider=provider,
        cases=cases,
    )

    assert summary.phase2 is not None
    assert summary.phase2.case_count == 2
    assert summary.phase2.publications_f1 == 0.5
    assert summary.phase2.overall_mean == 0.5


@pytest.mark.anyio
async def test_runner_routes_language_expectations_to_phase2_v2():
    provider = StaticProvider(
        ResumeIntelligence(
            languages=[
                Language(
                    name="English",
                    proficiency="Fluent",
                )
            ]
        )
    )

    cases = [
        build_case(
            "phase2-language-case",
            ExpectedResumeExtraction(),
            phase2_expected=ExpectedPhase2ResumeExtraction(
                languages=[
                    ExpectedLanguage(
                        name="English",
                        proficiency="Fluent",
                    )
                ]
            ),
        )
    ]

    summary = await run_resume_benchmark(
        provider_name="test",
        provider=provider,
        cases=cases,
    )

    assert summary.phase2 is not None
    assert summary.phase2.scorer_version == "phase2-v2"
    assert summary.phase2.case_count == 1
    assert summary.phase2.publications_f1 is None
    assert summary.phase2.languages_f1 == 1.0
    assert summary.phase2.overall_mean == 1.0


@pytest.mark.anyio
async def test_runner_rejects_mixed_phase2_scorer_versions():
    provider = StaticProvider(ResumeIntelligence())

    cases = [
        build_case(
            "phase2-publication-v1",
            ExpectedResumeExtraction(),
            phase2_expected=ExpectedPhase2ResumeExtraction(
                publications=[],
            ),
        ),
        build_case(
            "phase2-language-v2",
            ExpectedResumeExtraction(),
            phase2_expected=ExpectedPhase2ResumeExtraction(
                languages=[],
            ),
        ),
    ]

    with pytest.raises(
        ValueError,
        match="same Phase 2 scorer version",
    ):
        await run_resume_benchmark(
            provider_name="test",
            provider=provider,
            cases=cases,
        )
