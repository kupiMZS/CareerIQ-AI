import pytest

from app.schemas.career import (
    CareerRecommendation,
    CareerRecommendationResponse,
    LearningRoadmapStep,
)
from evals.schemas import ExpectedCareerRecommendation
from evals.scorer import (
    CAREER_SCORER_VERSION,
    score_career_recommendation,
)


def build_backend_response(
    *,
    entry_level: bool = False,
    missing_skills: list[str] | None = None,
) -> CareerRecommendationResponse:
    gaps = (
        missing_skills
        if missing_skills is not None
        else [
            "PostgreSQL",
            "Docker",
        ]
    )

    return CareerRecommendationResponse(
        status="ok",
        recommendations=[
            CareerRecommendation(
                career_title="Backend Engineer",
                match_score=0.8,
                rationale="Strong backend match.",
                matched_skills=[
                    "Python",
                    "FastAPI",
                ],
                missing_skills=gaps,
                entry_level=entry_level,
            )
        ],
        roadmap=[
            LearningRoadmapStep(
                step=index,
                title=f"Build {skill} proficiency",
                description=f"Learn {skill}.",
                skills=[skill],
            )
            for index, skill in enumerate(
                gaps,
                start=1,
            )
        ],
    )


def build_backend_expected(
    *,
    entry_level: bool = False,
) -> ExpectedCareerRecommendation:
    return ExpectedCareerRecommendation(
        status="ok",
        top_career="Backend Engineer",
        relevant_careers=[
            "Backend Engineer",
        ],
        missing_skills=[
            "PostgreSQL",
            "Docker",
        ],
        roadmap_skills=[
            "PostgreSQL",
            "Docker",
        ],
        entry_level=entry_level,
        missing_information=[],
    )


def test_career_scorer_version():
    assert CAREER_SCORER_VERSION == "career-v1"


def test_career_scorer_gives_perfect_score():
    score = score_career_recommendation(
        build_backend_expected(),
        build_backend_response(),
    )

    assert score.status.score == 1.0
    assert score.top_career.score == 1.0
    assert score.relevant_careers.recall == 1.0
    assert score.missing_skills.f1 == 1.0
    assert score.roadmap_skills.f1 == 1.0
    assert score.entry_level.score == 1.0
    assert score.missing_information.f1 == 1.0
    assert score.overall == 1.0


def test_career_scorer_normalizes_text_and_ignores_collection_order():
    expected = ExpectedCareerRecommendation(
        status="ok",
        top_career=" backend   engineer ",
        relevant_careers=[
            "BACKEND ENGINEER",
        ],
        missing_skills=[
            "docker",
            "POSTGRESQL",
        ],
        roadmap_skills=[
            "DOCKER",
            "postgresql",
        ],
        entry_level=False,
        missing_information=[],
    )

    score = score_career_recommendation(
        expected,
        build_backend_response(),
    )

    assert score.top_career.score == 1.0
    assert score.missing_skills.f1 == 1.0
    assert score.roadmap_skills.f1 == 1.0
    assert score.overall == 1.0


def test_relevant_career_metric_uses_coverage_for_overall():
    actual = build_backend_response()

    actual.recommendations.append(
        CareerRecommendation(
            career_title="Machine Learning Engineer",
            match_score=0.4,
            rationale="Secondary match.",
            matched_skills=[
                "Python",
            ],
            missing_skills=[
                "Machine Learning",
            ],
            entry_level=False,
        )
    )

    score = score_career_recommendation(
        build_backend_expected(),
        actual,
    )

    assert score.relevant_careers.precision == 0.5
    assert score.relevant_careers.recall == 1.0
    assert score.relevant_careers.f1 == pytest.approx(2 / 3)

    assert score.overall == 1.0


def test_career_scorer_penalizes_wrong_skill_gaps():
    actual = build_backend_response(
        missing_skills=[
            "Redis",
        ]
    )

    score = score_career_recommendation(
        build_backend_expected(),
        actual,
    )

    assert score.missing_skills.f1 == 0.0
    assert score.roadmap_skills.f1 == 0.0

    assert score.overall == pytest.approx(5 / 7)


def test_career_scorer_scores_entry_level_behavior():
    score = score_career_recommendation(
        build_backend_expected(
            entry_level=True,
        ),
        build_backend_response(
            entry_level=False,
        ),
    )

    assert score.entry_level.score == 0.0

    assert score.overall == pytest.approx(6 / 7)


def test_career_scorer_gives_perfect_insufficient_data_score():
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

    actual = CareerRecommendationResponse(
        status="needs_more_information",
        recommendations=[],
        roadmap=[],
        missing_information=[
            "career_goal",
            "skills",
        ],
    )

    score = score_career_recommendation(
        expected,
        actual,
    )

    assert score.status.score == 1.0
    assert score.top_career.score == 1.0
    assert score.entry_level.score == 1.0
    assert score.missing_information.f1 == 1.0
    assert score.overall == 1.0


def test_career_scorer_penalizes_wrong_missing_information():
    expected = ExpectedCareerRecommendation(
        status="needs_more_information",
        missing_information=[
            "skills",
        ],
    )

    actual = CareerRecommendationResponse(
        status="needs_more_information",
        missing_information=[
            "career_goal",
        ],
    )

    score = score_career_recommendation(
        expected,
        actual,
    )

    assert score.missing_information.f1 == 0.0

    assert score.overall == pytest.approx(6 / 7)
