import pytest

from app.schemas.evidence import EvidenceRecord
from app.schemas.resume import ResumeIntelligence, Skill
from app.services.analysis_response_adapter import (
    build_analysis_response,
)
from app.services.resume_evidence_audit import (
    audit_resume_skill_evidence,
)
from app.services.resume_intelligence_enricher import (
    enrich_resume_intelligence,
)


def _record(
    name: str,
    excerpt: str,
    field_path: str = "skills[0].name",
) -> EvidenceRecord:
    return EvidenceRecord(
        field_path=field_path,
        extracted_value=name,
        evidence_text=excerpt,
        source="deterministic",
    )


@pytest.mark.parametrize(
    ("resume", "name", "excerpt", "expected"),
    [
        (
            "Skills: Python",
            "Python",
            "Skills: Python",
            "lexically_supported",
        ),
        (
            "No experience with Docker",
            "Docker",
            "No experience with Docker",
            "explicitly_unsupported",
        ),
        (
            "Currently learning AWS",
            "AWS",
            "Currently learning AWS",
            "explicitly_unsupported",
        ),
        (
            "Skills: JavaScript",
            "Java",
            "Skills: JavaScript",
            "claim_not_found",
        ),
        (
            "Skills: Python",
            "Python",
            "Skills: Python, Docker",
            "excerpt_not_found",
        ),
        (
            "Experience with Azure",
            "AWS",
            "Experience with Azure",
            "claim_not_found",
        ),
        (
            "Skills: Python, Docker",
            "Docker",
            "Skills: Python, Docker",
            "lexically_supported",
        ),
    ],
)
def test_audit_returns_existing_verification_status(
    resume,
    name,
    excerpt,
    expected,
):
    intelligence = ResumeIntelligence(skills=[Skill(name=name)])
    record = _record(name, excerpt)

    result = audit_resume_skill_evidence(
        resume,
        intelligence,
        [record],
    )

    assert len(result) == 1
    assert result[0][0] is record
    assert result[0][1].status == expected


def test_audit_accepts_empty_records():
    intelligence = ResumeIntelligence(skills=[Skill(name="Python")])

    assert (
        audit_resume_skill_evidence(
            "Python",
            intelligence,
            [],
        )
        == []
    )


def test_audit_preserves_record_order():
    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python"),
            Skill(name="Docker"),
        ]
    )

    first = _record("Python", "Skills: Python")
    second = _record(
        "Docker",
        "Never used Docker",
        "skills[1].name",
    )

    results = audit_resume_skill_evidence(
        "Skills: Python\nNever used Docker",
        intelligence,
        [first, second],
    )

    assert [item[0] for item in results] == [
        first,
        second,
    ]
    assert [item[1].status for item in results] == [
        "lexically_supported",
        "explicitly_unsupported",
    ]


@pytest.mark.parametrize(
    ("field_path", "value", "message"),
    [
        ("skills[-1].name", "Python", "field_path"),
        ("skills[0].category", "Python", "field_path"),
        (
            "career_profile.career_goals[0]",
            "Python",
            "field_path",
        ),
        ("skills[1].name", "Python", "index"),
        ("skills[0].name", "Docker", "extracted_value"),
    ],
)
def test_audit_rejects_invalid_skill_reference(
    field_path,
    value,
    message,
):
    intelligence = ResumeIntelligence(skills=[Skill(name="Python")])

    record = _record(
        value,
        "Python",
        field_path,
    )

    with pytest.raises(ValueError, match=message):
        audit_resume_skill_evidence(
            "Python",
            intelligence,
            [record],
        )


def test_audit_preserves_inputs_and_provenance():
    intelligence = ResumeIntelligence(
        skills=[
            Skill(
                name="Docker",
                confidence=0.7,
                evidence=["Never used Docker"],
            )
        ]
    )

    record = EvidenceRecord(
        field_path="skills[0].name",
        extracted_value="Docker",
        evidence_text="Never used Docker",
        source="provider_verified",
        confidence=0.4,
    )

    before_intelligence = intelligence.model_dump()
    before_record = record.model_dump()

    results = audit_resume_skill_evidence(
        "Never used Docker",
        intelligence,
        [record],
    )

    assert results[0][1].status == "explicitly_unsupported"
    assert intelligence.model_dump() == before_intelligence
    assert record.model_dump() == before_record


def test_audit_after_enrichment_preserves_public_response():
    resume = "Jane Doe\njane@example.com\nSkills\nPython\nDocker"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(
                name="Python",
                evidence=["Python"],
            )
        ]
    )

    enriched = enrich_resume_intelligence(
        resume,
        intelligence,
    )

    before_intelligence = enriched.model_dump()
    before_response = build_analysis_response(
        resume,
        enriched,
    ).model_dump()

    results = audit_resume_skill_evidence(
        resume,
        enriched,
        [_record("Python", "Python")],
    )

    assert results[0][1].status == "lexically_supported"
    assert enriched.model_dump() == before_intelligence

    after_response = build_analysis_response(
        resume,
        enriched,
    ).model_dump()

    assert after_response == before_response
