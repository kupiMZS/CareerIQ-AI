from types import SimpleNamespace
from unittest.mock import AsyncMock

from app import main as main_module
from app.schemas.resume import ResumeIntelligence, Skill
from fastapi.testclient import TestClient


def test_opt_in_evidence_endpoint_reports_skill_statuses(
    monkeypatch,
):
    resume = "Skills\nPython\nNever used Docker\nPlan to learn AWS"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python", confidence=0.7),
            Skill(name="Docker", confidence=0.5),
            Skill(name="AWS"),
        ]
    )

    original = intelligence.model_dump()
    settings = object()

    analyze_mock = AsyncMock(return_value=intelligence)

    orchestrator = SimpleNamespace(analyze_resume=analyze_mock)

    monkeypatch.setattr(
        main_module,
        "get_settings",
        lambda: settings,
    )

    def fake_factory(received_settings):
        assert received_settings is settings
        return orchestrator

    monkeypatch.setattr(
        main_module,
        "create_orchestrator",
        fake_factory,
    )

    with TestClient(main_module.app) as client:
        response = client.post(
            "/analyze/evidence",
            json={"resume_text": resume},
        )

    assert response.status_code == 200

    payload = response.json()

    assert set(payload) == {
        "analysis",
        "skill_evidence",
    }

    assert set(payload["analysis"]) == {
        "ats_score",
        "extracted_name",
        "extracted_email",
        "skills",
        "education",
        "experience",
        "summary",
        "status",
    }

    reports = payload["skill_evidence"]

    assert len(reports) == 3

    by_skill = {item["skill_name"]: item for item in reports}

    assert set(by_skill) == {
        "Python",
        "Docker",
        "AWS",
    }

    assert by_skill["Python"]["status"] == ("literal_mention_only")

    assert by_skill["Docker"]["status"] == ("explicit_rejection_only")

    assert by_skill["AWS"]["status"] == ("literal_mention_only")

    assert "aspirational_wording" in (by_skill["AWS"]["review_flags"])

    assert all("field_path" in item and "review_flags" in item for item in reports)

    analyze_mock.assert_awaited_once_with(resume)

    assert intelligence.model_dump() == original
