from collections.abc import Hashable, Iterable

from pydantic import BaseModel, Field

from app.schemas.career import CareerRecommendationResponse
from app.schemas.resume import (
    Certification,
    Education,
    Experience,
    Language,
    Project,
    Publication,
    ResumeIntelligence,
)
from evals.schemas import (
    ExpectedCareerRecommendation,
    ExpectedCertification,
    ExpectedEducation,
    ExpectedExperience,
    ExpectedExtendedEducation,
    ExpectedExtendedExperience,
    ExpectedExtendedResumeExtraction,
    ExpectedLanguage,
    ExpectedPhase2ResumeExtraction,
    ExpectedProject,
    ExpectedPublication,
    ExpectedResumeExtraction,
)

CAREER_SCORER_VERSION = "career-v1"
EXTENDED_SCORER_VERSION = "extended-v2"
PHASE2_SCORER_VERSION = "phase2-v1"
PHASE2_V2_SCORER_VERSION = "phase2-v2"


class ScalarMetric(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
    )


class CollectionMetric(BaseModel):
    precision: float = Field(
        ge=0.0,
        le=1.0,
    )

    recall: float = Field(
        ge=0.0,
        le=1.0,
    )

    f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    matched_count: int = Field(
        ge=0,
    )

    expected_count: int = Field(
        ge=0,
    )

    actual_count: int = Field(
        ge=0,
    )


class ResumeExtractionScore(BaseModel):
    name: ScalarMetric
    email: ScalarMetric

    skills: CollectionMetric
    education: CollectionMetric
    experience: CollectionMetric

    overall: float = Field(
        ge=0.0,
        le=1.0,
    )


class ExtendedResumeExtractionScore(BaseModel):
    headline: ScalarMetric

    education_field_of_study: CollectionMetric
    education_dates: CollectionMetric
    experience_dates: CollectionMetric
    responsibilities: CollectionMetric
    projects: CollectionMetric
    certifications: CollectionMetric

    overall: float = Field(
        ge=0.0,
        le=1.0,
    )


class Phase2ResumeExtractionScore(BaseModel):
    publications: CollectionMetric | None = None
    languages: CollectionMetric | None = None

    overall: float = Field(
        ge=0.0,
        le=1.0,
    )


class CareerRecommendationScore(BaseModel):
    status: ScalarMetric
    top_career: ScalarMetric

    relevant_careers: CollectionMetric
    missing_skills: CollectionMetric
    roadmap_skills: CollectionMetric

    entry_level: ScalarMetric
    missing_information: CollectionMetric

    overall: float = Field(
        ge=0.0,
        le=1.0,
    )


def _normalize_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = " ".join(value.split()).casefold()

    return normalized or None


def _normalize_date(
    value: str | None,
) -> str | None:
    """
    Normalize dates conservatively.

    Extended scoring intentionally does not reinterpret
    date formats yet. For example, "Jan 2022" and
    "January 2022" remain different values.

    We only normalize whitespace and case so historical
    evaluation semantics remain explicit and predictable.
    """

    return _normalize_text(value)


def _normalize_text_collection(
    values: Iterable[str],
) -> tuple[str, ...]:
    normalized = {
        item for value in values if (item := _normalize_text(value)) is not None
    }

    return tuple(sorted(normalized))


def _score_scalar(
    expected: str | None,
    actual: str | None,
) -> ScalarMetric:
    return ScalarMetric(
        score=float(_normalize_text(expected) == _normalize_text(actual))
    )


def _score_collection(
    expected: Iterable[Hashable],
    actual: Iterable[Hashable],
) -> CollectionMetric:
    expected_set = set(expected)

    actual_set = set(actual)

    matched_count = len(expected_set & actual_set)

    expected_count = len(expected_set)

    actual_count = len(actual_set)

    if expected_count == 0 and actual_count == 0:
        return CollectionMetric(
            precision=1.0,
            recall=1.0,
            f1=1.0,
            matched_count=0,
            expected_count=0,
            actual_count=0,
        )

    precision = matched_count / actual_count if actual_count else 0.0

    recall = matched_count / expected_count if expected_count else 1.0

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return CollectionMetric(
        precision=precision,
        recall=recall,
        f1=f1,
        matched_count=matched_count,
        expected_count=expected_count,
        actual_count=actual_count,
    )


