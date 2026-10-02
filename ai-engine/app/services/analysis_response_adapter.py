from app.analyzer import analyze_resume
from app.schemas.analysis import AnalyzeResponse
from app.schemas.resume import (
    Education,
    Experience,
    ResumeIntelligence,
)


def _format_education(
    education: Education,
) -> str | None:
    qualification_parts = [
        education.degree,
        education.field_of_study,
    ]

    qualification = " ".join(part for part in qualification_parts if part).strip()

    if qualification and education.institution:
        return f"{qualification} at {education.institution}"

    if qualification:
        return qualification

    return education.institution


def _format_experience(
    experience: Experience,
) -> str | None:
    if experience.job_title and experience.company:
        return f"{experience.job_title} at {experience.company}"

    return experience.job_title or experience.company


def build_analysis_response(
    resume_text: str,
    intelligence: ResumeIntelligence,
) -> AnalyzeResponse:
    """
    Convert CareerIQ's rich internal intelligence
    model into the existing public API contract.

    Deterministic analysis remains the source of
    the legacy ATS score and acts as a compatibility
    fallback for missing structured fields.
    """

    baseline = analyze_resume(resume_text)

    skills = [skill.name for skill in intelligence.skills if skill.name.strip()]

    education = [
        formatted
        for item in intelligence.education
        if (formatted := _format_education(item))
    ]

    experience = [
        formatted
        for item in intelligence.experience
        if (formatted := _format_experience(item))
    ]

    return AnalyzeResponse(
        ats_score=baseline["ats_score"],
        extracted_name=(intelligence.candidate.name or baseline["extracted_name"]),
        extracted_email=(intelligence.candidate.email or baseline["extracted_email"]),
        skills=(skills or baseline["skills"]),
        education=(education or baseline["education"]),
        experience=(experience or baseline["experience"]),
        summary=(intelligence.professional_summary or baseline["summary"]),
        status="completed",
    )
