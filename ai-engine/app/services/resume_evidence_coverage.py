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
            )
        )

    return coverage