def _expected_education_signature(
    item: ExpectedEducation,
) -> tuple[
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.degree),
        _normalize_text(item.institution),
    )


def _actual_education_signature(
    item: Education,
) -> tuple[
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.degree),
        _normalize_text(item.institution),
    )


def _expected_experience_signature(
    item: ExpectedExperience,
) -> tuple[
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.job_title),
        _normalize_text(item.company),
    )


def _actual_experience_signature(
    item: Experience,
) -> tuple[
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.job_title),
        _normalize_text(item.company),
    )


def _expected_education_field_signature(
    item: ExpectedExtendedEducation,
) -> tuple[
    str | None,
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.degree),
        _normalize_text(item.institution),
        _normalize_text(item.field_of_study),
    )


def _actual_education_field_signature(
    item: Education,
) -> tuple[
    str | None,
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.degree),
        _normalize_text(item.institution),
        _normalize_text(item.field_of_study),
    )


def _expected_education_date_signature(
    item: ExpectedExtendedEducation,
) -> tuple[
    str | None,
    str | None,
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.degree),
        _normalize_text(item.institution),
        _normalize_date(item.start_date),
        _normalize_date(item.end_date),
    )


def _actual_education_date_signature(
    item: Education,
) -> tuple[
    str | None,
    str | None,
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.degree),
        _normalize_text(item.institution),
        _normalize_date(item.start_date),
        _normalize_date(item.end_date),
    )


def _expected_experience_date_signature(
    item: ExpectedExtendedExperience,
) -> tuple[
    str | None,
    str | None,
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.job_title),
        _normalize_text(item.company),
        _normalize_date(item.start_date),
        _normalize_date(item.end_date),
    )


def _actual_experience_date_signature(
    item: Experience,
) -> tuple[
    str | None,
    str | None,
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.job_title),
        _normalize_text(item.company),
        _normalize_date(item.start_date),
        _normalize_date(item.end_date),
    )


def _has_experience_date(
    start_date: str | None,
    end_date: str | None,
) -> bool:
    return (
        _normalize_date(start_date) is not None or _normalize_date(end_date) is not None
    )


def _expected_responsibility_signatures(
    items: Iterable[ExpectedExtendedExperience],
) -> list[
    tuple[
        str | None,
        str | None,
        str | None,
    ]
]:
    signatures = []

    for item in items:
        for responsibility in item.responsibilities:
            signatures.append(
                (
                    _normalize_text(item.job_title),
                    _normalize_text(item.company),
                    _normalize_text(responsibility),
                )
            )

    return signatures


def _actual_responsibility_signatures(
    items: Iterable[Experience],
) -> list[
    tuple[
        str | None,
        str | None,
        str | None,
    ]
]:
    signatures = []

    for item in items:
        for responsibility in item.responsibilities:
            signatures.append(
                (
                    _normalize_text(item.job_title),
                    _normalize_text(item.company),
                    _normalize_text(responsibility),
                )
            )

    return signatures


def _expected_project_signature(
    item: ExpectedProject,
) -> tuple[
    str | None,
    str | None,
    tuple[str, ...],
]:
    return (
        _normalize_text(item.name),
        _normalize_text(item.description),
        _normalize_text_collection(item.technologies),
    )


def _actual_project_signature(
    item: Project,
) -> tuple[
    str | None,
    str | None,
    tuple[str, ...],
]:
    return (
        _normalize_text(item.name),
        _normalize_text(item.description),
        _normalize_text_collection(item.technologies),
    )


def _expected_certification_signature(
    item: ExpectedCertification,
) -> tuple[
    str | None,
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.name),
        _normalize_text(item.issuer),
        _normalize_date(item.date),
    )


