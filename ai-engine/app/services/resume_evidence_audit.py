import re
from collections.abc import Sequence

from app.schemas.evidence import (
    EvidenceRecord,
    EvidenceVerificationResult,
)
from app.schemas.resume import ResumeIntelligence
from app.services.evidence_verifier import verify_evidence_record
from app.services.skill_evidence_collector import collect_literal_skill_evidence

_SKILL_NAME_PATH = re.compile(r"skills\[(\d+)\]\.name")


def audit_resume_skill_evidence(
    resume_text: str,
    intelligence: ResumeIntelligence,
    records: Sequence[EvidenceRecord],
) -> list[tuple[EvidenceRecord, EvidenceVerificationResult]]:
    """Audit explicitly supplied skill evidence without mutating inputs.

    Records and their provenance labels must be supplied by the caller.
    This function does not generate evidence or determine provenance.
    """
    audited = []

    for record in records:
        match = _SKILL_NAME_PATH.fullmatch(record.field_path)

        if match is None:
            raise ValueError(f"Unsupported skill field_path: {record.field_path}")

        index = int(match.group(1))

        if index >= len(intelligence.skills):
            raise ValueError(f"Skill index out of range: {index}")

        skill_name = intelligence.skills[index].name

        if record.extracted_value != skill_name:
            raise ValueError(
                "Evidence extracted_value does not match "
                "the referenced intelligence skill name."
            )

        result = verify_evidence_record(
            resume_text,
            record,
        )

        audited.append((record, result))

    return audited


def collect_and_audit_resume_skill_evidence(
    resume_text: str,
    intelligence: ResumeIntelligence,
) -> list[tuple[EvidenceRecord, EvidenceVerificationResult]]:
    """Collect and audit literal skill evidence without mutating inputs.

    Each matching resume line produces an independent verification result.
    No skill, evidence, or confidence values are changed.
    """
    records = collect_literal_skill_evidence(
        resume_text,
        intelligence,
    )

    return audit_resume_skill_evidence(
        resume_text,
        intelligence,
        records,
    )
