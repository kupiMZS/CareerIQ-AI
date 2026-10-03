from pydantic import BaseModel, Field

from app.providers.base import ResumeAnalysisProvider
from evals.schemas import ResumeEvalCase
from evals.scorer import (
    ResumeExtractionScore,
    score_resume_extraction,
)


class ResumeBenchmarkCaseResult(BaseModel):
    case_id: str
    score: ResumeExtractionScore


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

        results.append(
            ResumeBenchmarkCaseResult(
                case_id=case.case_id,
                score=score,
            )
        )

    case_count = len(results)

    name_accuracy = sum(result.score.name.score for result in results) / case_count

    email_accuracy = sum(result.score.email.score for result in results) / case_count

    skills_f1 = sum(result.score.skills.f1 for result in results) / case_count

    education_f1 = sum(result.score.education.f1 for result in results) / case_count

    experience_f1 = sum(result.score.experience.f1 for result in results) / case_count

    overall_mean = sum(result.score.overall for result in results) / case_count

    return ResumeBenchmarkSummary(
        provider=provider_name,
        case_count=case_count,
        name_accuracy=name_accuracy,
        email_accuracy=email_accuracy,
        skills_f1=skills_f1,
        education_f1=education_f1,
        experience_f1=experience_f1,
        overall_mean=overall_mean,
        cases=results,
    )