def _actual_certification_signature(
    item: Certification,
) -> tuple[
    str | None,
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.name),
        _normalize_text(item.issuer),
        _normalize_date(item.date),
    )


def _normalize_ordered_text_collection(
    values: Iterable[str],
) -> tuple[str, ...]:
    return tuple(
        item for value in values if (item := _normalize_text(value)) is not None
    )


def _expected_publication_signature(
    item: ExpectedPublication,
) -> tuple[
    str | None,
    tuple[str, ...],
    str | None,
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.title),
        _normalize_ordered_text_collection(item.authors),
        _normalize_text(item.venue),
        _normalize_date(item.date),
        _normalize_text(item.url),
    )


def _actual_publication_signature(
    item: Publication,
) -> tuple[
    str | None,
    tuple[str, ...],
    str | None,
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.title),
        _normalize_ordered_text_collection(item.authors),
        _normalize_text(item.venue),
        _normalize_date(item.date),
        _normalize_text(item.url),
    )


def _expected_language_signature(
    item: ExpectedLanguage,
) -> tuple[
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.name),
        _normalize_text(item.proficiency),
    )


def _actual_language_signature(
    item: Language,
) -> tuple[
    str | None,
    str | None,
]:
    return (
        _normalize_text(item.name),
        _normalize_text(item.proficiency),
    )


def score_resume_extraction(
    expected: ExpectedResumeExtraction,
    actual: ResumeIntelligence,
) -> ResumeExtractionScore:
    name = _score_scalar(
        expected.name,
        actual.candidate.name,
    )

    email = _score_scalar(
        expected.email,
        actual.candidate.email,
    )

    skills = _score_collection(
        (_normalize_text(skill) for skill in expected.skills),
        (_normalize_text(skill.name) for skill in actual.skills),
    )

    education = _score_collection(
        (_expected_education_signature(item) for item in expected.education),
        (_actual_education_signature(item) for item in actual.education),
    )

    experience = _score_collection(
        (_expected_experience_signature(item) for item in expected.experience),
        (_actual_experience_signature(item) for item in actual.experience),
    )

    overall = (name.score + email.score + skills.f1 + education.f1 + experience.f1) / 5

    return ResumeExtractionScore(
        name=name,
        email=email,
        skills=skills,
        education=education,
        experience=experience,
        overall=overall,
    )


def score_extended_resume_extraction(
    expected: ExpectedExtendedResumeExtraction,
    actual: ResumeIntelligence,
) -> ExtendedResumeExtractionScore:
    headline = _score_scalar(
        expected.headline,
        actual.candidate.headline,
    )

    education_field_of_study = _score_collection(
        (_expected_education_field_signature(item) for item in expected.education),
        (_actual_education_field_signature(item) for item in actual.education),
    )

    education_dates = _score_collection(
        (_expected_education_date_signature(item) for item in expected.education),
        (_actual_education_date_signature(item) for item in actual.education),
    )

    experience_dates = _score_collection(
        (
            _expected_experience_date_signature(item)
            for item in expected.experience
            if _has_experience_date(
                item.start_date,
                item.end_date,
            )
        ),
        (
            _actual_experience_date_signature(item)
            for item in actual.experience
            if _has_experience_date(
                item.start_date,
                item.end_date,
            )
        ),
    )

    responsibilities = _score_collection(
        _expected_responsibility_signatures(expected.experience),
        _actual_responsibility_signatures(actual.experience),
    )

    projects = _score_collection(
        (_expected_project_signature(item) for item in expected.projects),
        (_actual_project_signature(item) for item in actual.projects),
    )

    certifications = _score_collection(
        (_expected_certification_signature(item) for item in expected.certifications),
        (_actual_certification_signature(item) for item in actual.certifications),
    )

    overall = (
        headline.score
        + education_field_of_study.f1
        + education_dates.f1
        + experience_dates.f1
        + responsibilities.f1
        + projects.f1
        + certifications.f1
    ) / 7

    return ExtendedResumeExtractionScore(
        headline=headline,
        education_field_of_study=(education_field_of_study),
        education_dates=education_dates,
        experience_dates=experience_dates,
        responsibilities=responsibilities,
        projects=projects,
        certifications=certifications,
        overall=overall,
    )


