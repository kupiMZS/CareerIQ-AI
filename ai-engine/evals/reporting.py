from statistics import fmean, pstdev

from pydantic import BaseModel, Field

from evals.runner import (
    CareerBenchmarkSummary,
    ExtendedBenchmarkSummary,
    ResumeBenchmarkSummary,
)
from evals.scorer import (
    CAREER_SCORER_VERSION,
    EXTENDED_SCORER_VERSION,
)


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


class CareerBenchmarkMetrics(BaseModel):
    status_accuracy: MetricStatistics
    top_career_accuracy: MetricStatistics
    relevant_career_coverage: MetricStatistics
    missing_skills_f1: MetricStatistics
    roadmap_skills_f1: MetricStatistics
    entry_level_accuracy: MetricStatistics
    missing_information_f1: MetricStatistics
    overall_mean: MetricStatistics


class CareerBenchmarkReport(BaseModel):
    engine: str
    scorer_version: str
    dataset: str

    run_count: int = Field(
        ge=1,
    )

    case_count: int = Field(
        ge=1,
    )

    metrics: CareerBenchmarkMetrics
    runs: list[CareerBenchmarkSummary]


class BenchmarkMetrics(BaseModel):
    name_accuracy: MetricStatistics
    email_accuracy: MetricStatistics
    skills_f1: MetricStatistics
    education_f1: MetricStatistics
    experience_f1: MetricStatistics
    overall_mean: MetricStatistics


class ExtendedBenchmarkMetrics(BaseModel):
    headline_accuracy: MetricStatistics

    education_field_of_study_f1: MetricStatistics

    education_dates_f1: MetricStatistics
    experience_dates_f1: MetricStatistics
    responsibilities_f1: MetricStatistics
    projects_f1: MetricStatistics
    certifications_f1: MetricStatistics
    overall_mean: MetricStatistics


class ExtendedBenchmarkReport(BaseModel):
    scorer_version: str

    case_count: int = Field(
        ge=1,
    )

    metrics: ExtendedBenchmarkMetrics


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

    extended: ExtendedBenchmarkReport | None = None

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


def _build_extended_report(
    runs: list[ExtendedBenchmarkSummary],
) -> ExtendedBenchmarkReport:
    case_count = runs[0].case_count

    if any(run.case_count != case_count for run in runs):
        raise ValueError("All benchmark runs must use the same extended case count.")

    metrics = ExtendedBenchmarkMetrics(
        headline_accuracy=(
            _build_metric_statistics([run.headline_accuracy for run in runs])
        ),
        education_field_of_study_f1=(
            _build_metric_statistics([run.education_field_of_study_f1 for run in runs])
        ),
        education_dates_f1=(
            _build_metric_statistics([run.education_dates_f1 for run in runs])
        ),
        experience_dates_f1=(
            _build_metric_statistics([run.experience_dates_f1 for run in runs])
        ),
        responsibilities_f1=(
            _build_metric_statistics([run.responsibilities_f1 for run in runs])
        ),
        projects_f1=(_build_metric_statistics([run.projects_f1 for run in runs])),
        certifications_f1=(
            _build_metric_statistics([run.certifications_f1 for run in runs])
        ),
        overall_mean=(_build_metric_statistics([run.overall_mean for run in runs])),
    )

    return ExtendedBenchmarkReport(
        scorer_version=EXTENDED_SCORER_VERSION,
        case_count=case_count,
        metrics=metrics,
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
        name_accuracy=(_build_metric_statistics([run.name_accuracy for run in runs])),
        email_accuracy=(_build_metric_statistics([run.email_accuracy for run in runs])),
        skills_f1=(_build_metric_statistics([run.skills_f1 for run in runs])),
        education_f1=(_build_metric_statistics([run.education_f1 for run in runs])),
        experience_f1=(_build_metric_statistics([run.experience_f1 for run in runs])),
        overall_mean=(_build_metric_statistics([run.overall_mean for run in runs])),
    )

    extended_values = [run.extended for run in runs]

    has_extended = [value is not None for value in extended_values]

    if any(has_extended) and not all(has_extended):
        raise ValueError(
            "All benchmark runs must use the same extended evaluation coverage."
        )

    extended_report = None

    if all(has_extended):
        extended_runs = [value for value in extended_values if value is not None]

        extended_report = _build_extended_report(extended_runs)

    return ResumeBenchmarkReport(
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        dataset=dataset,
        run_count=len(runs),
        case_count=case_count,
        metrics=metrics,
        extended=extended_report,
        runs=runs,
    )


def build_career_benchmark_report(
    *,
    engine: str,
    dataset: str,
    runs: list[CareerBenchmarkSummary],
) -> CareerBenchmarkReport:
    if not runs:
        raise ValueError("Benchmark report requires at least one run.")

    if any(run.engine != engine for run in runs):
        raise ValueError("All benchmark runs must use the same engine.")

    case_count = runs[0].case_count

    if any(run.case_count != case_count for run in runs):
        raise ValueError("All benchmark runs must use the same case count.")

    metrics = CareerBenchmarkMetrics(
        status_accuracy=_build_metric_statistics([run.status_accuracy for run in runs]),
        top_career_accuracy=_build_metric_statistics(
            [run.top_career_accuracy for run in runs]
        ),
        relevant_career_coverage=_build_metric_statistics(
            [run.relevant_career_coverage for run in runs]
        ),
        missing_skills_f1=_build_metric_statistics(
            [run.missing_skills_f1 for run in runs]
        ),
        roadmap_skills_f1=_build_metric_statistics(
            [run.roadmap_skills_f1 for run in runs]
        ),
        entry_level_accuracy=_build_metric_statistics(
            [run.entry_level_accuracy for run in runs]
        ),
        missing_information_f1=_build_metric_statistics(
            [run.missing_information_f1 for run in runs]
        ),
        overall_mean=_build_metric_statistics([run.overall_mean for run in runs]),
    )

    return CareerBenchmarkReport(
        engine=engine,
        scorer_version=CAREER_SCORER_VERSION,
        dataset=dataset,
        run_count=len(runs),
        case_count=case_count,
        metrics=metrics,
        runs=runs,
    )
