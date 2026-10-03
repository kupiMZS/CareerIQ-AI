import json
from pathlib import Path

import pytest

from evals.loader import (
    EvalDatasetError,
    load_resume_eval_dataset,
)

DATASET_PATH = (
    Path(__file__).parents[1] / "evals" / "datasets" / "resume_extraction_v1.jsonl"
)


def test_resume_eval_dataset_loads():
    cases = load_resume_eval_dataset(DATASET_PATH)

    assert len(cases) == 5


def test_resume_eval_dataset_case_ids_are_unique():
    cases = load_resume_eval_dataset(DATASET_PATH)

    case_ids = [case.case_id for case in cases]

    assert len(case_ids) == len(set(case_ids))


def test_resume_eval_dataset_contains_expected_edge_cases():
    cases = load_resume_eval_dataset(DATASET_PATH)

    case_ids = {case.case_id for case in cases}

    assert "missing_email" in case_ids
    assert "multiple_experience_entries" in case_ids
    assert "sparse_resume" in case_ids


def test_loader_rejects_duplicate_case_ids(
    tmp_path: Path,
):
    path = tmp_path / "duplicate.jsonl"

    record = {
        "case_id": "duplicate",
        "description": "Synthetic duplicate case.",
        "resume_text": "John Doe",
        "expected": {},
    }

    path.write_text(
        "\n".join(
            [
                json.dumps(record),
                json.dumps(record),
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        EvalDatasetError,
        match="Duplicate evaluation case_id",
    ):
        load_resume_eval_dataset(path)


def test_loader_rejects_invalid_json(
    tmp_path: Path,
):
    path = tmp_path / "invalid.jsonl"

    path.write_text(
        "{invalid-json}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        EvalDatasetError,
        match="Invalid JSON",
    ):
        load_resume_eval_dataset(path)
