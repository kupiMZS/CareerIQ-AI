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
        json={
            "resume_text": "John Doe\nSoftware Engineer\nLaravel Angular"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ats_score"] == 20
    assert data["extracted_name"] == "John Doe"
    assert data["extracted_email"] is None
    assert data["skills"] == ["laravel", "angular"]
    assert data["education"] == []
    assert data["experience"] == ["Software Engineer"]
    assert data["status"] == "completed"


def test_analyze_requires_resume_text():
    response = client.post(
        "/analyze",
        json={
            "resume_text": ""
        },
    )

    assert response.status_code == 422
