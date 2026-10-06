import pytest
from pydantic import ValidationError

from app.schemas.career import (
    CareerProfile,
    CareerRecommendation,
    CareerRecommendationRequest,
    CareerRecommendationResponse,
    LearningRoadmapStep,
)


def test_career_recommendation_request_supports_complete_profile():
    request = CareerRecommendationRequest(
        profile=CareerProfile(
            current_role=" Backend Engineer ",
            career_goal=" Data Engineer ",
            years_experience=3,
            education=[
                "BSc Computer Science",
            ],
            interests=[
                "Data platforms",
            ],
        ),
        skills=[
            "Python",
            "FastAPI",
            "PostgreSQL",
        ],
    )

    assert request.profile.current_role == "Backend Engineer"

    assert request.profile.career_goal == "Data Engineer"

    assert request.profile.years_experience == 3

    assert request.skills == [
        "Python",
        "FastAPI",
        "PostgreSQL",
    ]


def test_career_recommendation_request_allows_insufficient_data():
    request = CareerRecommendationRequest()

    assert request.profile.current_role is None
    assert request.profile.career_goal is None
    assert request.profile.years_experience is None
    assert request.profile.education == []
    assert request.profile.interests == []
    assert request.skills == []


def test_career_profile_rejects_negative_experience():
    with pytest.raises(ValidationError):
        CareerProfile(
            years_experience=-1,
        )


def test_career_recommendation_validates_match_score():
    recommendation = CareerRecommendation(
        career_title="Backend Engineer",
        match_score=0.85,
        rationale=("Strong overlap with backend development skills."),
        matched_skills=[
            "Python",
            "FastAPI",
        ],
        missing_skills=[
            "Kubernetes",
        ],
    )

    assert recommendation.match_score == 0.85
    assert recommendation.matched_skills == [
        "Python",
        "FastAPI",
    ]
    assert recommendation.missing_skills == [
        "Kubernetes",
    ]


@pytest.mark.parametrize(
    "match_score",
    [
        -0.01,
        1.01,
    ],
)
def test_career_recommendation_rejects_invalid_match_score(
    match_score: float,
):
    with pytest.raises(ValidationError):
        CareerRecommendation(
            career_title="Backend Engineer",
            match_score=match_score,
            rationale="Test recommendation",
        )


def test_career_recommendation_supports_entry_level_result():
    recommendation = CareerRecommendation(
        career_title="Junior Backend Developer",
        match_score=0.7,
        rationale=(
            "Suitable entry-level path based on the candidate's current skills."
        ),
        matched_skills=[
            "Python",
        ],
        missing_skills=[
            "FastAPI",
            "PostgreSQL",
        ],
        entry_level=True,
    )

    assert recommendation.entry_level is True


def test_learning_roadmap_step_requires_positive_step_number():
    step = LearningRoadmapStep(
        step=1,
        title="Learn FastAPI",
        description=("Build REST APIs using FastAPI."),
        skills=[
            "FastAPI",
        ],
    )

    assert step.step == 1

    with pytest.raises(ValidationError):
        LearningRoadmapStep(
            step=0,
            title="Invalid step",
            description="Invalid step number",
        )


def test_career_recommendation_response_contains_skill_gaps_and_roadmap():
    response = CareerRecommendationResponse(
        status="ok",
        recommendations=[
            CareerRecommendation(
                career_title="Data Engineer",
                match_score=0.8,
                rationale=("Strong Python and database background."),
                matched_skills=[
                    "Python",
                    "PostgreSQL",
                ],
                missing_skills=[
                    "Apache Airflow",
                ],
            )
        ],
        roadmap=[
            LearningRoadmapStep(
                step=1,
                title="Learn workflow orchestration",
                description=("Build data pipelines with Apache Airflow."),
                skills=[
                    "Apache Airflow",
                ],
            )
        ],
    )

    assert response.recommendation_version == "1.0"
    assert response.status == "ok"

    assert response.recommendations[0].career_title == "Data Engineer"

    assert response.recommendations[0].missing_skills == [
        "Apache Airflow",
    ]

    assert response.roadmap[0].step == 1


def test_career_recommendation_response_supports_insufficient_data():
    response = CareerRecommendationResponse(
        status="needs_more_information",
        missing_information=[
            "skills",
            "career_goal",
        ],
    )

    assert response.status == "needs_more_information"

    assert response.recommendations == []
    assert response.roadmap == []

    assert response.missing_information == [
        "skills",
        "career_goal",
    ]


def test_career_recommendation_response_rejects_unknown_status():
    with pytest.raises(ValidationError):
        CareerRecommendationResponse(
            status="unknown",
        )
