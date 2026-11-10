import pytest

from app.schemas.resume import ResumeIntelligence, Skill
from app.services.analysis_response_adapter import (
    build_analysis_response,
)
from app.services.resume_evidence_audit import (
    collect_and_audit_resume_skill_evidence,
)
from app.services.resume_intelligence_enricher import (
    enrich_resume_intelligence,
)


@pytest.mark.parametrize(
    ("resume", "skill_name", "expected"),
    [
        (
            "Skills: Python",
            "Python",
            [("Skills: Python", "lexically_supported")],
        ),
        (
            "Never used Docker",
            "Docker",
            [("Never used Docker", "explicitly_unsupported")],
        ),
        (
            "Currently learning AWS",
            "AWS",
            [("Currently learning AWS", "explicitly_unsupported")],
        ),
        (
            "Skills: JavaScript",
            "Java",
            [],
        ),
        (
            "Skills: python",
            "Python",
            [],
        ),
        (
            "Experience with Azure",
            "AWS",
            [],
        ),
        (
            "",
            "Python",
            [],
        ),
    ],
)
def test_workflow_collects_and_verifies_literal_evidence(
    resume,
    skill_name,
    expected,
):
    intelligence = ResumeIntelligence(skills=[Skill(name=skill_name)])

    audited = collect_and_audit_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert [
        (record.evidence_text, result.status) for record, result in audited
    ] == expected

    for record, _ in audited:
        assert record.field_path == "skills[0].name"
        assert record.extracted_value == skill_name
        assert record.evidence_text in resume
        assert record.source == "deterministic"
        assert record.confidence is None


def test_workflow_retains_contradictory_skill_evidence():
    resume = "No experience with Python\nBuilt production services using Python"

    intelligence = ResumeIntelligence(skills=[Skill(name="Python")])

    audited = collect_and_audit_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert [result.status for _, result in audited] == [
        "explicitly_unsupported",
        "lexically_supported",
    ]

    assert [record.evidence_text for record, _ in audited] == (resume.splitlines())


def test_workflow_preserves_resume_order_and_skill_indices():
    resume = "Skills: Python, Docker\nNever used Docker\nBuilt with Python"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python"),
            Skill(name="Docker"),
        ]
    )

    audited = collect_and_audit_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert [(record.field_path, result.status) for record, result in audited] == [
        ("skills[0].name", "lexically_supported"),
        ("skills[1].name", "lexically_supported"),
        ("skills[1].name", "explicitly_unsupported"),
        ("skills[0].name", "lexically_supported"),
    ]


def test_workflow_preserves_intelligence_and_public_response():
    resume = "Jane Doe\njane@example.com\nSkills\nPython\nNever used Docker"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(
                name="Python",
                confidence=0.7,
                evidence=["Provider supplied Python"],
            ),
            Skill(
                name="Docker",
                confidence=0.5,
                evidence=["Provider supplied Docker"],
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

    audited = collect_and_audit_resume_skill_evidence(
        resume,
        enriched,
    )

    assert [result.status for _, result in audited] == [
        "lexically_supported",
        "explicitly_unsupported",
    ]

    assert all(
        record.source == "deterministic" and record.confidence is None
        for record, _ in audited
    )

    assert intelligence.model_dump() == original
    assert enriched.model_dump() == before_enriched

    after_response = build_analysis_response(
        resume,
        enriched,
    ).model_dump()

    assert after_response == before_response
