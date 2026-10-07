from pydantic import BaseModel, Field

from app.providers.base import ResumeAnalysisProvider
from app.services.career_recommendation_engine import CareerRecommendationEngine
from evals.schemas import CareerEvalCase, ResumeEvalCase
from evals.scorer import (
    CareerRecommendationScore,
    ExtendedResumeExtractionScore,
    ResumeExtractionScore,
    score_career_recommendation,
    score_extended_resume_extraction,
    score_resume_extraction,
)


class ResumeBenchmarkCaseResult(BaseModel):
    case_id: str
    score: ResumeExtractionScore

    extended_score: ExtendedResumeExtractionScore | None = None


class ExtendedBenchmarkSummary(BaseModel):
    case_count: int = Field(
        ge=1,
    )

    headline_accuracy: float = Field(
        ge=0.0,
        le=1.0,
    )

    education_field_of_study_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    education_dates_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    experience_dates_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    responsibilities_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    projects_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    certifications_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    overall_mean: float = Field(
        ge=0.0,
        le=1.0,
    )


class ResumeBenchmarkSummary(BaseModel):
    provider: str

    case_count: int = Field(
        ge=1,
    )

    name_accuracy: float = Field(
        ge=0.0,
        le=1.0,
    )

    email_accuracy: float = Field(
        ge=0.0,
        le=1.0,
    )

    skills_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    education_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    experience_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    overall_mean: float = Field(
        ge=0.0,
        le=1.0,
    )

    extended: ExtendedBenchmarkSummary | None = None

    cases: list[ResumeBenchmarkCaseResult]


async def run_resume_benchmark(
    provider_name: str,
    provider: ResumeAnalysisProvider,
    cases: list[ResumeEvalCase],
) -> ResumeBenchmarkSummary:
    if not cases:
        raise ValueError("Benchmark requires at least one evaluation case.")

    results: list[ResumeBenchmarkCaseResult] = []

    for case in cases:
        actual = await provider.analyze_resume(case.resume_text)

        score = score_resume_extraction(
            case.expected,
            actual,
        )

        extended_score = None

        if case.extended_expected is not None:
            extended_score = score_extended_resume_extraction(
                case.extended_expected,
                actual,
            )

        results.append(
            ResumeBenchmarkCaseResult(
                case_id=case.case_id,
                score=score,
                extended_score=extended_score,
            )
        )

    case_count = len(results)

    name_accuracy = sum(result.score.name.score for result in results) / case_count

    email_accuracy = sum(result.score.email.score for result in results) / case_count

    skills_f1 = sum(result.score.skills.f1 for result in results) / case_count

    education_f1 = sum(result.score.education.f1 for result in results) / case_count

    experience_f1 = sum(result.score.experience.f1 for result in results) / case_count

    overall_mean = sum(result.score.overall for result in results) / case_count

    extended_scores = [
        result.extended_score for result in results if result.extended_score is not None
    ]

    extended_summary = None

    if extended_scores:
        extended_case_count = len(extended_scores)

        extended_summary = ExtendedBenchmarkSummary(
            case_count=(extended_case_count),
            headline_accuracy=(
                sum(score.headline.score for score in (extended_scores))
                / extended_case_count
            ),
            education_field_of_study_f1=(
                sum(score.education_field_of_study.f1 for score in (extended_scores))
                / extended_case_count
            ),
            education_dates_f1=(
                sum(score.education_dates.f1 for score in (extended_scores))
                / extended_case_count
            ),
            experience_dates_f1=(
                sum(score.experience_dates.f1 for score in (extended_scores))
                / extended_case_count
            ),
            responsibilities_f1=(
                sum(score.responsibilities.f1 for score in (extended_scores))
                / extended_case_count
            ),
            projects_f1=(
                sum(score.projects.f1 for score in (extended_scores))
                / extended_case_count
            ),
            certifications_f1=(
                sum(score.certifications.f1 for score in (extended_scores))
                / extended_case_count
            ),
            overall_mean=(
                sum(score.overall for score in (extended_scores)) / extended_case_count
            ),
        )

    return ResumeBenchmarkSummary(
        provider=provider_name,
        case_count=case_count,
        name_accuracy=name_accuracy,
        email_accuracy=email_accuracy,
        skills_f1=skills_f1,
        education_f1=education_f1,
        experience_f1=experience_f1,
        overall_mean=overall_mean,
        extended=extended_summary,
        cases=results,
    )


class CareerBenchmarkCaseResult(BaseModel):
    case_id: str
    score: CareerRecommendationScore


class CareerBenchmarkSummary(BaseModel):
    engine: str

    case_count: int = Field(
        ge=1,
    )

    status_accuracy: float = Field(
        ge=0.0,
        le=1.0,
    )

    top_career_accuracy: float = Field(
        ge=0.0,
        le=1.0,
    )

    relevant_career_coverage: float = Field(
        ge=0.0,
        le=1.0,
    )

    missing_skills_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    roadmap_skills_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    entry_level_accuracy: float = Field(
        ge=0.0,
        le=1.0,
    )

    missing_information_f1: float = Field(
        ge=0.0,
        le=1.0,
    )

    overall_mean: float = Field(
        ge=0.0,
        le=1.0,
    )

    cases: list[CareerBenchmarkCaseResult]


async def run_career_benchmark(
    engine_name: str,
    engine: CareerRecommendationEngine,
    cases: list[CareerEvalCase],
) -> CareerBenchmarkSummary:
    if not cases:
        raise ValueError("Benchmark requires at least one evaluation case.")

    results: list[CareerBenchmarkCaseResult] = []

    for case in cases:
        actual = engine.recommend(case.request)

        score = score_career_recommendation(
            case.expected,
            actual,
        )

        results.append(
            CareerBenchmarkCaseResult(
                case_id=case.case_id,
                score=score,
            )
        )

    case_count = len(results)

    status_accuracy = sum(result.score.status.score for result in results) / case_count

    top_career_accuracy = (
        sum(result.score.top_career.score for result in results) / case_count
    )

    relevant_career_coverage = (
        sum(result.score.relevant_careers.recall for result in results) / case_count
    )

    missing_skills_f1 = (
        sum(result.score.missing_skills.f1 for result in results) / case_count
    )

    roadmap_skills_f1 = (
        sum(result.score.roadmap_skills.f1 for result in results) / case_count
    )

    entry_level_accuracy = (
        sum(result.score.entry_level.score for result in results) / case_count
    )

    missing_information_f1 = (
        sum(result.score.missing_information.f1 for result in results) / case_count
    )

    overall_mean = sum(result.score.overall for result in results) / case_count

    return CareerBenchmarkSummary(
        engine=engine_name,
        case_count=case_count,
        status_accuracy=status_accuracy,
        top_career_accuracy=top_career_accuracy,
        relevant_career_coverage=(relevant_career_coverage),
        missing_skills_f1=missing_skills_f1,
        roadmap_skills_f1=roadmap_skills_f1,
        entry_level_accuracy=(entry_level_accuracy),
        missing_information_f1=(missing_information_f1),
        overall_mean=overall_mean,
        cases=results,
    )