def score_phase2_resume_extraction(
    expected: ExpectedPhase2ResumeExtraction,
    actual: ResumeIntelligence,
) -> Phase2ResumeExtractionScore:
    publications = _score_collection(
        (
            _expected_publication_signature(item)
            for item in (expected.publications or [])
        ),
        (_actual_publication_signature(item) for item in actual.publications),
    )

    return Phase2ResumeExtractionScore(
        publications=publications,
        overall=publications.f1,
    )


def score_phase2_v2_resume_extraction(
    expected: ExpectedPhase2ResumeExtraction,
    actual: ResumeIntelligence,
) -> Phase2ResumeExtractionScore:
    publications = None
    languages = None

    covered_metrics: list[CollectionMetric] = []

    if expected.publications is not None:
        publications = _score_collection(
            (_expected_publication_signature(item) for item in expected.publications),
            (_actual_publication_signature(item) for item in actual.publications),
        )

        covered_metrics.append(publications)

    if expected.languages is not None:
        languages = _score_collection(
            (_expected_language_signature(item) for item in expected.languages),
            (_actual_language_signature(item) for item in actual.languages),
        )

        covered_metrics.append(languages)

    if not covered_metrics:
        raise ValueError("Phase 2 v2 scoring requires at least one covered field.")

    overall = sum(metric.f1 for metric in covered_metrics) / len(covered_metrics)

    return Phase2ResumeExtractionScore(
        publications=publications,
        languages=languages,
        overall=overall,
    )


def _score_optional_bool(
    expected: bool | None,
    actual: bool | None,
) -> ScalarMetric:
    if expected is None:
        return ScalarMetric(
            score=1.0,
        )

    return ScalarMetric(
        score=float(expected == actual),
    )


def score_career_recommendation(
    expected: ExpectedCareerRecommendation,
    actual: CareerRecommendationResponse,
) -> CareerRecommendationScore:
    actual_titles = [
        recommendation.career_title for recommendation in actual.recommendations
    ]

    actual_top_career = actual_titles[0] if actual_titles else None

    top_recommendation = actual.recommendations[0] if actual.recommendations else None

    actual_missing_skills = (
        top_recommendation.missing_skills if top_recommendation is not None else []
    )

    actual_entry_level = (
        top_recommendation.entry_level if top_recommendation is not None else None
    )

    actual_roadmap_skills = [skill for step in actual.roadmap for skill in step.skills]

    status = _score_scalar(
        expected.status,
        actual.status,
    )

    top_career = _score_scalar(
        expected.top_career,
        actual_top_career,
    )

    relevant_careers = _score_collection(
        _normalize_text_collection(expected.relevant_careers),
        _normalize_text_collection(actual_titles),
    )

    missing_skills = _score_collection(
        _normalize_text_collection(expected.missing_skills),
        _normalize_text_collection(actual_missing_skills),
    )

    roadmap_skills = _score_collection(
        _normalize_text_collection(expected.roadmap_skills),
        _normalize_text_collection(actual_roadmap_skills),
    )

    entry_level = _score_optional_bool(
        expected.entry_level,
        actual_entry_level,
    )

    missing_information = _score_collection(
        _normalize_text_collection(expected.missing_information),
        _normalize_text_collection(actual.missing_information),
    )

    component_scores = [
        status.score,
        top_career.score,
        relevant_careers.recall,
        missing_skills.f1,
        roadmap_skills.f1,
        entry_level.score,
        missing_information.f1,
    ]

    return CareerRecommendationScore(
        status=status,
        top_career=top_career,
        relevant_careers=relevant_careers,
        missing_skills=missing_skills,
        roadmap_skills=roadmap_skills,
        entry_level=entry_level,
        missing_information=missing_information,
        overall=(sum(component_scores) / len(component_scores)),
    )
