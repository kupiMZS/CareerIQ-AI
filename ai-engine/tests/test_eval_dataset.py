from pathlib import Path

import pytest

from evals.loader import EvalDatasetError, load_resume_eval_dataset
from evals.schemas import ResumeEvalCase

EVALS_DIR = Path(__file__).parents[1] / "evals" / "datasets"

V1_DATASET_PATH = EVALS_DIR / "resume_extraction_v1.jsonl"

V2_DATASET_PATH = EVALS_DIR / "resume_extraction_v2.jsonl"

V3_DATASET_PATH = EVALS_DIR / "resume_extraction_v3.jsonl"

EXTENDED_V1_DATASET_PATH = EVALS_DIR / "resume_extraction_extended_v1.jsonl"

PHASE2_PUBLICATIONS_V1_DATASET_PATH = (
    EVALS_DIR / "resume_extraction_phase2_publications_v1.jsonl"
)


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
        EXTENDED_V1_DATASET_PATH,
        PHASE2_PUBLICATIONS_V1_DATASET_PATH,
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
        EXTENDED_V1_DATASET_PATH,
        PHASE2_PUBLICATIONS_V1_DATASET_PATH,
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


def test_existing_dataset_case_has_no_extended_expectations():
    cases = load_resume_eval_dataset(V3_DATASET_PATH)

    assert cases
    assert all(case.extended_expected is None for case in cases)


def test_eval_case_accepts_extended_expectations():
    case = ResumeEvalCase.model_validate(
        {
            "case_id": "extended-example",
            "description": ("Synthetic extended extraction case"),
            "tags": [
                "extended",
            ],
            "resume_text": ("Jane Smith\nSenior Software Engineer"),
            "expected": {
                "name": "Jane Smith",
            },
            "extended_expected": {
                "headline": ("Senior Software Engineer"),
                "education": [
                    {
                        "degree": ("BSc Computer Science"),
                        "institution": ("Example University"),
                        "field_of_study": ("Computer Science"),
                        "start_date": "2018",
                        "end_date": "2022",
                    }
                ],
                "experience": [
                    {
                        "job_title": ("Software Engineer"),
                        "company": ("Example Technologies"),
                        "start_date": "2022",
                        "end_date": "2025",
                        "responsibilities": [
                            ("Built backend APIs"),
                        ],
                    }
                ],
                "projects": [
                    {
                        "name": "CareerIQ",
                        "description": ("Career intelligence platform"),
                        "technologies": [
                            "Python",
                            "FastAPI",
                        ],
                    }
                ],
                "certifications": [
                    {
                        "name": ("Cloud Developer"),
                        "issuer": ("Example Cloud"),
                        "date": "2025",
                    }
                ],
            },
        }
    )

    assert case.extended_expected is not None

    extended = case.extended_expected

    assert extended.headline == "Senior Software Engineer"

    assert extended.education[0].field_of_study == "Computer Science"

    assert extended.experience[0].responsibilities == ["Built backend APIs"]

    assert extended.projects[0].technologies == ["Python", "FastAPI"]

    assert extended.certifications[0].issuer == "Example Cloud"


def test_extended_v1_dataset_loads_ten_cases():
    cases = load_resume_eval_dataset(EXTENDED_V1_DATASET_PATH)

    assert len(cases) == 10


def test_extended_v1_cases_all_have_extended_expectations():
    cases = load_resume_eval_dataset(EXTENDED_V1_DATASET_PATH)

    assert all(case.extended_expected is not None for case in cases)


def test_extended_v1_contains_expected_cases():
    case_ids = get_case_ids(EXTENDED_V1_DATASET_PATH)

    expected_case_ids = {
        "extended_full_stack_engineer",
        "extended_education_dates",
        "extended_experience_dates",
        "extended_multiple_responsibilities",
        "extended_project",
        "extended_multiple_projects",
        "extended_certification",
        "extended_multiple_certifications",
        "extended_missing_optional_fields",
        "extended_two_jobs",
    }

    assert case_ids == expected_case_ids


