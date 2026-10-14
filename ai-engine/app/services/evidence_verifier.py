import re

from app.schemas.evidence import (
    EvidenceRecord,
    EvidenceVerificationResult,
)


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


_SKILL_PATH_PATTERN = re.compile(r"^skills\[\d+\]\.name$")

_UNSUPPORTED_SKILL_PREFIXES = (
    "no experience with",
    "never used",
    "not familiar with",
    "currently learning",
    "learning",
)


def is_explicitly_unsupported_skill_claim(
    record: EvidenceRecord,
) -> bool:
    """Detect a narrow set of explicit skill-negation statements."""
    if _SKILL_PATH_PATTERN.fullmatch(record.field_path) is None:
        return False

    value = re.escape(record.extracted_value)

    for prefix in _UNSUPPORTED_SKILL_PREFIXES:
        pattern = re.compile(
            rf"(?i)(?<!\w){re.escape(prefix)}\s+"
            rf"{value}(?!\w)"
        )
        if pattern.search(record.evidence_text):
            return True

    return False


def verify_evidence_record(
    resume_text: str,
    record: EvidenceRecord,
) -> EvidenceVerificationResult:
    """Combine literal, lexical, and explicit rejection checks."""
    if not verify_evidence_excerpt(resume_text, record):
        return EvidenceVerificationResult(
            status="excerpt_not_found",
            excerpt_found=False,
            claim_found=False,
        )

    if not verify_evidence_claim(resume_text, record):
        return EvidenceVerificationResult(
            status="claim_not_found",
            excerpt_found=True,
            claim_found=False,
        )

    if is_explicitly_unsupported_skill_claim(record):
        return EvidenceVerificationResult(
            status="explicitly_unsupported",
            excerpt_found=True,
            claim_found=True,
            explicitly_unsupported=True,
        )

    return EvidenceVerificationResult(
        status="lexically_supported",
        excerpt_found=True,
        claim_found=True,
    )
