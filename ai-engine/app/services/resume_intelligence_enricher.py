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


def _normalize(value: str) -> str:
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
) -> None:
    _deduplicate_experience(intelligence)

    for experience_value in baseline_experience:
        job_title, company = _split_experience(experience_value)

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

    _enrich_experience(
        enriched,
        baseline.get(
            "experience",
            [],
        ),
    )

    return enriched
