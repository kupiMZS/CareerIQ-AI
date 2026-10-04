import re

from app.analyzer import analyze_resume, detect_sections
from app.schemas.resume import (
    Education,
    Experience,
    ResumeIntelligence,
    Skill,
)

JOB_TITLE_KEYWORDS = (
    "engineer",
    "developer",
    "manager",
    "analyst",
    "consultant",
    "intern",
    "researcher",
    "designer",
    "scientist",
    "administrator",
    "architect",
    "specialist",
    "director",
    "officer",
)

INSTITUTION_KEYWORDS = (
    "university",
    "college",
    "institute",
    "school",
    "academy",
    "polytechnic",
)

LIST_PREFIX_PATTERN = re.compile(r"^\s*(?:[-*•▪◦‣]+|\d+[.)])\s*")

EXPERIENCE_DATE_RANGE_PATTERN = re.compile(
    r"^(?P<start>\d{4})\s*[-–—]\s*"
    r"(?P<end>\d{4}|present|current)$",
    re.IGNORECASE,
)

DATE_EVIDENCE_PATTERN = re.compile(
    r"\b(?:19|20)\d{2}\b|\b(?:present|current)\b",
    re.IGNORECASE,
)

EXPERIENCE_DATE_LINE_PATTERN = re.compile(
    r"^(?:[A-Za-z]{3,9}\s+)?(?:19|20)\d{2}\s*[-–—]\s*"
    r"(?:(?:[A-Za-z]{3,9}\s+)?(?:19|20)\d{2}|present|current)$",
    re.IGNORECASE,
)


def _normalize(
    value: str,
) -> str:
    return value.strip().casefold()


def _normalize_optional(
    value: str | None,
) -> str | None:
    if not value:
        return None

    normalized = _normalize(value)

    return normalized or None


def _strip_list_prefix(
    value: str,
) -> str:
    return LIST_PREFIX_PATTERN.sub(
        "",
        value,
    ).strip()


def _looks_like_job_title(
    value: str,
) -> bool:
    normalized = _normalize(value)

    return any(keyword in normalized for keyword in JOB_TITLE_KEYWORDS)


def _extract_headline(
    resume_text: str,
    *,
    candidate_name: str | None,
    candidate_email: str | None,
) -> str | None:
    normalized_name = _normalize_optional(candidate_name)
    normalized_email = _normalize_optional(candidate_email)

    for raw_line in resume_text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        # A recognized section heading marks the end
        # of the resume preamble.
        if detect_sections(line):
            break

        normalized_line = _normalize(line)

        if normalized_name is not None and normalized_line == normalized_name:
            continue

        if normalized_email is not None and normalized_email in normalized_line:
            continue

        if _looks_like_job_title(line):
            return line

    return None


def _looks_like_institution(
    value: str,
) -> bool:
    normalized = _normalize(value)

    return any(keyword in normalized for keyword in INSTITUTION_KEYWORDS)


def _split_education(
    value: str,
) -> tuple[str | None, str | None]:
    cleaned = _strip_list_prefix(value)

    separator = " at "

    if separator not in cleaned:
        return (
            cleaned or None,
            None,
        )

    degree, institution = cleaned.split(
        separator,
        maxsplit=1,
    )

    return (
        degree.strip() or None,
        institution.strip() or None,
    )


def _split_experience(
    value: str,
) -> tuple[str | None, str | None]:
    cleaned = _strip_list_prefix(value)

    if "|" in cleaned:
        left, right = cleaned.split(
            "|",
            maxsplit=1,
        )

        left = left.strip()
        right = right.strip()

        left_is_title = _looks_like_job_title(left)
        right_is_title = _looks_like_job_title(right)

        if right_is_title and not left_is_title:
            return (
                right or None,
                left or None,
            )

        return (
            left or None,
            right or None,
        )

    for separator in (
        " at ",
        " - ",
        " – ",
        " — ",
    ):
        if separator not in cleaned:
            continue

        job_title, company = cleaned.split(
            separator,
            maxsplit=1,
        )

        return (
            job_title.strip() or None,
            company.strip() or None,
        )

    return (
        cleaned or None,
        None,
    )


def _parse_experience_date_range(
    value: str,
) -> tuple[str, str] | None:
    match = EXPERIENCE_DATE_RANGE_PATTERN.fullmatch(value.strip())

    if match is None:
        return None

    start_date = match.group("start")
    end_date = match.group("end")

    if end_date.casefold() in {
        "present",
        "current",
    }:
        end_date = "Present"

    return (
        start_date,
        end_date,
    )


