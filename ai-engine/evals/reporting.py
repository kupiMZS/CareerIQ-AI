from statistics import fmean, pstdev

from pydantic import BaseModel, Field

from evals.runner import ResumeBenchmarkSummary


class MetricStatistics(BaseModel):
    mean: float = Field(
        ge=0.0,
        le=1.0,
    )
    minimum: float = Field(
        ge=0.0,
        le=1.0,
    )
    maximum: float = Field(
        ge=0.0,
        le=1.0,
    )
    standard_deviation: float = Field(
        ge=0.0,
        le=1.0,
    )


class BenchmarkMetrics(BaseModel):
    name_accuracy: MetricStatistics
    email_accuracy: MetricStatistics
    skills_f1: MetricStatistics
    education_f1: MetricStatistics
    experience_f1: MetricStatistics
    overall_mean: MetricStatistics


class ResumeBenchmarkReport(BaseModel):
    provider: str
    model: str | None = None
    prompt_version: str | None = None
    dataset: str

    run_count: int = Field(
        ge=1,
    )
    case_count: int = Field(
        ge=1,
    )

    metrics: BenchmarkMetrics
    runs: list[ResumeBenchmarkSummary]


def _build_metric_statistics(
    values: list[float],
) -> MetricStatistics:
    return MetricStatistics(
        mean=fmean(values),
        minimum=min(values),
        maximum=max(values),
        standard_deviation=pstdev(values),
    )


def build_resume_benchmark_report(
    *,
    provider: str,
    model: str | None,
    prompt_version: str | None,
    dataset: str,
    runs: list[ResumeBenchmarkSummary],
) -> ResumeBenchmarkReport:
    if not runs:
        raise ValueError("Benchmark report requires at least one run.")

    if any(run.provider != provider for run in runs):
        raise ValueError("All benchmark runs must use the same provider.")

    case_count = runs[0].case_count

    if any(run.case_count != case_count for run in runs):
        raise ValueError("All benchmark runs must use the same case count.")

    metrics = BenchmarkMetrics(
        name_accuracy=_build_metric_statistics([run.name_accuracy for run in runs]),
        email_accuracy=_build_metric_statistics([run.email_accuracy for run in runs]),
        skills_f1=_build_metric_statistics([run.skills_f1 for run in runs]),
        education_f1=_build_metric_statistics([run.education_f1 for run in runs]),
        experience_f1=_build_metric_statistics([run.experience_f1 for run in runs]),
        overall_mean=_build_metric_statistics([run.overall_mean for run in runs]),
    )

    return ResumeBenchmarkReport(
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        dataset=dataset,
        run_count=len(runs),
        case_count=case_count,
        metrics=metrics,
        runs=runs,
    )
