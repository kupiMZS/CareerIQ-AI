import re

from app.schemas.evidence import EvidenceRecord


def verify_evidence_excerpt(
    resume_text: str,
    record: EvidenceRecord,
) -> bool:
    """Check whether an evidence excerpt occurs literally in the resume."""
    return record.evidence_text in resume_text


def verify_evidence_claim(
    resume_text: str,
    record: EvidenceRecord,
) -> bool:
    """Check literal excerpt presence and complete-unit value occurrence."""
    if not verify_evidence_excerpt(resume_text, record):
        return False

    pattern = re.compile(rf"(?<!\w){re.escape(record.extracted_value)}(?!\w)")
    return pattern.search(record.evidence_text) is not None