def _has_date_evidence(
    lines: list[str],
) -> bool:
    return any(DATE_EVIDENCE_PATTERN.search(line) is not None for line in lines)


def _extract_experience_responsibilities(
    block_lines: list[str],
) -> list[str]:
    responsibilities: list[str] = []
    seen: set[str] = set()

    for line in block_lines:
        value = " ".join(_strip_list_prefix(line).split())

        if not value:
            continue

        if _parse_experience_date_range(value) is not None:
            continue

        if EXPERIENCE_DATE_LINE_PATTERN.fullmatch(value):
            continue

        normalized = _normalize(value)

        if normalized in seen:
            continue

        seen.add(normalized)
        responsibilities.append(value)

    return responsibilities


def _normalize_education_entry(
    item: Education,
) -> None:
    if not item.degree or item.institution:
        return

    degree, institution = _split_education(item.degree)

    if institution is None:
        return

    item.degree = degree
    item.institution = institution


def _education_entries_are_mergeable(
    first: Education,
    second: Education,
) -> bool:
    first_degree = _normalize_optional(first.degree)
    second_degree = _normalize_optional(second.degree)

    first_institution = _normalize_optional(first.institution)
    second_institution = _normalize_optional(second.institution)

    first_is_empty = first_degree is None and first_institution is None
    second_is_empty = second_degree is None and second_institution is None

    if first_is_empty or second_is_empty:
        return True

    same_degree = (
        first_degree is not None
        and second_degree is not None
        and first_degree == second_degree
    )

    same_institution = (
        first_institution is not None
        and second_institution is not None
        and first_institution == second_institution
    )

    if same_degree and same_institution:
        return True

    if same_institution and (first_degree is None or second_degree is None):
        return True

    return same_degree and (first_institution is None or second_institution is None)


def _merge_education_values(
    target: Education,
    source: Education,
) -> None:
    for field_name in (
        "institution",
        "degree",
        "field_of_study",
        "start_date",
        "end_date",
    ):
        target_value = getattr(
            target,
            field_name,
        )

        source_value = getattr(
            source,
            field_name,
        )

        if target_value is None and source_value is not None:
            setattr(
                target,
                field_name,
                source_value,
            )


def _deduplicate_education(
    intelligence: ResumeIntelligence,
) -> None:
    merged: list[Education] = []

    for item in intelligence.education:
        _normalize_education_entry(item)

        matching_entry = next(
            (
                existing
                for existing in merged
                if _education_entries_are_mergeable(
                    existing,
                    item,
                )
            ),
            None,
        )

        if matching_entry is None:
            merged.append(item)
            continue

        _merge_education_values(
            matching_entry,
            item,
        )

    intelligence.education = merged


def _enrich_multiline_education(
    intelligence: ResumeIntelligence,
    resume_text: str,
    baseline_education: list[str],
) -> None:
    sections = detect_sections(resume_text)

    education_lines = sections.get(
        "education",
        [],
    )

    if len(education_lines) < 2:
        return

    baseline_degrees: set[str] = set()

    for education_value in baseline_education:
        degree, _ = _split_education(education_value)

        if degree:
            baseline_degrees.add(_normalize(degree))

    for index, raw_line in enumerate(education_lines[:-1]):
        degree_line = _strip_list_prefix(raw_line)

        degree, inline_institution = _split_education(degree_line)

        if not degree:
            continue

        if inline_institution is not None:
            continue

        if _normalize(degree) not in baseline_degrees:
            continue

        institution = _strip_list_prefix(education_lines[index + 1])

        if not _looks_like_institution(institution):
            continue

        candidate = Education(
            degree=degree,
            institution=institution,
        )

        matching_entry = next(
            (
                item
                for item in intelligence.education
                if _education_entries_are_mergeable(
                    item,
                    candidate,
                )
            ),
            None,
        )

        if matching_entry is not None:
            _merge_education_values(
                matching_entry,
                candidate,
            )
            continue

        intelligence.education.append(candidate)

    _deduplicate_education(intelligence)


def _normalize_experience_entry(
    item: Experience,
) -> None:
    if not item.job_title or item.company:
        return

    job_title, company = _split_experience(item.job_title)

    if company is None:
        return

    item.job_title = job_title
    item.company = company


