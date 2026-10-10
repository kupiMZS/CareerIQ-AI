import argparse
import sys
from pathlib import Path

import pytest

from app.core.config import Settings
from evals.providers import EnrichedResumeProvider
from evals.reporting import (
    build_resume_benchmark_report,
)
from evals.run_benchmark import (
    build_benchmark_provider,
    get_benchmark_model,
    get_benchmark_prompt_version,
    parse_args,
    positive_int,
    write_benchmark_report,
)
from evals.runner import ResumeBenchmarkSummary


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


def test_parse_args_uses_repeatability_defaults(
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_benchmark",
        ],
    )

    args = parse_args()

    assert args.provider == "rule_based"
    assert args.runs == 1
    assert args.output is None


def test_parse_args_accepts_runs_and_output(
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_benchmark",
            "--provider",
            "local_enriched",
            "--runs",
            "3",
            "--output",
            "reports/result.json",
        ],
    )

    args = parse_args()

    assert args.provider == "local_enriched"
    assert args.runs == 3
    assert args.output == Path("reports/result.json")


def test_local_benchmark_metadata_uses_model_and_prompt():
    settings = Settings(ai_model="qwen3:4b-instruct")

    assert (
        get_benchmark_model(
            "local_enriched",
            settings,
        )
        == "qwen3:4b-instruct"
    )

    assert get_benchmark_prompt_version("local_enriched") == "resume-analysis-v5"


def test_rule_based_benchmark_has_no_llm_metadata():
    settings = Settings(ai_model="qwen3:4b-instruct")

    assert (
        get_benchmark_model(
            "rule_based",
            settings,
        )
        is None
    )

    assert get_benchmark_prompt_version("rule_based") is None


def test_write_benchmark_report_creates_json_file(
    tmp_path: Path,
):
    summary = ResumeBenchmarkSummary(
        provider="rule_based",
        case_count=5,
        name_accuracy=1.0,
        email_accuracy=1.0,
        skills_f1=0.96,
        education_f1=0.8,
        experience_f1=0.2,
        overall_mean=0.792,
        cases=[],
    )

    report = build_resume_benchmark_report(
        provider="rule_based",
        model=None,
        prompt_version=None,
        dataset="resume_extraction_v1.jsonl",
        runs=[
            summary,
        ],
    )

    output_path = tmp_path / "nested" / "report.json"

    write_benchmark_report(
        report,
        output_path,
    )

    assert output_path.exists()

    content = output_path.read_text(encoding="utf-8")

    assert '"provider": "rule_based"' in content
    assert '"run_count": 1' in content
    assert content.endswith("\n")


def test_parse_args_accepts_rule_based_enriched(
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_benchmark",
            "--provider",
            "rule_based_enriched",
        ],
    )

    args = parse_args()

    assert args.provider == "rule_based_enriched"


def test_rule_based_enriched_wraps_rule_based_provider():
    settings = Settings(
        ai_model="qwen3:4b-instruct",
    )

    provider = build_benchmark_provider(
        "rule_based_enriched",
        settings,
    )

    assert isinstance(
        provider,
        EnrichedResumeProvider,
    )

    assert provider.provider.__class__.__name__ == "RuleBasedProvider"


def test_rule_based_enriched_has_no_llm_metadata():
    settings = Settings(
        ai_model="qwen3:4b-instruct",
    )

    assert (
        get_benchmark_model(
            "rule_based_enriched",
            settings,
        )
        is None
    )

    assert get_benchmark_prompt_version("rule_based_enriched") is None
