import pytest

from evals.reporting import (
    build_career_benchmark_report,
)
from evals.runner import CareerBenchmarkSummary


def build_summary(
    *,
    engine: str = "deterministic",
    case_count: int = 10,
    status_accuracy: float = 1.0,
    top_career_accuracy: float = 1.0,
    relevant_career_coverage: float = 1.0,
    missing_skills_f1: float = 1.0,
    roadmap_skills_f1: float = 1.0,
    entry_level_accuracy: float = 1.0,
    missing_information_f1: float = 1.0,
    overall_mean: float = 1.0,
) -> CareerBenchmarkSummary:
    return CareerBenchmarkSummary(
        engine=engine,
        case_count=case_count,
        status_accuracy=status_accuracy,
        top_career_accuracy=top_career_accuracy,
        relevant_career_coverage=(relevant_career_coverage),
        missing_skills_f1=missing_skills_f1,
        roadmap_skills_f1=roadmap_skills_f1,
        entry_level_accuracy=entry_level_accuracy,
        missing_information_f1=(missing_information_f1),
        overall_mean=overall_mean,
        cases=[],
    )


def test_career_report_preserves_metadata():
    report = build_career_benchmark_report(
        engine="deterministic",
        dataset="career_recommendation_v1.jsonl",
        runs=[
            build_summary(),
        ],
    )

    assert report.engine == "deterministic"
    assert report.scorer_version == "career-v1"
    assert report.dataset == "career_recommendation_v1.jsonl"
    assert report.run_count == 1
    assert report.case_count == 10


def test_career_report_single_run_has_zero_variance():
    report = build_career_benchmark_report(
        engine="deterministic",
        dataset="career_recommendation_v1.jsonl",
        runs=[
            build_summary(
                overall_mean=0.95,
            ),
        ],
    )

    metric = report.metrics.overall_mean

    assert metric.mean == pytest.approx(0.95)
    assert metric.minimum == pytest.approx(0.95)
    assert metric.maximum == pytest.approx(0.95)
    assert metric.standard_deviation == 0.0


def test_career_report_aggregates_multiple_runs():
    report = build_career_benchmark_report(
        engine="deterministic",
        dataset="career_recommendation_v1.jsonl",
        runs=[
            build_summary(
                overall_mean=0.6,
                missing_skills_f1=0.7,
            ),
            build_summary(
                overall_mean=0.8,
                missing_skills_f1=0.9,
            ),
        ],
    )

    overall = report.metrics.overall_mean
    missing_skills = report.metrics.missing_skills_f1

    assert report.run_count == 2

    assert overall.mean == pytest.approx(0.7)
    assert overall.minimum == 0.6
    assert overall.maximum == 0.8
    assert overall.standard_deviation == pytest.approx(0.1)

    assert missing_skills.mean == pytest.approx(0.8)
    assert missing_skills.standard_deviation == pytest.approx(0.1)


def test_career_report_rejects_empty_runs():
    with pytest.raises(
        ValueError,
        match="at least one run",
    ):
        build_career_benchmark_report(
            engine="deterministic",
            dataset="career_recommendation_v1.jsonl",
            runs=[],
        )


def test_career_report_rejects_mixed_engines():
    with pytest.raises(
        ValueError,
        match="same engine",
    ):
        build_career_benchmark_report(
            engine="deterministic",
            dataset="career_recommendation_v1.jsonl",
            runs=[
                build_summary(
                    engine="deterministic",
                ),
                build_summary(
                    engine="experimental",
                ),
            ],
        )


def test_career_report_rejects_mixed_case_counts():
    with pytest.raises(
        ValueError,
        match="same case count",
    ):
        build_career_benchmark_report(
            engine="deterministic",
            dataset="career_recommendation_v1.jsonl",
            runs=[
                build_summary(
                    case_count=10,
                ),
                build_summary(
                    case_count=9,
                ),
            ],
        )