def _experience_entries_are_mergeable(
    first: Experience,
    second: Experience,
) -> bool:
    first_title = _normalize_optional(first.job_title)
    second_title = _normalize_optional(second.job_title)

    first_company = _normalize_optional(first.company)
    second_company = _normalize_optional(second.company)

    first_is_empty = first_title is None and first_company is None
    second_is_empty = second_title is None and second_company is None

    if first_is_empty or second_is_empty:
        return True

    same_title = (
        first_title is not None
        and second_title is not None
        and first_title == second_title
    )

    same_company = (
        first_company is not None
        and second_company is not None
        and first_company == second_company
    )

    if same_title and same_company:
        return True

    if same_title and (first_company is None or second_company is None):
        return True

    return same_company and (first_title is None or second_title is None)


def _merge_experience_values(
    target: Experience,
    source: Experience,
) -> None:
    for field_name in (
        "company",
        "job_title",
        "start_date",
        "end_date",
    ):
        target_value = getattr(
            target,
            field_name,
        )

        source_value = getattr(
            source,
            field_name,
        )

        if target_value is None and source_value is not None:
            setattr(
                target,
                field_name,
                source_value,
            )

    if not target.responsibilities and source.responsibilities:
        target.responsibilities = list(source.responsibilities)


def _deduplicate_experience(
    intelligence: ResumeIntelligence,
) -> None:
    merged: list[Experience] = []

    for item in intelligence.experience:
        _normalize_experience_entry(item)

        matching_entry = next(
            (
                existing
                for existing in merged
                if _experience_entries_are_mergeable(
                    existing,
                    item,
                )
            ),
            None,
        )

        if matching_entry is None:
            merged.append(item)
            continue

        _merge_experience_values(
            matching_entry,
            item,
        )

    intelligence.experience = merged


def _extract_structured_experience_blocks(
    experience_lines: list[str],
) -> list[
    tuple[
        Experience,
        list[str],
    ]
]:
    blocks: list[
        tuple[
            Experience,
            list[str],
        ]
    ] = []

    current_entry: Experience | None = None
    current_lines: list[str] = []

    for line in experience_lines:
        job_title, company = _split_experience(line)

        is_strong_entry = (
            job_title is not None
            and company is not None
            and _looks_like_job_title(job_title)
        )

        if is_strong_entry:
            if current_entry is not None:
                blocks.append(
                    (
                        current_entry,
                        current_lines,
                    )
                )

            current_entry = Experience(
                job_title=job_title,
                company=company,
            )

            current_lines = []
            continue

        if current_entry is not None:
            current_lines.append(line)

    if current_entry is not None:
        blocks.append(
            (
                current_entry,
                current_lines,
            )
        )

    return blocks


def _reconcile_explicit_experience(
    intelligence: ResumeIntelligence,
    experience_lines: list[str],
) -> None:
    blocks = _extract_structured_experience_blocks(experience_lines)

    if not blocks:
        return

    strong_signatures = {
        (
            _normalize_optional(entry.job_title),
            _normalize_optional(entry.company),
        )
        for entry, _ in blocks
    }

    # When an explicit Experience section contains
    # strong title + company records, discard
    # title-only records that are not backed by one
    # of those structured jobs. This prevents
    # responsibility lines such as "Built internal
    # APIs" or "Mentored junior engineers" from
    # becoming fake Experience entries.
    intelligence.experience = [
        item
        for item in intelligence.experience
        if (
            item.company is not None
            or (
                _normalize_optional(item.job_title),
                _normalize_optional(item.company),
            )
            in strong_signatures
        )
    ]

    for evidence_entry, block_lines in blocks:
        matching_entry = next(
            (
                item
                for item in intelligence.experience
                if _experience_entries_are_mergeable(
                    item,
                    evidence_entry,
                )
            ),
            None,
        )

        if matching_entry is None:
            matching_entry = evidence_entry.model_copy(deep=True)

            intelligence.experience.append(matching_entry)
        else:
            _merge_experience_values(
                matching_entry,
                evidence_entry,
            )

        parsed_dates = None

        for line in block_lines:
            parsed_dates = _parse_experience_date_range(line)

            if parsed_dates is not None:
                break

        if parsed_dates is not None:
            (
                matching_entry.start_date,
                matching_entry.end_date,
            ) = parsed_dates

        elif not _has_date_evidence(block_lines):
            # The explicit job block contains no
            # date evidence. Remove unsupported
            # provider dates rather than preserving
            # a hallucinated date from another
            # section of the resume.
            matching_entry.start_date = None
            matching_entry.end_date = None

        # Literal responsibility lines from a strong
        # Experience block are authoritative. This
        # replaces unsupported provider-generated
        # responsibilities while preserving the
        # association with the correct job.
        matching_entry.responsibilities = _extract_experience_responsibilities(
            block_lines
        )

    _deduplicate_experience(intelligence)


