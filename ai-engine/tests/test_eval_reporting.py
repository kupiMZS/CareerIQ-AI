import pytest

from evals.reporting import (
    build_resume_benchmark_report,
)
from evals.runner import ResumeBenchmarkSummary


def build_summary(
    *,
    provider: str = "local_enriched",
    case_count: int = 5,
    name_accuracy: float = 1.0,
    email_accuracy: float = 1.0,
    skills_f1: float = 1.0,
    education_f1: float = 1.0,
    experience_f1: float = 1.0,
    overall_mean: float = 1.0,
) -> ResumeBenchmarkSummary:
    return ResumeBenchmarkSummary(
        provider=provider,
        case_count=case_count,
        name_accuracy=name_accuracy,
        email_accuracy=email_accuracy,
        skills_f1=skills_f1,
        education_f1=education_f1,
        experience_f1=experience_f1,
        overall_mean=overall_mean,
        cases=[],
    )


def test_report_preserves_benchmark_metadata():
    report = build_resume_benchmark_report(
        provider="local_enriched",
        model="qwen3:4b-instruct",
        prompt_version="resume-analysis-v2",
        dataset="resume_extraction_v1.jsonl",
        runs=[
            build_summary(),
        ],
    )

    assert report.provider == "local_enriched"
    assert report.model == "qwen3:4b-instruct"
    assert report.prompt_version == "resume-analysis-v2"
    assert report.dataset == "resume_extraction_v1.jsonl"
    assert report.run_count == 1
    assert report.case_count == 5


def test_report_single_run_has_zero_variance():
    report = build_resume_benchmark_report(
        provider="local_enriched",
        model="qwen3:4b-instruct",
        prompt_version="resume-analysis-v2",
        dataset="resume_extraction_v1.jsonl",
        runs=[
            build_summary(
                overall_mean=0.9866666667,
            ),
        ],
    )

    metric = report.metrics.overall_mean

    assert metric.mean == pytest.approx(0.9866666667)
    assert metric.minimum == pytest.approx(0.9866666667)
    assert metric.maximum == pytest.approx(0.9866666667)
    assert metric.standard_deviation == 0.0


def test_report_aggregates_multiple_runs():
    report = build_resume_benchmark_report(
        provider="local",
        model="qwen3:4b-instruct",
        prompt_version="resume-analysis-v2",
        dataset="resume_extraction_v1.jsonl",
        runs=[
            build_summary(
                provider="local",
                overall_mean=0.6,
            ),
            build_summary(
                provider="local",
                overall_mean=0.8,
            ),
        ],
    )

    metric = report.metrics.overall_mean

    assert report.run_count == 2
    assert metric.mean == pytest.approx(0.7)
    assert metric.minimum == 0.6
    assert metric.maximum == 0.8
    assert metric.standard_deviation == pytest.approx(0.1)


def test_report_rejects_empty_runs():
    with pytest.raises(
        ValueError,
        match="at least one run",
    ):
        build_resume_benchmark_report(
            provider="local",
            model="qwen3:4b-instruct",
            prompt_version="resume-analysis-v2",
            dataset="resume_extraction_v1.jsonl",
            runs=[],
        )


def test_report_rejects_mixed_providers():
    with pytest.raises(
        ValueError,
        match="same provider",
    ):
        build_resume_benchmark_report(
            provider="local",
            model="qwen3:4b-instruct",
            prompt_version="resume-analysis-v2",
            dataset="resume_extraction_v1.jsonl",
            runs=[
                build_summary(provider="local"),
                build_summary(provider="rule_based"),
            ],
        )


def test_report_rejects_mixed_case_counts():
    with pytest.raises(
        ValueError,
        match="same case count",
    ):
        build_resume_benchmark_report(
            provider="local",
            model="qwen3:4b-instruct",
            prompt_version="resume-analysis-v2",
            dataset="resume_extraction_v1.jsonl",
            runs=[
                build_summary(
                    provider="local",
                    case_count=5,
                ),
                build_summary(
                    provider="local",
                    case_count=6,
                ),
            ],
        )
