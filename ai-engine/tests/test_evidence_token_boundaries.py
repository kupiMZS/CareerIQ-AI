import pytest

from app.schemas.evidence import EvidenceRecord
from app.schemas.resume import ResumeIntelligence, Skill
from app.services import (
    build_analysis_response,
    enrich_resume_intelligence,
    summarize_resume_skill_evidence,
)
from app.services.evidence_verifier import (
    is_explicitly_unsupported_skill_claim,
    verify_evidence_claim,
    verify_evidence_record,
)


@pytest.mark.parametrize(
    ("resume", "skill", "status", "flags"),
    [
        ("Skills: C++", "C++", "literal_mention_only", ()),
        ("Skills: C#", "C#", "literal_mention_only", ()),
        ("Skills: C++", "C", "no_literal_evidence", ()),
        ("Skills: C#", "C", "no_literal_evidence", ()),
        ("Skills: C+++", "C++", "no_literal_evidence", ()),
        ("Skills: C##", "C#", "no_literal_evidence", ()),
        ("Skills: C++17", "C++", "no_literal_evidence", ()),
        ("Used C++/CLI", "C++", "literal_mention_only", ()),
        (
            "Career goal: Learn C++",
            "C++",
            "literal_mention_only",
            ("aspirational_wording",),
        ),
        (
            "Career goal: Learn C+++",
            "C++",
            "no_literal_evidence",
            (),
        ),
        (
            "Job requirements: C#",
            "C#",
            "literal_mention_only",
            ("requirement_wording",),
        ),
        (
            "Job requirements: C##",
            "C#",
            "no_literal_evidence",
            (),
        ),
        ("Never used C++", "C++", "explicit_rejection_only", ()),
        ("Never used C+++", "C++", "no_literal_evidence", ()),
        (
            "No experience with C#",
            "C#",
            "explicit_rejection_only",
            (),
        ),
        (
            "No experience with C#",
            "C",
            "no_literal_evidence",
            (),
        ),
        (
            "No experience with C++, but proficient in C++",
            "C++",
            "explicit_rejection_only",
            ("rejection_with_contrast",),
        ),
        (
            "No experience with C+++, but proficient in C++",
            "C++",
            "literal_mention_only",
            (),
        ),
        (
            "Career goal: Learn C+++; Skills: C++",
            "C++",
            "literal_mention_only",
            (),
        ),
        (
            "Job requirements: C##; Skills: C#",
            "C#",
            "literal_mention_only",
            (),
        ),
    ],
)
def test_special_character_skill_boundaries(
    resume,
    skill,
    status,
    flags,
):
    intelligence = ResumeIntelligence(skills=[Skill(name=skill)])

    report = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )[0]

    assert report.status == status
    assert report.review_flags == flags

    for record, result in report.audited_records:
        assert record.extracted_value == skill
        assert record.evidence_text in resume
        assert record.confidence is None
        assert result.claim_found is True


@pytest.mark.parametrize(
    ("excerpt", "skill", "claim_found", "rejected"),
    [
        ("Never used C+++", "C++", False, False),
        ("Never used C++", "C++", True, True),
        ("Never used C#", "C#", True, True),
        ("Never used C##", "C#", False, False),
        ("No experience with C++", "C", False, False),
    ],
)
def test_manual_evidence_verification_uses_same_boundaries(
    excerpt,
    skill,
    claim_found,
    rejected,
):
    record = EvidenceRecord(
        field_path="skills[0].name",
        extracted_value=skill,
        evidence_text=excerpt,
        source="deterministic",
    )

    assert verify_evidence_claim(excerpt, record) is claim_found

    assert is_explicitly_unsupported_skill_claim(record) is rejected

    result = verify_evidence_record(excerpt, record)

    assert result.claim_found is claim_found

    if rejected:
        assert result.status == "explicitly_unsupported"
    elif not claim_found:
        assert result.status == "claim_not_found"


def test_boundary_reporting_preserves_existing_public_response():
    resume = (
        "Jane Doe\n"
        "jane@example.com\n"
        "Skills: C++\n"
        "Career goal: Learn C#\n"
        "Never used C+++\n"
        "Never used Docker"
    )

    intelligence = ResumeIntelligence(
        skills=[
            Skill(
                name="C++",
                confidence=0.7,
                evidence=["Provider C++"],
            ),
            Skill(
                name="C#",
                confidence=0.5,
                evidence=["Provider C#"],
            ),
            Skill(
                name="Docker",
                confidence=0.4,
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
        "literal_mention_only",
        "explicit_rejection_only",
    ]

    assert [report.review_flags for report in reports] == [
        (),
        ("aspirational_wording",),
        (),
    ]

    assert intelligence.model_dump() == original
    assert enriched.model_dump() == before_enriched

    after_response = build_analysis_response(
        resume,
        enriched,
    ).model_dump()

    assert after_response == before_response
    assert enriched.analysis_version == "1.0"
