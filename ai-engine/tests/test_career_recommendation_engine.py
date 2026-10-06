from app.schemas.career import (
    CareerProfile,
    CareerRecommendationRequest,
)
from app.services.career_recommendation_engine import (
    CareerRecommendationEngine,
)


def test_engine_ranks_backend_engineer_for_matching_skills():
    engine = CareerRecommendationEngine()

    response = engine.recommend(
        CareerRecommendationRequest(
            skills=[
                "Python",
                "FastAPI",
                "PostgreSQL",
                "Docker",
            ],
        )
    )

    assert response.status == "ok"
    assert response.recommendations

    recommendation = response.recommendations[0]

    assert recommendation.career_title == "Backend Engineer"

    assert recommendation.match_score == 1.0

    assert recommendation.matched_skills == [
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
    ]

    assert recommendation.missing_skills == []


def test_engine_identifies_skill_gaps():
    engine = CareerRecommendationEngine()

    response = engine.recommend(
        CareerRecommendationRequest(
            skills=[
                "Python",
                "FastAPI",
            ],
        )
    )

    recommendation = response.recommendations[0]

    assert recommendation.career_title == "Backend Engineer"

    assert recommendation.matched_skills == [
        "Python",
        "FastAPI",
    ]

    assert recommendation.missing_skills == [
        "PostgreSQL",
        "Docker",
    ]


def test_engine_changes_ranking_for_different_career_goal():
    engine = CareerRecommendationEngine()

    backend_response = engine.recommend(
        CareerRecommendationRequest(
            profile=CareerProfile(
                career_goal=("Backend Engineer"),
            ),
            skills=[
                "Python",
                "PostgreSQL",
            ],
        )
    )

    data_response = engine.recommend(
        CareerRecommendationRequest(
            profile=CareerProfile(
                career_goal="Data Engineer",
            ),
            skills=[
                "Python",
                "PostgreSQL",
            ],
        )
    )

    assert backend_response.recommendations[0].career_title == "Backend Engineer"

    assert data_response.recommendations[0].career_title == "Data Engineer"


def test_engine_marks_results_entry_level_when_no_experience():
    engine = CareerRecommendationEngine()

    response = engine.recommend(
        CareerRecommendationRequest(
            profile=CareerProfile(
                years_experience=0,
            ),
            skills=[
                "Python",
                "FastAPI",
                "PostgreSQL",
                "Docker",
            ],
        )
    )

    assert response.status == "ok"

    assert all(
        recommendation.entry_level for recommendation in response.recommendations
    )

    assert "entry-level" in response.recommendations[0].rationale


def test_engine_generates_roadmap_from_missing_skills():
    engine = CareerRecommendationEngine()

    response = engine.recommend(
        CareerRecommendationRequest(
            skills=[
                "Python",
                "FastAPI",
            ],
        )
    )

    assert response.status == "ok"

    assert [step.skills for step in response.roadmap] == [
        ["PostgreSQL"],
        ["Docker"],
    ]

    assert [step.step for step in response.roadmap] == [
        1,
        2,
    ]


def test_engine_generates_portfolio_step_when_no_skill_gap():
    engine = CareerRecommendationEngine()

    response = engine.recommend(
        CareerRecommendationRequest(
            skills=[
                "Python",
                "FastAPI",
                "PostgreSQL",
                "Docker",
            ],
        )
    )

    assert len(response.roadmap) == 1
    assert response.roadmap[0].step == 1

    assert response.roadmap[0].title == "Build a role-focused portfolio project"


def test_engine_requests_more_information_for_empty_input():
    engine = CareerRecommendationEngine()

    response = engine.recommend(CareerRecommendationRequest())

    assert response.status == "needs_more_information"

    assert response.recommendations == []
    assert response.roadmap == []

    assert response.missing_information == [
        "skills",
        "career_goal",
    ]


def test_engine_matches_skills_case_insensitively_without_duplicates():
    engine = CareerRecommendationEngine()

    response = engine.recommend(
        CareerRecommendationRequest(
            skills=[
                "python",
                "FASTAPI",
                "Python",
                "postgresql",
                "docker",
            ],
        )
    )

    recommendation = response.recommendations[0]

    assert recommendation.career_title == "Backend Engineer"

    assert recommendation.matched_skills == [
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
    ]


def test_engine_is_deterministic_for_same_input():
    engine = CareerRecommendationEngine()

    request = CareerRecommendationRequest(
        profile=CareerProfile(
            career_goal="Data Engineer",
            years_experience=2,
        ),
        skills=[
            "Python",
            "SQL",
            "PostgreSQL",
        ],
    )

    first = engine.recommend(request)
    second = engine.recommend(request)

    assert first.model_dump() == second.model_dump()
