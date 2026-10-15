from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
import app.services.resume_evidence_audit as audit_module
import app.services.resume_evidence_coverage as coverage_module
from app import services
from app.schemas.analysis import AnalyzeResponse
from app.schemas.resume import ResumeIntelligence, Skill
from app.services import (
    build_analysis_response,
    enrich_resume_intelligence,
)

PUBLIC_FIELDS = {
    "ats_score",
    "extracted_name",
    "extracted_email",
    "skills",
    "education",
    "experience",
    "summary",
    "status",
}


def _unexpected_evidence_call(*args, **kwargs):
    raise AssertionError(
        "The public /analyze endpoint must not invoke internal evidence auditing."
    )


@pytest.mark.parametrize(
    "resume",
    [
        ("Jane Doe\njane@example.com\nSkills: Python\nNever used Docker"),
        (
            "Jane Doe\n"
            "jane@example.com\n"
            "Career goal: Learn Python\n"
            "Job requirements: Docker"
        ),
    ],
)
def test_analyze_does_not_automatically_audit_evidence(
    monkeypatch,
    resume,
):
    intelligence = ResumeIntelligence(
        skills=[
            Skill(
                name="Python",
                confidence=0.7,
                evidence=["Provider Python"],
            ),
            Skill(
                name="Docker",
                confidence=0.5,
                evidence=["Provider Docker"],
            ),
        ]
    )

    original = intelligence.model_dump()

    enriched = enrich_resume_intelligence(
        resume,
        intelligence,
    )

    expected_response = build_analysis_response(
        resume,
        enriched,
    ).model_dump(mode="json")

    settings = object()

    analyze_mock = AsyncMock(return_value=intelligence)

    orchestrator = SimpleNamespace(analyze_resume=analyze_mock)

    def fake_factory(received_settings):
        assert received_settings is settings
        return orchestrator

    monkeypatch.setattr(
        main_module,
        "get_settings",
        lambda: settings,
    )

    monkeypatch.setattr(
        main_module,
        "create_orchestrator",
        fake_factory,
    )

    monkeypatch.setattr(
        services,
        "summarize_resume_skill_evidence",
        _unexpected_evidence_call,
    )

    monkeypatch.setattr(
        coverage_module,
        "summarize_resume_skill_evidence",
        _unexpected_evidence_call,
    )

    monkeypatch.setattr(
        coverage_module,
        "collect_and_audit_resume_skill_evidence",
        _unexpected_evidence_call,
    )

    monkeypatch.setattr(
        audit_module,
        "collect_and_audit_resume_skill_evidence",
        _unexpected_evidence_call,
    )

    monkeypatch.setattr(
        main_module,
        "summarize_resume_skill_evidence",
        _unexpected_evidence_call,
        raising=False,
    )

    monkeypatch.setattr(
        main_module,
        "collect_and_audit_resume_skill_evidence",
        _unexpected_evidence_call,
        raising=False,
    )

    with TestClient(main_module.app) as client:
        response = client.post(
            "/analyze",
            json={"resume_text": resume},
        )

    assert response.status_code == 200
    assert response.json() == expected_response

    assert set(response.json()) == PUBLIC_FIELDS
    assert set(AnalyzeResponse.model_fields) == PUBLIC_FIELDS

    analyze_mock.assert_awaited_once_with(resume)

    assert intelligence.model_dump() == original
    assert intelligence.analysis_version == "1.0"


def test_invalid_resume_does_not_start_analysis(
    monkeypatch,
):
    def unexpected_call(*args, **kwargs):
        raise AssertionError(
            "Invalid requests must be rejected before starting analysis."
        )

    monkeypatch.setattr(
        main_module,
        "get_settings",
        unexpected_call,
    )

    monkeypatch.setattr(
        main_module,
        "create_orchestrator",
        unexpected_call,
    )

    with TestClient(main_module.app) as client:
        response = client.post(
            "/analyze",
            json={"resume_text": ""},
        )

    assert response.status_code == 422


def test_evidence_reporter_remains_explicitly_callable():
    resume = "Skills: Python\nNever used Docker"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python", confidence=0.7),
            Skill(name="Docker", confidence=0.5),
        ]
    )

    original = intelligence.model_dump()

    reports = services.summarize_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert [report.status for report in reports] == [
        "literal_mention_only",
        "explicit_rejection_only",
    ]

    assert [report.review_flags for report in reports] == [
        (),
        (),
    ]

    assert all(
        record.source == "deterministic" and record.confidence is None
        for report in reports
        for record, _ in report.audited_records
    )

    assert intelligence.model_dump() == original
