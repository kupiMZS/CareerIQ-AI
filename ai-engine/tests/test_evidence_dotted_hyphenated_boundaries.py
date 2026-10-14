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
        ("Skills: Node.js", "Node", "no_literal_evidence", ()),
        ("Skills: Node.js", "Node.js", "literal_mention_only", ()),
        ("Skills: Node.js.", "Node.js", "literal_mention_only", ()),
        ("Skills: Node.js.v2", "Node.js", "no_literal_evidence", ()),
        ("Skills: Node.", "Node", "literal_mention_only", ()),
        ("Skills: scikit-learn", "scikit", "no_literal_evidence", ()),
        ("Skills: scikit-learn", "learn", "no_literal_evidence", ()),
        (
            "Skills: scikit-learn",
            "scikit-learn",
            "literal_mention_only",
            (),
        ),
        ("Skills: Python-based", "Python", "no_literal_evidence", ()),
        ("Skills: Python.", "Python", "literal_mention_only", ()),
        ("- Python", "Python", "literal_mention_only", ()),
        ("Skills: C++.", "C++", "literal_mention_only", ()),
        ("Skills: C#.", "C#", "literal_mention_only", ()),
        (
            "Career goal: Learn Node.js",
            "Node",
            "no_literal_evidence",
            (),
        ),
        (
            "Career goal: Learn Node.js",
            "Node.js",
            "literal_mention_only",
            ("aspirational_wording",),
        ),
        (
            "Job requirements: Node.js",
            "Node.js",
            "literal_mention_only",
            ("requirement_wording",),
        ),
        (
            "Job requirements: Node.js",
            "Node",
            "no_literal_evidence",
            (),
        ),
        (
            "Never used Node.js",
            "Node.js",
            "explicit_rejection_only",
            (),
        ),
        (
            "Never used Node.js.v2",
            "Node.js",
            "no_literal_evidence",
            (),
        ),
        (
            "No experience with Node.js, but expert in Node.js",
            "Node.js",
            "explicit_rejection_only",
            ("rejection_with_contrast",),
        ),
        (
            "No experience with Node.js.v2; Skills: Node.js",
            "Node.js",
            "literal_mention_only",
            (),
        ),
        (
            "Skills: Python, scikit-learn",
            "learn",
            "no_literal_evidence",
            (),
        ),
        (
            "Worked with Node.js/TypeScript",
            "Node.js",
            "literal_mention_only",
            (),
        ),
        (
            "Used scikit-learn.",
            "scikit-learn",
            "literal_mention_only",
            (),
        ),
        (
            "Skills: Node.js-based",
            "Node.js",
            "no_literal_evidence",
            (),
        ),
    ],
)
def test_dotted_and_hyphenated_skill_boundaries(
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
        ("Never used Node.js", "Node", False, False),
        ("Never used Node.js", "Node.js", True, True),
        ("Never used Node.js.v2", "Node.js", False, False),
        ("Never used scikit-learn", "scikit", False, False),
        ("Never used scikit-learn", "scikit-learn", True, True),
        ("No experience with Python-based", "Python", False, False),
        ("Never used Python.", "Python", True, True),
    ],
)
def test_manual_verifier_respects_technical_names(
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


def test_boundary_hardening_preserves_public_response():
    resume = (
        "Jane Doe\n"
        "jane@example.com\n"
        "Skills: Node.js.\n"
        "Career goal: Learn scikit-learn\n"
        "Never used Python-based\n"
        "Never used Docker"
    )

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Node.js", confidence=0.7),
            Skill(name="scikit-learn", confidence=0.5),
            Skill(name="Python", confidence=0.6),
            Skill(name="Docker", confidence=0.4),
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
        "no_literal_evidence",
        "explicit_rejection_only",
    ]

    assert [report.review_flags for report in reports] == [
        (),
        ("aspirational_wording",),
        (),
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
