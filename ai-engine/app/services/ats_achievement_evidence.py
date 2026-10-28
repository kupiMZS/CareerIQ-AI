"""Conservative textual evidence for quantified outcomes."""

import re

from app.analyzer import SECTION_ALIASES
from app.schemas.ats import ATSFinding, ATSReport

_RELEVANT_SECTIONS = frozenset({"experience", "projects", "achievements"})

_OUTCOME_VERBS = re.compile(
    r"\b(?:reduced|decreased|improved|increased|"
    r"boosted|saved|cut|grew|raised|lowered|"
    r"accelerated|shortened|expanded|achieved|"
    r"eliminated|prevented)\b",
    re.IGNORECASE,
)

_MEASUREMENT = re.compile(
    r"(?<!\w)(?:"
    r"[$€£]\s*\d[\d,]*(?:\.\d+)?"
    r"|(?:USD|BDT|EUR|GBP)\s+\d[\d,]*(?:\.\d+)?"
    r"|\d+(?:\.\d+)?\s*(?:"
    r"%(?!\w)|percent\b|percentage\s+points?\b"
    r"|hours?\b|minutes?\b|days?\b|seconds?\b"
    r"|orders?\b|transactions?\b|tickets?\b"
    r"|customers?\b|users?\b|errors?\b|defects?\b"
    r")"
    r")",
    re.IGNORECASE,
)

_UNCERTAIN = re.compile(
    r"\b(?:goal|target|planned|plan|aimed|aim|"
    r"hoped|hope|expected|expect|projected|"
    r"forecast|forecasted|will|would|intended)\b",
    re.IGNORECASE,
)

_NEGATION = re.compile(
    r"\b(?:no|not|never|without|failed|unable)\b"
    r"|didn['’]t",
    re.IGNORECASE,
)

_CLAUSE_SEPARATOR = re.compile(r"[;!?]|\.(?=\s|$)")

_LIMITATIONS = [
    (
        "Only text under recognizable Experience, Projects, "
        "or Achievements headings was examined."
    ),
    (
        "Detected outcomes are lexical evidence candidates. "
        "Their accuracy and actual impact were not verified."
    ),
    ("Original document layout and job-specific alignment were not assessed."),
]


def _relevant_lines(text: str) -> tuple[bool, list[str]]:
    """Collect text within relevant recognized sections."""

    observed_section = False
    current_section: str | None = None
    lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        heading = line.casefold().removesuffix(":").strip()

        recognized = SECTION_ALIASES.get(heading) if len(line) <= 80 else None

        if recognized is not None:
            current_section = recognized if recognized in _RELEVANT_SECTIONS else None

            if current_section:
                observed_section = True

            continue

        if current_section is not None:
            lines.append(line)

    return observed_section, lines


def _has_quantified_outcome(line: str) -> bool:
    """Require an outcome verb and measurement in one clause."""

    for clause in _CLAUSE_SEPARATOR.split(line):
        if _UNCERTAIN.search(clause):
            continue

        if _NEGATION.search(clause):
            continue

        for action in _OUTCOME_VERBS.finditer(clause):
            for metric in _MEASUREMENT.finditer(clause):
                distance = metric.start() - action.end()

                if 0 <= distance <= 90:
                    return True

    return False


def assess_quantified_outcome_evidence(
    resume_text: str,
) -> ATSReport:
    """Report explicit, unverified quantified outcome candidates.

    The function does not modify existing resume intelligence,
    calculate an ATS score, or verify real-world achievements.
    """

    text = resume_text.strip()

    if not text:
        return ATSReport(
            score=None,
            findings=[
                ATSFinding(
                    code="quantified_outcome_evidence",
                    status="not_assessed",
                    explanation="No resume text was provided.",
                )
            ],
            limitations=list(_LIMITATIONS),
        )

    observed, lines = _relevant_lines(text)

    candidates: list[str] = []

    for line in lines:
        if _has_quantified_outcome(line) and line not in candidates:
            candidates.append(line)

    if candidates:
        finding = ATSFinding(
            code="quantified_outcome_evidence",
            status="satisfied",
            explanation=(
                "At least one statement contains an outcome "
                "verb and an explicit measurement in the same "
                "clause. The claim was not independently verified."
            ),
            supporting_text=candidates[:3],
        )

    elif not observed or not lines:
        finding = ATSFinding(
            code="quantified_outcome_evidence",
            status="not_assessed",
            explanation=(
                "No evaluable statements were found beneath "
                "recognized Experience, Projects, or "
                "Achievements headings."
            ),
        )

    else:
        finding = ATSFinding(
            code="quantified_outcome_evidence",
            status="needs_attention",
            explanation=(
                "Relevant section text was present, but no "
                "explicit quantified outcome met the "
                "conservative matching rules. This does not "
                "prove that achievements are absent."
            ),
            recommendation=(
                "Where appropriate, describe genuine results "
                "using verifiable measurements. Do not invent "
                "numbers or achievements."
            ),
        )

    return ATSReport(
        score=None,
        findings=[finding],
        limitations=list(_LIMITATIONS),
    )
