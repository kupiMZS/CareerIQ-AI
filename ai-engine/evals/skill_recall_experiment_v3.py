"""Research-only boundary hardening for skill recall.

Shadow v3 delegates skill matching to v2 after normalizing
additional non-candidate section boundaries.

Not imported by the production analyzer or public API.
"""

import re
from collections.abc import Sequence

from app.analyzer import SECTION_ALIASES
from evals.skill_recall_experiment_v2 import (
    _STOP_HEADINGS,
)
from evals.skill_recall_experiment_v2 import (
    propose_additional_skills as shadow_v2,
)

EXPERIMENT_VERSION = "skill-recall-shadow-v3"

_EXTRA_STOP = re.compile(
    r"(?:job|position|role|client)\s+"
    r"(?:description|requirements)"
    r"|(?:professional|personal)\s+references",
    re.IGNORECASE,
)

_INLINE_REFERENCES = re.compile(
    r"(?:professional\s+)?references\s*:\s*.+",
    re.IGNORECASE,
)


def _normalize_boundaries(resume_text: str) -> str:
    """Preserve content while marking non-candidate sections.

    A nested Skills heading inside an excluded section
    does not re-enable candidate skill extraction.
    """
    lines: list[str] = []
    excluded = False

    for raw in resume_text.splitlines():
        line = raw.strip()
        heading = " ".join(line.casefold().rstrip(" :|•-").split())

        stop = (
            heading in _STOP_HEADINGS
            or _EXTRA_STOP.fullmatch(heading) is not None
            or _INLINE_REFERENCES.fullmatch(line) is not None
        )

        if stop:
            excluded = True
            lines.append("Job requirements")
            continue

        recognized = SECTION_ALIASES.get(heading)

        if excluded and recognized == "skills":
            lines.append("Job requirements")
            continue

        if recognized is not None and recognized != "skills":
            excluded = False

        lines.append(raw)

    return "\n".join(lines)


def propose_additional_skills(
    resume_text: str,
    existing_skills: Sequence[str],
) -> tuple[str, ...]:
    """Propose v2 skill matches with safer section boundaries."""
    normalized = _normalize_boundaries(resume_text)

    return shadow_v2(
        normalized,
        existing_skills,
    )
