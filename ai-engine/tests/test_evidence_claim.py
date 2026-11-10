import pytest

from app.schemas.evidence import EvidenceRecord
from app.services.evidence_verifier import verify_evidence_claim


@pytest.mark.parametrize(
    ("resume_text", "value", "excerpt", "expected"),
    [
        ("Skills: Python, Docker", "Python", "Skills: Python", True),
        ("Experience with Azure", "AWS", "Experience with Azure", False),
        ("Skills: JavaScript", "Java", "Skills: JavaScript", False),
        ("Experience with Python", "Python", "Experience with Python", True),
        ("Skills: docker", "Docker", "Skills: docker", False),
        (
            "- Platform engineering",
            "Platform engineering",
            "- Platform engineering",
            True,
        ),
        ("Skills: Python", "Python", "Skills: Python, Docker", False),
        ("No experience with Python", "Python", "No experience with Python", True),
    ],
)
def test_verify_evidence_claim(
    resume_text,
    value,
    excerpt,
    expected,
):
    record = EvidenceRecord(
        field_path="skills[0].name",
        extracted_value=value,
        evidence_text=excerpt,
        source="deterministic",
    )

    assert verify_evidence_claim(resume_text, record) is expected


def test_verify_evidence_claim_does_not_mutate_record():
    record = EvidenceRecord(
        field_path="skills[0].name",
        extracted_value="Python",
        evidence_text="Skills: Python",
        source="provider_verified",
        confidence=0.8,
    )
    original = record.model_dump()

    assert verify_evidence_claim("Skills: Python", record) is True
    assert record.model_dump() == original
