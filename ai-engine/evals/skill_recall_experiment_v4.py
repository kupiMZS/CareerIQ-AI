"""Research-only nested-section safety experiment.

Shadow v4 preserves v3 boundaries and prevents nested skill
headings from reactivating extraction inside excluded sections.

Not imported by the production analyzer or public API.
"""

from collections.abc import Sequence

from app.analyzer import SECTION_ALIASES
from evals.skill_recall_experiment_v2 import (
    _SKILL_HEADINGS,
)
from evals.skill_recall_experiment_v2 import (
    propose_additional_skills as shadow_v2,
)
from evals.skill_recall_experiment_v3 import (
    _normalize_boundaries as normalize_v3,
)

EXPERIMENT_VERSION = "skill-recall-shadow-v4"


def _suppress_nested_skill_headings(resume_text: str) -> str:
    """Suppress skill headings until a valid section transition."""
    normalized = normalize_v3(resume_text)

    lines: list[str] = []
    excluded = False

    for raw in normalized.splitlines():
        line = raw.strip()
        heading = " ".join(line.casefold().rstrip(" :|•-").split())

        if heading == "job requirements":
            excluded = True
            lines.append(raw)
            continue

        section = SECTION_ALIASES.get(heading)

        if section is not None and section != "skills":
            excluded = False

        if excluded and heading in _SKILL_HEADINGS:
            lines.append("Job requirements")
            continue

        lines.append(raw)

    return "\n".join(lines)


def propose_additional_skills(
    resume_text: str,
    existing_skills: Sequence[str],
) -> tuple[str, ...]:
    """Apply v2 skill matching after v4 boundary protection."""
    safe_text = _suppress_nested_skill_headings(resume_text)

    return shadow_v2(
        safe_text,
        existing_skills,
    )
