from pathlib import Path

import pytest

from evals.loader import (
    EvalDatasetError,
    load_resume_eval_dataset,
)

EVALS_DIR = Path(__file__).parents[1] / "evals" / "datasets"

V1_DATASET_PATH = EVALS_DIR / "resume_extraction_v1.jsonl"

V2_DATASET_PATH = EVALS_DIR / "resume_extraction_v2.jsonl"

V3_DATASET_PATH = EVALS_DIR / "resume_extraction_v3.jsonl"


def get_case_ids(
    dataset_path: Path,
) -> set[str]:
    return {case.case_id for case in load_resume_eval_dataset(dataset_path)}


def test_v1_dataset_loads_five_cases():
    cases = load_resume_eval_dataset(V1_DATASET_PATH)

    assert len(cases) == 5


def test_v2_dataset_loads_fifteen_cases():
    cases = load_resume_eval_dataset(V2_DATASET_PATH)

    assert len(cases) == 15


def test_v3_dataset_loads_twenty_five_cases():
    cases = load_resume_eval_dataset(V3_DATASET_PATH)

    assert len(cases) == 25


@pytest.mark.parametrize(
    "dataset_path",
    [
        V1_DATASET_PATH,
        V2_DATASET_PATH,
        V3_DATASET_PATH,
    ],
)
def test_dataset_case_ids_are_unique(
    dataset_path: Path,
):
    cases = load_resume_eval_dataset(dataset_path)

    case_ids = [case.case_id for case in cases]

    assert len(case_ids) == len(set(case_ids))


def test_v2_preserves_all_v1_cases():
    v1_case_ids = get_case_ids(V1_DATASET_PATH)

    v2_case_ids = get_case_ids(V2_DATASET_PATH)

    assert v1_case_ids <= v2_case_ids


def test_v3_preserves_all_v2_cases():
    v2_case_ids = get_case_ids(V2_DATASET_PATH)

    v3_case_ids = get_case_ids(V3_DATASET_PATH)

    assert v2_case_ids <= v3_case_ids


def test_v2_contains_expected_edge_cases():
    case_ids = get_case_ids(V2_DATASET_PATH)

    expected_edge_cases = {
        "multiple_education_entries",
        "education_without_institution",
        "experience_dash_format",
        "experience_without_dates",
        "inline_skills_no_heading",
        "mixed_section_order",
        "contact_only_sparse",
        "email_with_surrounding_punctuation",
        "repeated_skills",
        "no_standard_section_headings",
    }

    assert expected_edge_cases <= case_ids


def test_v3_contains_expected_hard_cases():
    case_ids = get_case_ids(V3_DATASET_PATH)

    expected_hard_cases = {
        "experience_em_dash_format",
        "experience_en_dash_format",
        "company_first_experience",
        "pipe_separated_experience",
        "multiple_roles_same_company",
        "same_title_different_companies",
        "education_degree_and_institution_separate_lines",
        "multiple_education_multiline",
        "compact_contact_and_inline_skills",
        "noisy_bulleted_resume",
    }

    assert expected_hard_cases <= case_ids


@pytest.mark.parametrize(
    "dataset_path",
    [
        V2_DATASET_PATH,
        V3_DATASET_PATH,
    ],
)
def test_dataset_cases_have_descriptions_and_tags(
    dataset_path: Path,
):
    cases = load_resume_eval_dataset(dataset_path)

    for case in cases:
        assert case.description
        assert case.tags


def test_loader_rejects_duplicate_case_ids(
    tmp_path: Path,
):
    dataset_path = tmp_path / "duplicate.jsonl"

    line = (
        '{"case_id":"duplicate",'
        '"description":"Synthetic case",'
        '"resume_text":"John Doe",'
        '"expected":{}}'
    )

    dataset_path.write_text(
        f"{line}\n{line}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        EvalDatasetError,
        match="Duplicate evaluation case_id",
    ):
        load_resume_eval_dataset(dataset_path)


def test_loader_rejects_invalid_json(
    tmp_path: Path,
):
    dataset_path = tmp_path / "invalid.jsonl"

    dataset_path.write_text(
        "{not-valid-json}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        EvalDatasetError,
        match="Invalid JSON",
    ):
        load_resume_eval_dataset(dataset_path)
