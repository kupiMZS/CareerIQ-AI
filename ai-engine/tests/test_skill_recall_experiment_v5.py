import asyncio
import runpy
from pathlib import Path

import pytest

from app.providers.rule_based import RuleBasedProvider
from app.schemas.resume import Skill
from evals.loader import load_resume_eval_dataset
from evals.providers import EnrichedResumeProvider
from evals.scorer import score_resume_extraction
from evals.skill_recall_experiment_v5 import (
    EXPERIMENT_VERSION,
    propose_additional_skills,
)

# Synthetic development examples, not real-world holdout cases.
# ID, category, resume text, existing skills, expected additions.
CASES = [
    (
        "core_competencies",
        "format",
        "Core Competencies\nExcel\nTerraform",
        (),
        ("Excel", "Terraform"),
    ),
    (
        "slash_separated",
        "format",
        "Tools: Excel / Terraform",
        (),
        ("Excel", "Terraform"),
    ),
    (
        "go_dash_golang",
        "format",
        "Skills\nGo — Golang",
        (),
        ("Go",),
    ),
    (
        "excel_advanced",
        "format",
        "Skills\nMicrosoft Excel (advanced)",
        (),
        ("Excel",),
    ),
    (
        "terraform_aws",
        "format",
        "Skills\nTerraform / AWS",
        ("AWS",),
        ("Terraform",),
    ),
    (
        "stack_inline",
        "format",
        "Stack: Terraform | Spring",
        (),
        ("Terraform", "Spring"),
    ),
    (
        "spring_framework",
        "format",
        "Skills\n- Spring Framework",
        (),
        ("Spring",),
    ),
    (
        "go_programming_language",
        "format",
        "Skills\nGo (programming language)",
        (),
        ("Go",),
    ),
    (
        "job_competencies",
        "negative",
        "Job Requirements\nCore Competencies\nExcel",
        (),
        (),
    ),
    (
        "job_stack",
        "negative",
        "Job Requirements\nStack: Spring | Go",
        (),
        (),
    ),
    (
        "job_technology_stack",
        "negative",
        "Job Requirements\nTechnology Stack\nTerraform",
        (),
        (),
    ),
    (
        "client_tools",
        "negative",
        "Client Requirements\nTools\nExcel",
        (),
        (),
    ),
    (
        "reference_skills",
        "negative",
        "References\nProfessional Skills\nGo",
        (),
        (),
    ),
    (
        "ordinary_go",
        "negative",
        "Skills\nI go to meetings",
        (),
        (),
    ),
    (
        "spring_season",
        "negative",
        "Education\nSpring 2026",
        (),
        (),
    ),
    (
        "experience_spring",
        "negative",
        "Experience\nSpring",
        (),
        (),
    ),
    (
        "negated_go",
        "negative",
        "Skills\nNo experience with Go",
        (),
        (),
    ),
    (
        "career_goals",
        "negative",
        "Career Goals\nSkills: Terraform",
        (),
        (),
    ),
    (
        "nested_skills",
        "negative",
        "Job Requirements\nSkills\nExcel",
        (),
        (),
    ),
    (
        "nested_professional_skills",
        "negative",
        "Role Requirements\nProfessional Skills\nSpring",
        (),
        (),
    ),
    (
        "ordinary_skills",
        "preservation",
        "Skills\nExcel\nSpring",
        (),
        ("Excel", "Spring"),
    ),
    (
        "existing_aliases",
        "preservation",
        "Technical Skills\nMicrosoft Excel\nGo (Golang)",
        (),
        ("Excel", "Go"),
    ),
    (
        "section_recovery",
        "preservation",
        "Client Requirements\nTools\nExcel\nEducation\nBSc\nSkills\nGo",
        (),
        ("Go",),
    ),
    (
        "inline_skills",
        "preservation",
        "Skills: Terraform, Excel",
        (),
        ("Terraform", "Excel"),
    ),
]


