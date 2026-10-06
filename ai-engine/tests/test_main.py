from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "service": "careeriq-ai-engine",
    }


def test_analyze_resume():
    response = client.post(
        "/analyze",
        json={"resume_text": ("John Doe\nSoftware Engineer\nLaravel Angular")},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ats_score"] == 20
    assert data["extracted_name"] == "John Doe"
    assert data["extracted_email"] is None
    assert data["skills"] == [
        "laravel",
        "angular",
    ]
    assert data["education"] == []
    assert data["experience"] == ["Software Engineer"]
    assert data["status"] == "completed"


def test_analyze_requires_resume_text():
    response = client.post(
        "/analyze",
        json={
            "resume_text": "",
        },
    )

    assert response.status_code == 422


def test_career_recommendation_endpoint():
    response = client.post(
        "/career/recommend",
        json={
            "profile": {
                "current_role": ("Backend Developer"),
                "career_goal": ("Backend Engineer"),
                "years_experience": 2,
            },
            "skills": [
                "Python",
                "FastAPI",
                "PostgreSQL",
                "Docker",
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["recommendation_version"] == "1.0"

    assert data["recommendations"]

    recommendation = data["recommendations"][0]

    assert recommendation["career_title"] == "Backend Engineer"

    assert recommendation["match_score"] == 1.0

    assert recommendation["matched_skills"] == [
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
    ]

    assert recommendation["missing_skills"] == []

    assert data["roadmap"]


def test_career_recommendation_endpoint_handles_insufficient_data():
    response = client.post(
        "/career/recommend",
        json={},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "needs_more_information"

    assert data["recommendations"] == []
    assert data["roadmap"] == []

    assert data["missing_information"] == [
        "skills",
        "career_goal",
    ]


def test_career_recommendation_endpoint_validates_profile():
    response = client.post(
        "/career/recommend",
        json={
            "profile": {
                "years_experience": -1,
            },
            "skills": [
                "Python",
            ],
        },
    )

    assert response.status_code == 422
