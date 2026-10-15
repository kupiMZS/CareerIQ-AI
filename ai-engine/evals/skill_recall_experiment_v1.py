"""Opt-in, research-only skill-recall shadow experiment.

Not used by the public API, legacy analyzer, or benchmark provider.
Literal mentions are not proof of proficiency.
"""

import re
from collections.abc import Sequence

from app.analyzer import SECTION_ALIASES, SKILL_KEYWORDS

EXPERIMENT_VERSION = "skill-recall-shadow-v1"

EXPERIMENTAL_TERMS = (
    "Excel",
    "Spring",
    "Go",
    "Terraform",
)

_CANONICAL = {name.casefold(): name for name in EXPERIMENTAL_TERMS}

_ALLOWED = frozenset({name.casefold() for name in SKILL_KEYWORDS} | set(_CANONICAL))

_INLINE_SKILLS = re.compile(
    r"(?i)^(?:skills|technical skills|core skills|key skills|"
    r"technologies|technical expertise)\s*:\s*(.+)$"
)

_BULLET = re.compile(r"^\s*(?:[-*•▪◦‣]+\s*|\d+[.)]\s*)")

_SPLIT = re.compile(r"[,;|]")

_EXCLUDED_HEADINGS = {
    "job requirements",
    "role requirements",
    "required skills",
}


def propose_additional_skills(
    resume_text: str,
    existing_skills: Sequence[str],
) -> tuple[str, ...]:
    """Return conservative literal candidates without mutating inputs.

    Recognizes explicit skills sections and early unlabeled
    technology lists containing at least two existing skills.
    Does not infer proficiency, confidence, or missing skills.
    """
    existing = {name.strip().casefold() for name in existing_skills if name.strip()}

    proposed: list[str] = []
    proposed_keys: set[str] = set()

    active_section: str | None = None
    nonempty_position = 0

    for raw_line in resume_text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        nonempty_position += 1

        heading = line.casefold().rstrip(" :|•-").strip()

        recognized_section = SECTION_ALIASES.get(heading)

        if recognized_section is not None:
            active_section = recognized_section
            continue

        if heading in _EXCLUDED_HEADINGS:
            active_section = "excluded"
            continue

        inline_match = _INLINE_SKILLS.fullmatch(line)

        if inline_match is not None:
            content = inline_match.group(1)
        else:
            content = _BULLET.sub("", line)

        parts = [part.strip() for part in _SPLIT.split(content)]

        if not parts or any(not part for part in parts):
            continue

        normalized = [part.casefold() for part in parts]

        if any(name not in _ALLOWED for name in normalized):
            continue

        existing_on_line = {name for name in normalized if name in existing}

        early_unlabeled_list = (
            active_section is None
            and nonempty_position <= 5
            and len(parts) >= 3
            and len(existing_on_line) >= 2
        )

        explicitly_skill_scoped = inline_match is not None or active_section == "skills"

        if not (explicitly_skill_scoped or early_unlabeled_list):
            continue

        for name in normalized:
            if (
                name in _CANONICAL
                and name not in existing
                and name not in proposed_keys
            ):
                proposed.append(_CANONICAL[name])
                proposed_keys.add(name)

    return tuple(proposed)