@pytest.mark.parametrize(
    "case",
    CASES,
    ids=[case[0] for case in CASES],
)
def test_format_and_safety(case):
    _, _, resume, existing, expected = case

    original = tuple(existing)
    actual = propose_additional_skills(resume, existing)

    assert actual == expected
    assert tuple(existing) == original
    assert actual == propose_additional_skills(resume, existing)
    assert len(actual) == len(set(actual))


@pytest.mark.parametrize(
    ("resume", "expected"),
    [
        (
            "Career Goals\nStack\nTerraform",
            (),
        ),
        (
            "Professional Summary\nCore Competencies\nGo",
            (),
        ),
        (
            "Career Interests\nStack\nSpring",
            (),
        ),
        (
            "Career Goals\nSkills:\nExcel",
            (),
        ),
        (
            "Career Goals\nTechnical Skills:\nGo",
            (),
        ),
        (
            "Professional Summary\nSkills:\nSpring",
            (),
        ),
        (
            "Professional Summary\nSoftware Engineer\nSkills\nExcel",
            ("Excel",),
        ),
        (
            "Professional Summary\nExperienced analyst\nCore Competencies\nExcel",
            (),
        ),
    ],
)
def test_adjacent_narrative_heading_safety(resume, expected):
    assert propose_additional_skills(resume, ()) == expected


def test_preserves_v2_adversarial_cases():
    path = Path(__file__).with_name("test_skill_recall_experiment_v2.py")

    cases = runpy.run_path(str(path))["CASES"]

    assert EXPERIMENT_VERSION == "skill-recall-shadow-v5"
    assert len(cases) == 30

    for _, resume, existing, expected in cases:
        assert propose_additional_skills(resume, existing) == expected


def test_preserves_v4_nested_boundary_cases():
    path = Path(__file__).with_name("test_skill_recall_experiment_v4.py")

    cases = runpy.run_path(str(path))["CASES"]

    assert len(cases) == 18

    for _, resume, existing, expected in cases:
        assert propose_additional_skills(resume, existing) == expected


def test_preserves_existing_resume_extraction_benchmark():
    async def evaluate():
        cases = load_resume_eval_dataset(
            Path("evals/datasets/resume_extraction_v3.jsonl")
        )

        provider = EnrichedResumeProvider(RuleBasedProvider())

        legacy = [0, 0, 0]
        shadow = [0, 0, 0]

        for case in cases:
            original = await provider.analyze_resume(case.resume_text)

            before = original.model_dump()

            additions = propose_additional_skills(
                case.resume_text,
                [skill.name for skill in original.skills],
            )

            experimental = original.model_copy(
                update={
                    "skills": [
                        *original.skills,
                        *[Skill(name=name) for name in additions],
                    ]
                }
            )

            for totals, intelligence in (
                (legacy, original),
                (shadow, experimental),
            ):
                metric = score_resume_extraction(
                    case.expected,
                    intelligence,
                ).skills

                totals[0] += metric.matched_count
                totals[1] += metric.actual_count
                totals[2] += metric.expected_count

            assert original.model_dump() == before

        assert len(cases) == 25
        assert legacy == [61, 61, 66]
        assert shadow == [66, 66, 66]

    asyncio.run(evaluate())


@pytest.mark.parametrize(
    ("resume", "expected"),
    [
        (
            "Career Goals\nI want to learn\nStack\nTerraform",
            (),
        ),
        (
            "Career Interests\nExploring new technologies\nCore Competencies\nGo",
            (),
        ),
        (
            "Skills\nExcel\nCareer Goals\nI plan to learn\nStack\nTerraform",
            ("Excel",),
        ),
        (
            "Professional Summary\nNot yet proficient\nCore Competencies\nSpring",
            (),
        ),
    ],
)
def test_multiline_narrative_section_safety(resume, expected):
    assert propose_additional_skills(resume, ()) == expected
