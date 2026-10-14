from app.schemas.evidence import EvidenceRecord


def verify_evidence_excerpt(
    resume_text: str,
    record: EvidenceRecord,
) -> bool:
    """Check whether an evidence excerpt occurs literally in the resume."""
    return record.evidence_text in resume_text
