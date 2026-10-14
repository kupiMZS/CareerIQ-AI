import pytest

from app.schemas.evidence import EvidenceRecord
from app.services.evidence_verifier import verify_evidence_excerpt


def _record(evidence_text: str) -> EvidenceRecord:
    return EvidenceRecord(
        field_path="skills[0].name",
        extracted_value="Python",
        evidence_text=evidence_text,
        source="deterministic",
    )


@pytest.mark.parametrize(
    ("resume_text", "evidence_text", "expected"),
    [
        ("Skills: Python, Docker", "Skills: Python", True),
        ("- Distributed systems", "- Distributed systems", True),
        ("Experience with AWS", "Experience with Azure", False),
        ("Python Developer", "python developer", False),
        ("Machine learning", "Machine   learning", False),
        ("Python", "Python", True),
        ("Python", "Python Developer", False),
        ("", "Python", False),
    ],
)
def test_verify_evidence_excerpt_literal_matching(
    resume_text,
    evidence_text,
    expected,
):
    record = _record(evidence_text)

    assert verify_evidence_excerpt(resume_text, record) is expected


def test_verify_evidence_excerpt_preserves_record():
    record = EvidenceRecord(
        field_path="skills[0].name",
        extracted_value="Python",
        evidence_text="Skills: Python",
        source="provider_verified",
        confidence=0.8,
    )
    original = record.model_dump()

    assert verify_evidence_excerpt("Skills: Python", record) is True
    assert record.model_dump() == original


def test_verify_evidence_excerpt_does_not_assume_semantic_support():
    record = EvidenceRecord(
        field_path="skills[0].name",
        extracted_value="AWS",
        evidence_text="Experience with Azure",
        source="deterministic",
    )

    assert verify_evidence_excerpt("Experience with Azure", record) is True
