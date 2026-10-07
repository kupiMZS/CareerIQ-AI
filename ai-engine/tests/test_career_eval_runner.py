import pytest

from app.schemas.career import (
    CareerRecommendationRequest,
    CareerRecommendationResponse,
)
from app.services.career_recommendation_engine import (
    CareerRecommendationEngine,
)
from evals.runner import run_career_benchmark
from evals.schemas import (
    CareerEvalCase,
    ExpectedCareerRecommendation,
)


class StaticCareerEngine(CareerRecommendationEngine):
    def __init__(
        self,
        result: CareerRecommendationResponse,
    ):
        self.result = result
        self.calls = 0

    def recommend(
        self,
        request: CareerRecommendationRequest,
    ) -> CareerRecommendationResponse:
        self.calls += 1
        return self.result


def build_case(
    case_id: str,
    expected: ExpectedCareerRecommendation,
) -> CareerEvalCase:
    return CareerEvalCase(
        case_id=case_id,
        description="Synthetic career benchmark case.",
        request=CareerRecommendationRequest(),
        expected=expected,
    )


@pytest.mark.anyio
async def test_career_runner_produces_perfect_aggregate_score():
    engine = StaticCareerEngine(
        CareerRecommendationResponse(
            status="needs_more_information",
            recommendations=[],
            roadmap=[],
            missing_information=[
                "skills",
                "career_goal",
            ],
        )
    )

    expected = ExpectedCareerRecommendation(
        status="needs_more_information",
        top_career=None,
        relevant_careers=[],
        missing_skills=[],
        roadmap_skills=[],
        entry_level=None,
        missing_information=[
            "skills",
            "career_goal",
        ],
    )

    cases = [
        build_case(
            "case-one",
            expected,
        ),
        build_case(
            "case-two",
            expected,
        ),
    ]

    summary = await run_career_benchmark(
        engine_name="test",
        engine=engine,
        cases=cases,
    )

    assert engine.calls == 2
    assert summary.engine == "test"
    assert summary.case_count == 2
    assert summary.status_accuracy == 1.0
    assert summary.top_career_accuracy == 1.0
    assert summary.relevant_career_coverage == 1.0
    assert summary.missing_skills_f1 == 1.0
    assert summary.roadmap_skills_f1 == 1.0
    assert summary.entry_level_accuracy == 1.0
    assert summary.missing_information_f1 == 1.0
    assert summary.overall_mean == 1.0


@pytest.mark.anyio
async def test_career_runner_averages_case_scores():
    engine = StaticCareerEngine(
        CareerRecommendationResponse(
            status="needs_more_information",
            recommendations=[],
            roadmap=[],
            missing_information=[
                "skills",
            ],
        )
    )

    cases = [
        build_case(
            "match",
            ExpectedCareerRecommendation(
                status="needs_more_information",
                missing_information=[
                    "skills",
                ],
            ),
        ),
        build_case(
            "mismatch",
            ExpectedCareerRecommendation(
                status="needs_more_information",
                missing_information=[
                    "career_goal",
                ],
            ),
        ),
    ]

    summary = await run_career_benchmark(
        engine_name="test",
        engine=engine,
        cases=cases,
    )

    assert summary.status_accuracy == 1.0
    assert summary.missing_information_f1 == 0.5

    assert summary.overall_mean == pytest.approx(13 / 14)


@pytest.mark.anyio
async def test_career_runner_preserves_case_ids():
    engine = StaticCareerEngine(
        CareerRecommendationResponse(
            status="needs_more_information",
        )
    )

    cases = [
        build_case(
            "first-case",
            ExpectedCareerRecommendation(
                status="needs_more_information",
            ),
        ),
        build_case(
            "second-case",
            ExpectedCareerRecommendation(
                status="needs_more_information",
            ),
        ),
    ]

    summary = await run_career_benchmark(
        engine_name="test",
        engine=engine,
        cases=cases,
    )

    assert [result.case_id for result in summary.cases] == [
        "first-case",
        "second-case",
    ]


@pytest.mark.anyio
async def test_career_runner_rejects_empty_dataset():
    engine = StaticCareerEngine(
        CareerRecommendationResponse(
            status="needs_more_information",
        )
    )

    with pytest.raises(
        ValueError,
        match="at least one evaluation case",
    ):
        await run_career_benchmark(
            engine_name="test",
            engine=engine,
            cases=[],
        )

    assert engine.calls == 0
