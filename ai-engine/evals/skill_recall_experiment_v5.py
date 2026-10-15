"""Research-only conservative skill-format recovery experiment.

Exact aliases and separators are normalized before applying
the existing Shadow v4 section-boundary protections.

Not connected to production resume analysis or the public API.
"""

import re
from collections.abc import Sequence

from app.analyzer import SECTION_ALIASES
from evals.skill_recall_experiment_v2 import _SKILL_HEADINGS
from evals.skill_recall_experiment_v4 import (
    propose_additional_skills as shadow_v4,
)

EXPERIMENT_VERSION = "skill-recall-shadow-v5"

_EXTRA_HEADINGS = frozenset({"core competencies", "stack"})

_SKILL_HEADINGS = (
    frozenset(name for name, section in SECTION_ALIASES.items() if section == "skills")
    | _SKILL_HEADINGS
    | _EXTRA_HEADINGS
)

_EXACT_ALIASES = {
    "go — golang": "Go",
    "go – golang": "Go",
    "microsoft excel (advanced)": "Excel",
    "spring framework": "Spring",
    "go (programming language)": "Go",
}

_DELIMITERS = re.compile(r"([,;|]|\s+/\s+)")
_BULLET = re.compile(r"^(?:[-*•▪◦‣]+\s*|\d+[.)]\s*)")


def _normalize_tokens(value: str) -> str:
    """Replace only exact, explicitly approved skill-token aliases."""
    parts = _DELIMITERS.split(value)
    result: list[str] = []

    for position, part in enumerate(parts):
        if position % 2:
            result.append(", " if "/" in part else part)
            continue

        token = part.strip()
        bullet = _BULLET.match(token)

        prefix = token[: bullet.end()] if bullet else ""
        name = token[bullet.end() :] if bullet else token

        normalized_name = " ".join(name.casefold().split())
        replacement = _EXACT_ALIASES.get(normalized_name, name)

        result.append(prefix + replacement)

    return "".join(result)


def _normalize_formats(resume_text: str) -> str:
    """Normalize exact skill formats conservatively.

    Immediately nested skill headings inside certain personal
    narrative sections are ambiguous and must not establish
    candidate skill ownership.
    """
    result: list[str] = []
    preceding_section: str | None = None
    narrative_text_seen = False

    narrative_sections = frozenset(
        {
            "summary",
            "career_goals",
            "career_interests",
            "career_profile",
        }
    )

    for raw in resume_text.splitlines():
        line = raw.strip()

        if not line:
            result.append(raw)
            continue

        heading = " ".join(line.casefold().rstrip(" :|•-").split())

        prefix = None
        content = None
        inline_heading = None

        if ":" in line:
            prefix, content = line.split(":", 1)
            inline_heading = " ".join(prefix.casefold().split())

        is_skill_heading = (
            heading in _SKILL_HEADINGS or inline_heading in _SKILL_HEADINGS
        )

        in_narrative = preceding_section in narrative_sections

        candidate_heading = (
            inline_heading if inline_heading in _SKILL_HEADINGS else heading
        )

        # A conventional explicit skills section can follow
        # descriptive text in a professional summary.
        allow_summary_transition = (
            preceding_section == "summary"
            and narrative_text_seen
            and candidate_heading
            in {
                "skills",
                "technical skills",
                "core skills",
                "key skills",
            }
        )

        # Other skill headings inside a narrative section
        # remain ambiguous, even after descriptive lines.
        if in_narrative and is_skill_heading and not allow_summary_transition:
            result.append("Job requirements")
            preceding_section = None
            narrative_text_seen = False
            continue

        recognized = SECTION_ALIASES.get(heading)

        if recognized is not None:
            preceding_section = recognized
            narrative_text_seen = False
        elif in_narrative and not is_skill_heading:
            narrative_text_seen = True
        else:
            preceding_section = None
            narrative_text_seen = False

        if heading in _EXTRA_HEADINGS:
            result.append("Skills")
            continue

        if inline_heading in _SKILL_HEADINGS:
            label = "Skills" if inline_heading in _EXTRA_HEADINGS else prefix

            if content.strip():
                result.append(f"{label}: {_normalize_tokens(content)}")
            else:
                result.append(label)

            continue

        result.append(_normalize_tokens(line))

    return "\n".join(result)


def propose_additional_skills(
    resume_text: str,
    existing_skills: Sequence[str],
) -> tuple[str, ...]:
    """Propose additions with exact-format recovery and v4 safety."""
    normalized = _normalize_formats(resume_text)

    return shadow_v4(normalized, existing_skills)
