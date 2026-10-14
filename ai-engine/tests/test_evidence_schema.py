import pytest
from pydantic import ValidationError

from app.schemas.evidence import EvidenceRecord


def test_evidence_record_accepts_deterministic_evidence():
    record = EvidenceRecord(
        field_path="career_profile.career_interests[0]",
        extracted_value="Distributed systems",
        evidence_text="- Distributed systems",
        source="deterministic",
    )

    assert record.field_path == "career_profile.career_interests[0]"
    assert record.extracted_value == "Distributed systems"
    assert record.evidence_text == "- Distributed systems"
    assert record.source == "deterministic"
    assert record.confidence is None


def test_evidence_record_accepts_verified_provider_source():
    record = EvidenceRecord(
        field_path="skills[0].name",
        extracted_value="Python",
        evidence_text="Skills: Python",
        source="provider_verified",
        confidence=0.8,
    )

    assert record.source == "provider_verified"
    assert record.confidence == 0.8


@pytest.mark.parametrize(
    "field_name",
    [
        "field_path",
        "extracted_value",
        "evidence_text",
    ],
)
@pytest.mark.parametrize("invalid_value", ["", "   "])
def test_evidence_record_rejects_blank_required_fields(
    field_name,
    invalid_value,
):
    data = {
        "field_path": "skills[0].name",
        "extracted_value": "Python",
        "evidence_text": "Python",
        "source": "deterministic",
    }
    data[field_name] = invalid_value

    with pytest.raises(ValidationError):
        EvidenceRecord(**data)


@pytest.mark.parametrize("invalid_confidence", [-0.1, 1.1])
def test_evidence_record_rejects_out_of_range_confidence(
    invalid_confidence,
):
    with pytest.raises(ValidationError):
        EvidenceRecord(
            field_path="skills[0].name",
            extracted_value="Python",
            evidence_text="Python",
            source="deterministic",
            confidence=invalid_confidence,
        )


def test_evidence_record_accepts_confidence_boundaries():
    for confidence in (0.0, 1.0):
        record = EvidenceRecord(
            field_path="skills[0].name",
            extracted_value="Python",
            evidence_text="Python",
            source="deterministic",
            confidence=confidence,
        )
        assert record.confidence == confidence


def test_evidence_record_rejects_unknown_source():
    with pytest.raises(ValidationError):
        EvidenceRecord(
            field_path="skills[0].name",
            extracted_value="Python",
            evidence_text="Python",
            source="inferred",
        )


def test_evidence_record_strips_surrounding_whitespace():
    record = EvidenceRecord(
        field_path="  skills[0].name  ",
        extracted_value="  Python  ",
        evidence_text="  Skills: Python  ",
        source="deterministic",
    )

    assert record.field_path == "skills[0].name"
    assert record.extracted_value == "Python"
    assert record.evidence_text == "Skills: Python"
