import pytest
from pydantic import ValidationError

from app.schemas.evidence import (
    EvidenceRecord,
    EvidenceVerificationResult,
)
from app.services.evidence_verifier import verify_evidence_record


def _record(
    value: str,
    excerpt: str,
    field_path: str = "skills[0].name",
) -> EvidenceRecord:
    return EvidenceRecord(
        field_path=field_path,
        extracted_value=value,
        evidence_text=excerpt,
        source="deterministic",
    )


@pytest.mark.parametrize(
    ("resume_text", "value", "excerpt", "status"),
    [
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
            "No experience with Python",
            "Python",
            "No experience with Python",
            "explicitly_unsupported",
        ),
        (
            "Currently learning AWS",
            "AWS",
            "Currently learning AWS",
            "explicitly_unsupported",
        ),
        (
            "Skills: Python",
            "Python",
            "Skills: Python",
            "lexically_supported",
        ),
        (
            "Skills: JavaScript",
            "Java",
            "Skills: JavaScript",
            "claim_not_found",
        ),
        (
            "No experience with Java, but proficient in Python",
            "Python",
            "No experience with Java, but proficient in Python",
            "lexically_supported",
        ),
    ],
)
def test_combined_evidence_verification(
    resume_text,
    value,
    excerpt,
    status,
):
    result = verify_evidence_record(
        resume_text,
        _record(value, excerpt),
    )

    assert result.status == status
    assert result.excerpt_found is (status != "excerpt_not_found")
    assert result.claim_found is (
        status
        not in (
            "excerpt_not_found",
            "claim_not_found",
        )
    )
    assert result.explicitly_unsupported is (status == "explicitly_unsupported")


def test_combined_verifier_preserves_non_skill_scope():
    record = _record(
        "Python",
        "Currently learning Python",
        "career_profile.career_goals[0]",
    )

    result = verify_evidence_record(
        "Currently learning Python",
        record,
    )

    assert result.status == "lexically_supported"


def test_combined_verifier_does_not_mutate_record():
    record = EvidenceRecord(
        field_path="skills[0].name",
        extracted_value="Docker",
        evidence_text="Never used Docker",
        source="provider_verified",
        confidence=0.4,
    )

    original = record.model_dump()

    result = verify_evidence_record("Never used Docker", record)

    assert result.status == "explicitly_unsupported"
    assert record.model_dump() == original
    assert record.confidence == 0.4


def test_verification_result_rejects_unknown_status():
    with pytest.raises(ValidationError):
        EvidenceVerificationResult(
            status="verified",
            excerpt_found=True,
            claim_found=True,
        )
