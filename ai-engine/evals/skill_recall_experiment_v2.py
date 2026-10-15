"""Research-only, context-scoped skill recall shadow experiment v2.

Not imported by the production analyzer or the public API.
A literal skill mention is not proof of proficiency.
"""

import re
from collections.abc import Sequence

from app.analyzer import SECTION_ALIASES, SKILL_KEYWORDS

EXPERIMENT_VERSION = "skill-recall-shadow-v2"
EXPERIMENTAL_TERMS = ("Excel", "Spring", "Go", "Terraform")
_CANONICAL = {term.casefold(): term for term in EXPERIMENTAL_TERMS}
_ALIASES = {
    "go (golang)": "go",
    "microsoft excel": "excel",
    "terraform (infrastructure as code)": "terraform",
}
_ALLOWED = frozenset({term.casefold() for term in SKILL_KEYWORDS} | set(_CANONICAL))
_SKILL_HEADINGS = frozenset({"professional skills", "technology stack", "tools"})
_STOP_HEADINGS = frozenset(
    {
        "requirements",
        "job requirements",
        "role requirements",
        "required skills",
        "references",
    }
)
_INLINE_SKILLS = re.compile(
    r"(?i)^(?:skills|technical skills|core skills|key skills|technologies|"
    r"technical expertise|professional skills|technology stack|tools)\s*:\s*(.+)$"
)
_BULLET = re.compile(r"^\s*(?:[-*•▪◦‣]+\s*|\d+[.)]\s*)")
_SPLIT = re.compile(r"[,;|]")


def propose_additional_skills(
    resume_text: str, existing_skills: Sequence[str]
) -> tuple[str, ...]:
    """Propose literal additions only in strongly skill-scoped contexts."""
    existing = {skill.strip().casefold() for skill in existing_skills if skill.strip()}
    proposed: list[str] = []
    added: set[str] = set()
    active_section: str | None = None
    line_position = 0

    for raw in resume_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line_position += 1
        heading = line.casefold().rstrip(" :|•-").strip()

        if heading in _STOP_HEADINGS:
            active_section = "excluded"
            continue
        if heading in _SKILL_HEADINGS:
            active_section = "skills"
            continue
        recognized = SECTION_ALIASES.get(heading)
        if recognized is not None:
            active_section = recognized
            continue

        inline = _INLINE_SKILLS.fullmatch(line)
        if inline is not None and active_section not in (None, "skills"):
            continue

        content = inline.group(1) if inline is not None else _BULLET.sub("", line)
        tokens = [part.strip().casefold() for part in _SPLIT.split(content)]
        if not tokens or any(not part for part in tokens):
            continue
        if any(token not in _ALLOWED and token not in _ALIASES for token in tokens):
            continue

        names = [_ALIASES.get(token, token) for token in tokens]
        legacy_matches = {name for name in names if name in existing}
        early_list = (
            active_section is None
            and line_position <= 5
            and len(names) >= 3
            and len(legacy_matches) >= 2
        )
        if inline is None and active_section != "skills" and not early_list:
            continue

        for name in names:
            if name in _CANONICAL and name not in existing and name not in added:
                proposed.append(_CANONICAL[name])
                added.add(name)
        if inline is not None and active_section is None:
            active_section = "skills"

    return tuple(proposed)
