from app.analyzer import analyze_resume
from app.schemas.resume import (
    Education,
    Experience,
    ResumeIntelligence,
    Skill,
)


def _normalize(value: str) -> str:
    return value.strip().casefold()


def _split_experience(
    value: str,
) -> tuple[str | None, str | None]:
    separator = " at "

    if separator not in value:
        cleaned = value.strip()

        return (
            cleaned or None,
            None,
        )

    job_title, company = value.split(
        separator,
        maxsplit=1,
    )

    return (
        job_title.strip() or None,
        company.strip() or None,
    )


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
    for education_value in baseline_education:
        normalized_value = _normalize(education_value)

        already_present = any(
            item.degree and _normalize(item.degree) == normalized_value
            for item in intelligence.education
        )

        if already_present:
            continue

        empty_degree_entry = next(
            (item for item in intelligence.education if not item.degree),
            None,
        )

        if empty_degree_entry is not None:
            empty_degree_entry.degree = education_value
            continue

        intelligence.education.append(
            Education(
                degree=education_value,
            )
        )


def _enrich_experience(
    intelligence: ResumeIntelligence,
    baseline_experience: list[str],
) -> None:
    for experience_value in baseline_experience:
        job_title, company = _split_experience(experience_value)

        normalized_full = _normalize(experience_value)

        normalized_job_title = _normalize(job_title) if job_title else None

        normalized_company = _normalize(company) if company else None

        matching_entry = next(
            (
                item
                for item in intelligence.experience
                if (item.job_title and _normalize(item.job_title) == normalized_full)
                or (
                    item.job_title
                    and normalized_job_title
                    and _normalize(item.job_title) == normalized_job_title
                )
                or (
                    item.company
                    and normalized_company
                    and _normalize(item.company) == normalized_company
                )
                or (
                    item.job_title
                    and item.company
                    and _normalize((f"{item.job_title} at {item.company}"))
                    == normalized_full
                )
            ),
            None,
        )

        if matching_entry is not None:
            if (
                matching_entry.job_title
                and _normalize(matching_entry.job_title) == normalized_full
                and job_title
                and company
            ):
                matching_entry.job_title = job_title

                if not matching_entry.company:
                    matching_entry.company = company

                continue

            if not matching_entry.job_title and job_title:
                matching_entry.job_title = job_title

            if not matching_entry.company and company:
                matching_entry.company = company

            continue

        intelligence.experience.append(
            Experience(
                job_title=job_title,
                company=company,
            )
        )


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

    _enrich_education(
        enriched,
        baseline.get(
            "education",
            [],
        ),
    )

    _enrich_experience(
        enriched,
        baseline.get(
            "experience",
            [],
        ),
    )

    return enriched