def _enrich_skills(
    intelligence: ResumeIntelligence,
    baseline_skills: list[str],
) -> None:
    existing_skills = {_normalize(skill.name) for skill in intelligence.skills}

    for skill_name in baseline_skills:
        normalized_name = _normalize(skill_name)

        if normalized_name in existing_skills:
            continue

        intelligence.skills.append(
            Skill(
                name=skill_name,
            )
        )

        existing_skills.add(normalized_name)


def _enrich_education(
    intelligence: ResumeIntelligence,
    baseline_education: list[str],
) -> None:
    _deduplicate_education(intelligence)

    for education_value in baseline_education:
        degree, institution = _split_education(education_value)

        candidate = Education(
            degree=degree,
            institution=institution,
        )

        matching_entry = next(
            (
                item
                for item in intelligence.education
                if _education_entries_are_mergeable(
                    item,
                    candidate,
                )
            ),
            None,
        )

        if matching_entry is not None:
            _merge_education_values(
                matching_entry,
                candidate,
            )
            continue

        intelligence.education.append(candidate)

    _deduplicate_education(intelligence)


def _enrich_experience(
    intelligence: ResumeIntelligence,
    baseline_experience: list[str],
    *,
    has_explicit_experience_section: bool,
    has_strong_experience_entries: bool,
) -> None:
    _deduplicate_experience(intelligence)

    for experience_value in baseline_experience:
        job_title, company = _split_experience(experience_value)

        # If an explicit Experience section already
        # gives us strong title + company records,
        # do not let title-only rule-based matches
        # become additional Experience entries.
        if (
            has_explicit_experience_section
            and has_strong_experience_entries
            and company is None
        ):
            continue

        # Preserve the existing no-section guard:
        # without an explicit Experience section,
        # only accept a baseline candidate when it
        # also contains company structure.
        if not has_explicit_experience_section and company is None:
            continue

        candidate = Experience(
            job_title=job_title,
            company=company,
        )

        matching_entry = next(
            (
                item
                for item in intelligence.experience
                if _experience_entries_are_mergeable(
                    item,
                    candidate,
                )
            ),
            None,
        )

        if matching_entry is not None:
            _merge_experience_values(
                matching_entry,
                candidate,
            )
            continue

        intelligence.experience.append(candidate)

    _deduplicate_experience(intelligence)


def enrich_resume_intelligence(
    resume_text: str,
    intelligence: ResumeIntelligence,
) -> ResumeIntelligence:
    enriched = intelligence.model_copy(deep=True)

    baseline = analyze_resume(resume_text)

    baseline_name = baseline.get("extracted_name")
    baseline_email = baseline.get("extracted_email")

    if not enriched.candidate.name and baseline_name:
        enriched.candidate.name = baseline_name

    if not enriched.candidate.email and baseline_email:
        enriched.candidate.email = baseline_email

    if not enriched.candidate.headline:
        enriched.candidate.headline = _extract_headline(
            resume_text,
            candidate_name=(enriched.candidate.name or baseline_name),
            candidate_email=(enriched.candidate.email or baseline_email),
        )

    _enrich_skills(
        enriched,
        baseline.get(
            "skills",
            [],
        ),
    )

    baseline_education = baseline.get(
        "education",
        [],
    )

    _enrich_education(
        enriched,
        baseline_education,
    )

    _enrich_multiline_education(
        enriched,
        resume_text,
        baseline_education,
    )

    sections = detect_sections(resume_text)

    experience_lines = sections.get(
        "experience",
        [],
    )

    structured_experience_blocks = _extract_structured_experience_blocks(
        experience_lines
    )

    _enrich_experience(
        enriched,
        baseline.get(
            "experience",
            [],
        ),
        has_explicit_experience_section=("experience" in sections),
        has_strong_experience_entries=bool(structured_experience_blocks),
    )

    if experience_lines:
        _reconcile_explicit_experience(
            enriched,
            experience_lines,
        )

    return enriched
