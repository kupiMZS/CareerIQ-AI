import json
from pathlib import Path

import pytest

from app.core.config import Settings
from evals.loader import load_resume_eval_dataset
from evals.run_benchmark import build_benchmark_provider
from evals.runner import run_resume_benchmark

AI_ENGINE_DIR = Path(__file__).parents[1]

DATASET_PATH = (
    AI_ENGINE_DIR / "evals" / "datasets" / "resume_extraction_phase2_languages_v1.jsonl"
)

BASELINE_PATH = (
    AI_ENGINE_DIR
    / "evals"
    / "baselines"
    / ("resume_extraction_phase2_languages_v1_rule_based_enriched.json")
)


def load_baseline() -> dict:
    return json.loads(
        BASELINE_PATH.read_text(
            encoding="utf-8",
        )
    )


def test_phase2_language_baseline_metadata():
    baseline = load_baseline()

    assert baseline["provider"] == "rule_based_enriched"
    assert baseline["model"] is None
    assert baseline["prompt_version"] is None

    assert baseline["run_count"] == 3
    assert baseline["case_count"] == 7

    assert baseline["extended"] is None

    phase2 = baseline["phase2"]

    assert phase2 is not None
    assert phase2["scorer_version"] == "phase2-v2"
    assert phase2["case_count"] == 7

    assert phase2["metrics"]["publications_f1"] is None

    languages = phase2["metrics"]["languages_f1"]

    assert languages is not None
    assert languages["mean"] == 1.0
    assert languages["minimum"] == 1.0
    assert languages["maximum"] == 1.0
    assert languages["standard_deviation"] == 0.0

    overall = phase2["metrics"]["overall_mean"]

    assert overall["mean"] == 1.0
    assert overall["minimum"] == 1.0
    assert overall["maximum"] == 1.0
    assert overall["standard_deviation"] == 0.0


def test_phase2_language_baseline_runs_are_repeatable():
    baseline = load_baseline()

    assert len(baseline["runs"]) == 3

    for run in baseline["runs"]:
        phase2 = run["phase2"]

        assert phase2 is not None
        assert phase2["scorer_version"] == "phase2-v2"
        assert phase2["case_count"] == 7
        assert phase2["publications_f1"] is None
        assert phase2["languages_f1"] == 1.0
        assert phase2["overall_mean"] == 1.0


@pytest.mark.anyio
async def test_rule_based_enriched_meets_frozen_language_baseline():
    baseline = load_baseline()

    settings = Settings(
        ai_model="qwen3:4b-instruct",
    )

    provider = build_benchmark_provider(
        "rule_based_enriched",
        settings,
    )

    cases = load_resume_eval_dataset(DATASET_PATH)

    summary = await run_resume_benchmark(
        provider_name="rule_based_enriched",
        provider=provider,
        cases=cases,
    )

    assert summary.phase2 is not None

    expected = baseline["phase2"]

    assert summary.phase2.scorer_version == expected["scorer_version"]

    assert summary.phase2.case_count == expected["case_count"]

    assert summary.phase2.publications_f1 is None

    assert summary.phase2.languages_f1 == expected["metrics"]["languages_f1"]["mean"]

    assert summary.phase2.overall_mean == expected["metrics"]["overall_mean"]["mean"]
