import re
from dataclasses import dataclass
from typing import Literal

from app.schemas.evidence import (
    EvidenceRecord,
    EvidenceVerificationResult,
)
from app.schemas.resume import ResumeIntelligence
from app.services.resume_evidence_audit import (
    collect_and_audit_resume_skill_evidence,
)

SkillEvidenceCoverageStatus = Literal[
    "no_literal_evidence",
    "literal_mention_only",
    "explicit_rejection_only",
    "mixed_mentions",
]

SkillEvidenceReviewFlag = Literal[
    "aspirational_wording",
    "requirement_wording",
    "rejection_with_contrast",
]

_ASPIRATIONAL_WORDING = re.compile(
    r"(?i)(?<!\w)(?:career\s+(?:goal|objective)\s*:\s*learn|"
    r"(?:want|plan|hope)\s+to\s+learn|"
    r"planning\s+to\s+learn|"
    r"interested\s+in\s+learning)\b"
)

_REQUIREMENT_WORDING = re.compile(
    r"(?i)(?<!\w)(?:(?:job|role)\s+requirements?|"
    r"requirements?|required\s+skills?)\s*:"
)


def _marker_targets_skill(
    excerpt: str,
    marker_pattern: re.Pattern[str],
    skill_name: str,
) -> bool:
    """Require the named skill directly after a context marker."""
    target_pattern = re.compile(rf"\s*{re.escape(skill_name)}(?![\w+#]|\.[\w]|-[\w])")

    return any(
        target_pattern.match(excerpt, marker.end()) is not None
        for marker in marker_pattern.finditer(excerpt)
    )


def _rejection_has_local_contrast(
    record: EvidenceRecord,
) -> bool:
    """Recognize contrast immediately following a skill mention."""
    pattern = re.compile(
        rf"(?<![\w+#.\-]){re.escape(record.extracted_value)}(?![\w+#]|\.[\w]|-[\w])"
        r"\s*[,;]?\s*(?:but|however)\b",
        flags=re.IGNORECASE,
    )

    return pattern.search(record.evidence_text) is not None


@dataclass(frozen=True, slots=True)
class SkillEvidenceCoverage:
    """Internal report for one extracted skill."""

    field_path: str
    skill_name: str
    status: SkillEvidenceCoverageStatus
    audited_records: tuple[
        tuple[EvidenceRecord, EvidenceVerificationResult],
        ...,
    ]
    review_flags: tuple[SkillEvidenceReviewFlag, ...] = ()


def _detect_context_review_flags(
    entries: tuple[
        tuple[EvidenceRecord, EvidenceVerificationResult],
        ...,
    ],
) -> tuple[SkillEvidenceReviewFlag, ...]:
    """Identify narrow, skill-scoped wording for manual review."""
    flags: list[SkillEvidenceReviewFlag] = []

    if any(
        _marker_targets_skill(
            record.evidence_text,
            _ASPIRATIONAL_WORDING,
            record.extracted_value,
        )
        for record, _ in entries
    ):
        flags.append("aspirational_wording")

    if any(
        _marker_targets_skill(
            record.evidence_text,
            _REQUIREMENT_WORDING,
            record.extracted_value,
        )
        for record, _ in entries
    ):
        flags.append("requirement_wording")

    if any(
        result.status == "explicitly_unsupported"
        and _rejection_has_local_contrast(record)
        for record, result in entries
    ):
        flags.append("rejection_with_contrast")

    return tuple(flags)


def summarize_resume_skill_evidence(
    resume_text: str,
    intelligence: ResumeIntelligence,
) -> list[SkillEvidenceCoverage]:
    """Summarize literal evidence without judging proficiency.

    Retain every extracted skill, including those with no
    collected evidence. Do not mutate the intelligence model.
    """
    audited = collect_and_audit_resume_skill_evidence(
        resume_text,
        intelligence,
    )

    by_path: dict[
        str,
        list[tuple[EvidenceRecord, EvidenceVerificationResult]],
    ] = {}

    for record, result in audited:
        by_path.setdefault(record.field_path, []).append((record, result))

    coverage = []

    for index, skill in enumerate(intelligence.skills):
        path = f"skills[{index}].name"
        entries = tuple(by_path.get(path, []))

        has_mention = any(
            result.status == "lexically_supported" for _, result in entries
        )

        has_rejection = any(
            result.status == "explicitly_unsupported" for _, result in entries
        )

        if has_mention and has_rejection:
            status = "mixed_mentions"
        elif has_rejection:
            status = "explicit_rejection_only"
        elif has_mention:
            status = "literal_mention_only"
        else:
            status = "no_literal_evidence"

        coverage.append(
            SkillEvidenceCoverage(
                field_path=path,
                skill_name=skill.name,
                status=status,
                audited_records=entries,
                review_flags=_detect_context_review_flags(entries),
            )
        )

    return coverage
