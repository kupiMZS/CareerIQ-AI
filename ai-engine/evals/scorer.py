from collections.abc import Hashable, Iterable

from pydantic import BaseModel, Field

from app.schemas.resume import (
    Education,
    Experience,
    ResumeIntelligence,
)
from evals.schemas import (
    ExpectedEducation,
    ExpectedExperience,
    ExpectedResumeExtraction,
)


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


def _normalize_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = " ".join(value.split()).casefold()

    return normalized or None


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
) -> tuple[str | None, str | None]:
    return (
        _normalize_text(item.degree),
        _normalize_text(item.institution),
    )


def _actual_education_signature(
    item: Education,
) -> tuple[str | None, str | None]:
    return (
        _normalize_text(item.degree),
        _normalize_text(item.institution),
    )


def _expected_experience_signature(
    item: ExpectedExperience,
) -> tuple[str | None, str | None]:
    return (
        _normalize_text(item.job_title),
        _normalize_text(item.company),
    )


def _actual_experience_signature(
    item: Experience,
) -> tuple[str | None, str | None]:
    return (
        _normalize_text(item.job_title),
        _normalize_text(item.company),
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