def test_eval_case_accepts_phase2_publication_expectations():
    case = ResumeEvalCase.model_validate(
        {
            "case_id": "phase2-publication-example",
            "description": "Synthetic Phase 2 publication case",
            "tags": [
                "phase2",
                "publications",
            ],
            "resume_text": ("Jane Smith\nPublications\nTitle: Example Publication"),
            "expected": {
                "name": "Jane Smith",
            },
            "phase2_expected": {
                "publications": [
                    {
                        "title": "Example Publication",
                        "authors": [
                            "Jane Smith",
                        ],
                        "venue": "Example Journal",
                        "date": "2025",
                        "url": "https://example.com/publication",
                    }
                ]
            },
        }
    )

    assert case.phase2_expected is not None

    publication = case.phase2_expected.publications[0]

    assert publication.title == "Example Publication"
    assert publication.authors == ["Jane Smith"]
    assert publication.venue == "Example Journal"
    assert publication.date == "2025"
    assert publication.url == "https://example.com/publication"


def test_phase2_publications_v1_dataset_loads_seven_cases():
    cases = load_resume_eval_dataset(PHASE2_PUBLICATIONS_V1_DATASET_PATH)

    assert len(cases) == 7


def test_phase2_publications_v1_cases_have_phase2_expectations():
    cases = load_resume_eval_dataset(PHASE2_PUBLICATIONS_V1_DATASET_PATH)

    assert all(case.phase2_expected is not None for case in cases)

    assert all(case.extended_expected is None for case in cases)


def test_phase2_publications_v1_contains_expected_cases():
    case_ids = get_case_ids(PHASE2_PUBLICATIONS_V1_DATASET_PATH)

    assert case_ids == {
        "phase2_publication_complete",
        "phase2_publication_multiple",
        "phase2_publication_missing_optional_metadata",
        "phase2_publication_section_alias",
        "phase2_publication_field_aliases",
        "phase2_publication_unstructured_not_inferred",
        "phase2_publication_absent",
    }


def test_eval_case_accepts_phase2_language_expectations():
    case = ResumeEvalCase.model_validate(
        {
            "case_id": "phase2-language-example",
            "description": "Synthetic Phase 2 language case",
            "tags": [
                "phase2",
                "languages",
            ],
            "resume_text": ("Jane Smith\nLanguages\nEnglish: Fluent"),
            "expected": {
                "name": "Jane Smith",
            },
            "phase2_expected": {
                "languages": [
                    {
                        "name": "English",
                        "proficiency": "Fluent",
                    }
                ]
            },
        }
    )

    assert case.phase2_expected is not None
    assert case.phase2_expected.publications is None

    assert case.phase2_expected.languages is not None
    assert len(case.phase2_expected.languages) == 1

    language = case.phase2_expected.languages[0]

    assert language.name == "English"
    assert language.proficiency == "Fluent"


PHASE2_LANGUAGES_V1_DATASET_PATH = (
    EVALS_DIR / "resume_extraction_phase2_languages_v1.jsonl"
)


def test_phase2_languages_v1_dataset_loads_seven_cases():
    cases = load_resume_eval_dataset(PHASE2_LANGUAGES_V1_DATASET_PATH)

    assert len(cases) == 7


def test_phase2_languages_v1_cases_have_language_coverage():
    cases = load_resume_eval_dataset(PHASE2_LANGUAGES_V1_DATASET_PATH)

    assert all(case.phase2_expected is not None for case in cases)

    assert all(
        case.phase2_expected.languages is not None
        for case in cases
        if case.phase2_expected is not None
    )

    assert all(
        case.phase2_expected.publications is None
        for case in cases
        if case.phase2_expected is not None
    )

    assert all(case.extended_expected is None for case in cases)


def test_phase2_languages_v1_contains_expected_cases():
    case_ids = get_case_ids(PHASE2_LANGUAGES_V1_DATASET_PATH)

    assert case_ids == {
        "phase2_language_complete",
        "phase2_language_multiple_formats",
        "phase2_language_missing_proficiency",
        "phase2_language_section_alias",
        "phase2_language_labeled_records",
        "phase2_language_no_inference",
        "phase2_language_absent",
    }


def test_phase2_languages_v1_has_descriptions_and_tags():
    cases = load_resume_eval_dataset(PHASE2_LANGUAGES_V1_DATASET_PATH)

    assert all(case.description.strip() for case in cases)

    assert all(case.tags for case in cases)
