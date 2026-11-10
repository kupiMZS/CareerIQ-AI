import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.schemas.analysis import AnalyzeRequest
from app.schemas.ats import MAX_ATS_RESUME_CHARS

EXPECTED_CODES = [
    "contact_email",
    "section_skills",
    "section_education",
    "section_experience",
    "section_skills_content",
    "section_education_content",
    "section_experience_content",
    "quantified_outcome_evidence",
]


def _post(payload):
    with TestClient(main_module.app) as client:
        return client.post(
            "/analyze/ats",
            json=payload,
        )


def test_ats_endpoint_returns_eight_findings():
    resume = """
Taylor Example
taylor@example.com

Skills
Python

Education
BSc Computer Science

Experience
Reduced processing time by 35%.
"""

    response = _post({"resume_text": resume})

    assert response.status_code == 200

    payload = response.json()

    assert set(payload) == {
        "report_version",
        "score",
        "findings",
        "limitations",
    }

    assert payload["report_version"] == "ats-v1"
    assert payload["score"] is None
    assert "ats_score" not in payload

    assert [finding["code"] for finding in payload["findings"]] == EXPECTED_CODES

    assert all(finding["status"] == "satisfied" for finding in payload["findings"])

    assert payload["limitations"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"resume_text": ""},
        {"resume_text": "   \n   "},
        {"resume_text": None},
        {"resume_text": []},
    ],
)
def test_invalid_requests_return_422(payload):
    response = _post(payload)

    assert response.status_code == 422


def test_ats_endpoint_does_not_use_ai_provider(
    monkeypatch,
):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("ATS endpoint must not invoke the AI provider.")

    monkeypatch.setattr(
        main_module,
        "get_settings",
        forbidden,
    )

    monkeypatch.setattr(
        main_module,
        "create_orchestrator",
        forbidden,
    )

    response = _post(
        {"resume_text": ("Skills\nPython\nExperience\nReduced errors by 20%.")}
    )

    assert response.status_code == 200
    assert response.json()["score"] is None


def test_empty_sections_are_not_treated_as_content():
    response = _post({"resume_text": ("Skills\nEducation\nExperience\n")})

    assert response.status_code == 200

    findings = {item["code"]: item for item in response.json()["findings"]}

    for code in (
        "section_skills_content",
        "section_education_content",
        "section_experience_content",
    ):
        assert findings[code]["status"] == ("needs_attention")

    assert findings["quantified_outcome_evidence"]["status"] == "not_assessed"


def test_quantified_outcome_is_not_claimed_verified():
    response = _post({"resume_text": ("Experience\nReduced errors by 20%.")})

    assert response.status_code == 200

    finding = next(
        item
        for item in response.json()["findings"]
        if item["code"] == "quantified_outcome_evidence"
    )

    assert finding["status"] == "satisfied"

    assert "not independently verified" in (finding["explanation"])

    assert finding["supporting_text"] == ["Reduced errors by 20%."]


def test_repeated_requests_are_deterministic():
    payload = {
        "resume_text": ("person@example.com\nSkills\nPython\nExperience\nSaved $3,000.")
    }

    first = _post(payload)
    second = _post(payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_existing_analysis_routes_remain_registered():
    routes = {
        (route.path, method)
        for route in main_module.app.routes
        for method in getattr(route, "methods", ())
    }

    assert ("/analyze", "POST") in routes
    assert ("/analyze/evidence", "POST") in routes
    assert ("/analyze/ats", "POST") in routes


def test_openapi_documents_separate_ats_response():
    schema = main_module.app.openapi()

    assert "/analyze" in schema["paths"]
    assert "/analyze/evidence" in schema["paths"]
    assert "/analyze/ats" in schema["paths"]

    operation = schema["paths"]["/analyze/ats"]["post"]

    response_schema = operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]

    assert "ATSReport" in str(response_schema)


def test_ats_endpoint_accepts_maximum_resume_length():
    prefix = "Experience\n"

    text = prefix + ("X" * (MAX_ATS_RESUME_CHARS - len(prefix)))

    assert len(text) == MAX_ATS_RESUME_CHARS

    response = _post({"resume_text": text})

    assert response.status_code == 200
    assert response.json()["report_version"] == "ats-v1"
    assert response.json()["score"] is None
    assert len(response.json()["findings"]) == 8


def test_ats_endpoint_rejects_over_limit():
    oversized_text = "X" * (MAX_ATS_RESUME_CHARS + 1)

    response = _post({"resume_text": oversized_text})

    assert response.status_code == 422

    detail = response.json()["detail"]

    assert any("resume_text" in item.get("loc", []) for item in detail)


def test_ats_endpoint_rejects_unexpected_fields():
    response = _post(
        {
            "resume_text": "Skills\nPython",
            "unsupported_control": "example",
        }
    )

    assert response.status_code == 422


def test_legacy_request_schema_remains_unbounded():
    text = "X" * (MAX_ATS_RESUME_CHARS + 1)

    request = AnalyzeRequest(resume_text=text)

    assert request.resume_text == text
