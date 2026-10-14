from fastapi.routing import APIRoute

from app import services
from app.main import app
from app.schemas.analysis import AnalyzeResponse
from app.schemas.resume import ResumeIntelligence, Skill
from app.services import (
    build_analysis_response,
    enrich_resume_intelligence,
    summarize_resume_skill_evidence,
)
from app.services.resume_evidence_coverage import (
    summarize_resume_skill_evidence as original_reporter,
)

PUBLIC_ANALYZE_FIELDS = {
    "ats_score",
    "extracted_name",
    "extracted_email",
    "skills",
    "education",
    "experience",
    "summary",
    "status",
}


def test_coverage_reporter_is_exported_from_service_layer():
    assert summarize_resume_skill_evidence is original_reporter
    assert services.summarize_resume_skill_evidence is original_reporter
    assert "summarize_resume_skill_evidence" in services.__all__


def test_service_reports_all_skills_without_scoring():
    resume = "Skills\nPython\nNever used Docker"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python", confidence=0.7),
            Skill(name="Docker", confidence=0.5),
            Skill(name="AWS", confidence=None),
        ]
    )

    original = intelligence.model_dump()

    reports = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert [report.field_path for report in reports] == [
        "skills[0].name",
        "skills[1].name",
        "skills[2].name",
    ]

    assert [report.status for report in reports] == [
        "literal_mention_only",
        "explicit_rejection_only",
        "no_literal_evidence",
    ]

    assert reports[2].audited_records == ()

    assert all(
        record.source == "deterministic"
        and record.confidence is None
        and record.evidence_text in resume
        for report in reports
        for record, _ in report.audited_records
    )

    assert intelligence.model_dump() == original


def test_service_preserves_response_after_enrichment():
    resume = "Jane Doe\njane@example.com\nSkills\nPython\nNever used Docker"

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

    before_enriched = enriched.model_dump()

    before_response = build_analysis_response(
        resume,
        enriched,
    ).model_dump()

    reports = summarize_resume_skill_evidence(
        resume,
        enriched,
    )

    assert [report.status for report in reports] == [
        "literal_mention_only",
        "explicit_rejection_only",
    ]

    after_response = build_analysis_response(
        resume,
        enriched,
    ).model_dump()

    assert after_response == before_response
    assert enriched.model_dump() == before_enriched
    assert intelligence.model_dump() == original


def test_public_analyze_response_contract_is_unchanged():
    assert set(AnalyzeResponse.model_fields) == (PUBLIC_ANALYZE_FIELDS)

    routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/analyze"
        and "POST" in route.methods
    ]

    assert len(routes) == 1
    assert routes[0].response_model is AnalyzeResponse

    schema = app.openapi()

    response_schema = schema["components"]["schemas"]["AnalyzeResponse"]

    assert set(response_schema["properties"]) == (PUBLIC_ANALYZE_FIELDS)

    assert "SkillEvidenceCoverage" not in schema["components"]["schemas"]

    assert ResumeIntelligence().analysis_version == "1.0"


def test_unmatched_provider_evidence_is_not_promoted():
    intelligence = ResumeIntelligence(
        skills=[
            Skill(
                name="AWS",
                evidence=["AWS"],
                confidence=0.8,
            )
        ]
    )

    original = intelligence.model_dump()

    reports = summarize_resume_skill_evidence(
        "Experience with Azure",
        intelligence,
    )

    assert len(reports) == 1
    assert reports[0].status == "no_literal_evidence"
    assert reports[0].audited_records == ()
    assert intelligence.model_dump() == original
