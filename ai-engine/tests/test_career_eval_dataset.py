import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from evals.loader import (
    EvalDatasetError,
    load_career_eval_dataset,
)
from evals.schemas import CareerEvalCase


def build_case_payload(
    case_id: str = "backend-engineer",
) -> dict:
    return {
        "case_id": case_id,
        "description": ("Backend-focused candidate with matching skills"),
        "tags": [
            "career-recommendation",
            "backend",
        ],
        "request": {
            "profile": {
                "current_role": "Backend Developer",
                "career_goal": "Backend Engineer",
                "years_experience": 2,
                "education": [
                    "BSc Computer Science",
                ],
                "interests": [],
            },
            "skills": [
                "Python",
                "FastAPI",
                "PostgreSQL",
                "Docker",
            ],
        },
        "expected": {
            "status": "ok",
            "top_career": "Backend Engineer",
            "relevant_careers": [
                "Backend Engineer",
            ],
            "missing_skills": [],
            "roadmap_skills": [
                "Python",
                "FastAPI",
                "PostgreSQL",
                "Docker",
            ],
            "entry_level": False,
            "missing_information": [],
        },
    }


def test_career_eval_case_accepts_production_request_contract():
    case = CareerEvalCase.model_validate(build_case_payload())

    assert case.case_id == "backend-engineer"

    assert case.request.profile.current_role == "Backend Developer"

    assert case.request.profile.career_goal == "Backend Engineer"

    assert case.request.skills == [
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
    ]

    assert case.expected.top_career == "Backend Engineer"

    assert case.expected.status == "ok"


def test_career_eval_case_reuses_request_validation():
    payload = build_case_payload()

    payload["request"]["profile"]["years_experience"] = -1

    with pytest.raises(ValidationError):
        CareerEvalCase.model_validate(payload)


def test_career_dataset_loader_loads_cases(
    tmp_path: Path,
):
    dataset_path = tmp_path / "career_recommendation.jsonl"

    first = build_case_payload("backend-engineer")

    second = build_case_payload("backend-engineer-second")

    dataset_path.write_text(
        "\n".join(
            [
                json.dumps(first),
                json.dumps(second),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    cases = load_career_eval_dataset(dataset_path)

    assert len(cases) == 2

    assert [case.case_id for case in cases] == [
        "backend-engineer",
        "backend-engineer-second",
    ]


def test_career_dataset_loader_rejects_duplicate_case_ids(
    tmp_path: Path,
):
    dataset_path = tmp_path / "duplicate-career.jsonl"

    payload = build_case_payload()

    line = json.dumps(payload)

    dataset_path.write_text(
        f"{line}\n{line}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        EvalDatasetError,
        match="Duplicate evaluation case_id",
    ):
        load_career_eval_dataset(dataset_path)


def test_career_dataset_loader_rejects_invalid_json(
    tmp_path: Path,
):
    dataset_path = tmp_path / "invalid-career.jsonl"

    dataset_path.write_text(
        "{not-valid-json}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        EvalDatasetError,
        match="Invalid JSON",
    ):
        load_career_eval_dataset(dataset_path)


def test_career_dataset_loader_rejects_empty_dataset(
    tmp_path: Path,
):
    dataset_path = tmp_path / "empty-career.jsonl"

    dataset_path.write_text(
        "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        EvalDatasetError,
        match="contains no cases",
    ):
        load_career_eval_dataset(dataset_path)


def test_career_dataset_loader_rejects_missing_file(
    tmp_path: Path,
):
    dataset_path = tmp_path / "missing-career.jsonl"

    with pytest.raises(
        EvalDatasetError,
        match="does not exist",
    ):
        load_career_eval_dataset(dataset_path)
