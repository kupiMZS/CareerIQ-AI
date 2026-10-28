"""Conservative, text-based ATS structure assessment."""

from app.analyzer import SECTION_ALIASES, extract_email
from app.schemas.ats import ATSFinding, ATSReport

_SECTION_LABELS = {
    "skills": "Skills",
    "education": "Education",
    "experience": "Experience",
}

_LIMITATIONS = [
    (
        "Only extracted resume text was examined; original "
        "document layout and formatting were not assessed."
    ),
    ("No job description was provided; job-specific alignment was not assessed."),
]


def _recognized_sections(text: str) -> dict[str, str]:
    """Find explicitly labeled sections, not casual mentions."""

    recognized: dict[str, str] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line or len(line) > 80:
            continue

        heading = line.casefold().removesuffix(":").strip()
        section = SECTION_ALIASES.get(heading)

        if section in _SECTION_LABELS and section not in recognized:
            recognized[section] = line

    return recognized


def assess_resume_structure(resume_text: str) -> ATSReport:
    """Assess observable contact and section text only.

    The report is deliberately unscored and has no effect
    on the existing public analysis contract.
    """

    text = resume_text.strip()
    codes = (
        "contact_email",
        "section_skills",
        "section_education",
        "section_experience",
    )

    if not text:
        return ATSReport(
            findings=[
                ATSFinding(
                    code=code,
                    status="not_assessed",
                    explanation="No resume text was provided.",
                )
                for code in codes
            ],
            limitations=list(_LIMITATIONS),
        )

    findings: list[ATSFinding] = []

    email = extract_email(text)

    if email:
        findings.append(
            ATSFinding(
                code="contact_email",
                status="satisfied",
                explanation=(
                    "A recognizable email address was found "
                    "in the supplied resume text."
                ),
                supporting_text=[email],
            )
        )
    else:
        findings.append(
            ATSFinding(
                code="contact_email",
                status="needs_attention",
                explanation=(
                    "No recognizable email address was found "
                    "in the supplied resume text."
                ),
                recommendation=(
                    "Check that your contact email is present "
                    "and readable in the resume text."
                ),
            )
        )

    recognized = _recognized_sections(text)

    for section, label in _SECTION_LABELS.items():
        heading = recognized.get(section)

        if heading:
            findings.append(
                ATSFinding(
                    code=f"section_{section}",
                    status="satisfied",
                    explanation=(f"A recognizable {label} section heading was found."),
                    supporting_text=[heading],
                )
            )
        else:
            findings.append(
                ATSFinding(
                    code=f"section_{section}",
                    status="needs_attention",
                    explanation=(
                        f"No recognizable {label} section "
                        "heading was found. This does not "
                        "establish that the underlying "
                        "information is absent."
                    ),
                    recommendation=(
                        f"Consider a clearly labeled {label} "
                        "section when relevant to your resume."
                    ),
                )
            )

    return ATSReport(
        score=None,
        findings=findings,
        limitations=list(_LIMITATIONS),
    )


_CONTENT_PLACEHOLDERS = {
    "n/a",
    "none",
    "not applicable",
    "pending",
    "tbd",
    "to be added",
    "",
}


def assess_resume_section_content(resume_text: str) -> ATSReport:
    """Check for text beneath recognized section headings.

    This does not verify qualifications, experience, or
    the truth of any statement in the supplied resume.
    """

    text = resume_text.strip()

    section_codes = {
        section: f"section_{section}_content" for section in _SECTION_LABELS
    }

    limitations = [
        *_LIMITATIONS,
        (
            "Section content checks establish only the presence "
            "of non-placeholder text under recognized headings; "
            "they do not validate qualifications or experience."
        ),
    ]

    if not text:
        return ATSReport(
            findings=[
                ATSFinding(
                    code=code,
                    status="not_assessed",
                    explanation="No resume text was provided.",
                )
                for code in section_codes.values()
            ],
            limitations=limitations,
        )

    observed: set[str] = set()

    bodies: dict[str, list[str]] = {section: [] for section in _SECTION_LABELS}

    current_section: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        heading = line.casefold().removesuffix(":").strip()

        recognized = SECTION_ALIASES.get(heading) if len(line) <= 80 else None

        if recognized is not None:
            if recognized in bodies:
                current_section = recognized
                observed.add(recognized)
            else:
                current_section = None

            continue

        if current_section is None:
            continue

        normalized = line.casefold().strip(" .:-—–")

        if normalized in _CONTENT_PLACEHOLDERS:
            continue

        bodies[current_section].append(line)

    findings: list[ATSFinding] = []

    for section, label in _SECTION_LABELS.items():
        code = section_codes[section]

        if section not in observed:
            findings.append(
                ATSFinding(
                    code=code,
                    status="not_assessed",
                    explanation=(
                        f"No recognizable {label} heading was "
                        "found, so its section content could "
                        "not be evaluated separately."
                    ),
                )
            )

        elif not bodies[section]:
            findings.append(
                ATSFinding(
                    code=code,
                    status="needs_attention",
                    explanation=(
                        f"The {label} heading was found, "
                        "but no non-placeholder content "
                        "was detected beneath it."
                    ),
                    recommendation=(
                        f"Review the {label} section and "
                        "include relevant information "
                        "when applicable."
                    ),
                )
            )

        else:
            findings.append(
                ATSFinding(
                    code=code,
                    status="satisfied",
                    explanation=(
                        f"Non-placeholder text was detected "
                        f"beneath a recognized {label} heading. "
                        "Its factual accuracy was not verified."
                    ),
                    supporting_text=[bodies[section][0]],
                )
            )

    return ATSReport(
        score=None,
        findings=findings,
        limitations=limitations,
    )
