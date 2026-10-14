import pytest

from app.schemas.evidence import EvidenceRecord
from app.services.evidence_verifier import (
    is_explicitly_unsupported_skill_claim,
)


@pytest.mark.parametrize(
    ("excerpt", "value", "expected"),
    [
        ("No experience with Python", "Python", True),
        ("Never used Docker", "Docker", True),
        ("Not familiar with Kubernetes", "Kubernetes", True),
        ("Currently learning AWS", "AWS", True),
        ("Learning AWS", "AWS", True),
        ("Experienced in Python", "Python", False),
        (
            "No experience with Java, but proficient in Python",
            "Python",
            False,
        ),
        (
            "Never used Docker, experienced with Python",
            "Python",
            False,
        ),
        ("No experience with JavaScript", "Java", False),
        ("No experience with Python", "Docker", False),
    ],
)
def test_explicit_skill_rejection(excerpt, value, expected):
    record = EvidenceRecord(
        field_path="skills[0].name",
        extracted_value=value,
        evidence_text=excerpt,
        source="deterministic",
    )

    assert is_explicitly_unsupported_skill_claim(record) is expected


def test_rejection_guard_does_not_apply_to_career_goals():
    record = EvidenceRecord(
        field_path="career_profile.career_goals[0]",
        extracted_value="Python",
        evidence_text="Currently learning Python",
        source="deterministic",
    )

    assert is_explicitly_unsupported_skill_claim(record) is False


def test_rejection_guard_preserves_evidence_record():
    record = EvidenceRecord(
        field_path="skills[0].name",
        extracted_value="Docker",
        evidence_text="Never used Docker",
        source="provider_verified",
        confidence=0.4,
    )

    original = record.model_dump()

    assert is_explicitly_unsupported_skill_claim(record) is True
    assert record.model_dump() == original
