"""Research-only, section-scoped vocabulary expansion.

Only explicitly formatted skill declarations may introduce
the additional technologies. Production is unchanged.
"""

import re
from collections.abc import Sequence

from app.analyzer import SECTION_ALIASES
from evals.skill_recall_experiment_v5 import (
    _normalize_formats,
)
from evals.skill_recall_experiment_v5 import (
    propose_additional_skills as shadow_v5,
)

EXPERIMENT_VERSION = "skill-recall-shadow-v6"

NEW_TERMS = (
    "Dart",
    "Flutter",
    "ASP.NET Core",
    "Express.js",
    "SignalR",
    "Socket.IO",
    "SQL Server",
    "Jest",
)

_CANONICAL = {name.casefold(): name for name in NEW_TERMS}

_EXTRA_SKILL_HEADINGS = frozenset(
    {
        "professional skills",
        "technology stack",
        "tools",
        "core competencies",
        "stack",
    }
)

_CATEGORIES = frozenset(
    {
        "programming languages",
        "frontend & mobile",
        "backend & apis",
        "databases",
        "testing & qa",
        "cloud & devops",
        "ai integration",
        "frameworks",
        "technologies",
        "tools",
        "frontend",
        "backend",
        "mobile",
        "testing",
    }
)

_BLOCKED_HEADINGS = frozenset(
    {
        "requirements",
        "job requirements",
        "role requirements",
        "required skills",
        "references",
    }
)

_SPLIT = re.compile(r"[,;|]")


def _heading(value: str) -> str:
    return " ".join(value.casefold().rstrip(" :|•-").split())


def _recover_explicit_technologies(
    normalized_text: str,
    existing: set[str],
) -> tuple[str, ...]:
    """Recover explicit terms without nested-section reactivation."""
    active = False
    blocked = False
    section: str | None = None
    found: list[str] = []
    seen: set[str] = set(existing)

    def can_start_skills() -> bool:
        # Conservative rule: an apparent skills heading inside
        # an unrelated section is not a trusted boundary.
        return not blocked and section in (None, "summary", "skills")

    def collect(value: str) -> None:
        for part in _SPLIT.split(value):
            token = " ".join(part.strip().casefold().split())
            canonical = _CANONICAL.get(token)

            if canonical is None or token in seen:
                continue

            seen.add(token)
            found.append(canonical)

    for raw_line in normalized_text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        heading = _heading(line)

        if heading in _BLOCKED_HEADINGS:
            blocked = True
            active = False
            section = "excluded"
            continue

        recognized = SECTION_ALIASES.get(heading)

        if recognized is not None:
            if recognized == "skills":
                active = can_start_skills()
                if active:
                    section = "skills"
            else:
                active = False
                blocked = False
                section = recognized
            continue

        if heading in _EXTRA_SKILL_HEADINGS:
            active = can_start_skills()
            if active:
                section = "skills"
            continue

        prefix, separator, content = line.partition(":")
        prefix_heading = _heading(prefix)

        if separator and (
            SECTION_ALIASES.get(prefix_heading) == "skills"
            or prefix_heading in _EXTRA_SKILL_HEADINGS
        ):
            active = can_start_skills()
            if active:
                section = "skills"
                collect(content)
            continue

        if active and separator and prefix_heading in _CATEGORIES:
            collect(content)
            continue

        # Stop at prose or unknown headings. Do not allow
        # later nested skill headings to reopen that scope.
        active = False
        if section == "skills":
            section = "unstructured"

    return tuple(found)


def propose_additional_skills(
    resume_text: str,
    existing_skills: Sequence[str],
) -> tuple[str, ...]:
    """Compose v5 recovery with cautious new vocabulary."""
    previous = shadow_v5(resume_text, existing_skills)

    existing = {
        skill.strip().casefold()
        for skill in (*existing_skills, *previous)
        if skill.strip()
    }

    normalized = _normalize_formats(resume_text)

    additional = _recover_explicit_technologies(
        normalized,
        existing,
    )

    return (*previous, *additional)
