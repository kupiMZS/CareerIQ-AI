import re

from app.schemas.evidence import EvidenceRecord
from app.schemas.resume import ResumeIntelligence


def collect_literal_skill_evidence(
    resume_text: str,
    intelligence: ResumeIntelligence,
) -> list[EvidenceRecord]:
    """Collect literal resume excerpts for existing skill names.

    The deterministic source label describes excerpt collection,
    not the origin of the skill or proof of candidate proficiency.

    No evidence, skill, or confidence values are modified.
    """
    patterns = []

    for index, skill in enumerate(intelligence.skills):
        name = skill.name

        # Avoid empty and non-canonical names. EvidenceRecord
        # strips whitespace, so padded names cannot retain the
        # exact extracted-value identity required by the audit.
        if not name or name != name.strip():
            continue

        pattern = re.compile(rf"(?<![\w+#.\-]){re.escape(name)}(?![\w+#]|\.[\w]|-[\w])")

        patterns.append((index, name, pattern))

    records = []

    for line in resume_text.splitlines():
        # Trimming surrounding whitespace still leaves an exact
        # contiguous excerpt of the original resume.
        excerpt = line.strip()

        if not excerpt:
            continue

        for index, name, pattern in patterns:
            if pattern.search(excerpt) is None:
                continue

            records.append(
                EvidenceRecord(
                    field_path=f"skills[{index}].name",
                    extracted_value=name,
                    evidence_text=excerpt,
                    source="deterministic",
                )
            )

    return records
