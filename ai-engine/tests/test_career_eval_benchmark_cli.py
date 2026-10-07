import argparse
import json
import sys
from pathlib import Path

import pytest

from evals.reporting import (
    build_career_benchmark_report,
)
from evals.run_career_benchmark import (
    DEFAULT_DATASET_PATH,
    build_benchmark_engine,
    parse_args,
    positive_int,
    run,
    write_benchmark_report,
)
from evals.runner import CareerBenchmarkSummary


def build_summary() -> CareerBenchmarkSummary:
    return CareerBenchmarkSummary(
        engine="deterministic",
        case_count=10,
        status_accuracy=1.0,
        top_career_accuracy=1.0,
        relevant_career_coverage=1.0,
        missing_skills_f1=1.0,
        roadmap_skills_f1=1.0,
        entry_level_accuracy=1.0,
        missing_information_f1=1.0,
        overall_mean=1.0,
        cases=[],
    )


def test_positive_int_accepts_positive_value():
    assert positive_int("3") == 3


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-1",
    ],
)
def test_positive_int_rejects_non_positive_value(
    value: str,
):
    with pytest.raises(
        argparse.ArgumentTypeError,
        match="at least 1",
    ):
        positive_int(value)


def test_parse_args_uses_career_defaults(
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_career_benchmark",
        ],
    )

    args = parse_args()

    assert args.engine == "deterministic"
    assert args.dataset == DEFAULT_DATASET_PATH
    assert args.runs == 1
    assert args.output is None


def test_parse_args_accepts_runs_dataset_and_output(
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_career_benchmark",
            "--engine",
            "deterministic",
            "--dataset",
            "evals/datasets/custom.jsonl",
            "--runs",
            "3",
            "--output",
            "reports/career.json",
        ],
    )

    args = parse_args()

    assert args.engine == "deterministic"
    assert args.dataset == Path("evals/datasets/custom.jsonl")
    assert args.runs == 3
    assert args.output == Path("reports/career.json")


def test_build_benchmark_engine_returns_engine():
    engine = build_benchmark_engine("deterministic")

    assert engine.__class__.__name__ == "CareerRecommendationEngine"


def test_write_benchmark_report_creates_json_file(
    tmp_path: Path,
):
    report = build_career_benchmark_report(
        engine="deterministic",
        dataset="career_recommendation_v1.jsonl",
        runs=[
            build_summary(),
        ],
    )

    output_path = tmp_path / "nested" / "career-report.json"

    write_benchmark_report(
        report,
        output_path,
    )

    assert output_path.exists()

    content = output_path.read_text(encoding="utf-8")

    assert '"engine": "deterministic"' in content
    assert '"scorer_version": "career-v1"' in content
    assert '"run_count": 1' in content
    assert content.endswith("\n")


@pytest.mark.anyio
async def test_career_cli_runs_frozen_dataset(
    monkeypatch,
    tmp_path: Path,
    capsys,
):
    output_path = tmp_path / "career-report.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_career_benchmark",
            "--runs",
            "1",
            "--output",
            str(output_path),
        ],
    )

    await run()

    stdout = capsys.readouterr().out

    payload = json.loads(stdout)

    assert payload["engine"] == "deterministic"
    assert payload["scorer_version"] == "career-v1"
    assert payload["run_count"] == 1
    assert payload["case_count"] == 10

    assert output_path.exists()

    written_payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert written_payload == payload
