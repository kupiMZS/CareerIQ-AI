import asyncio
import runpy
from pathlib import Path

import pytest

from app.providers.rule_based import RuleBasedProvider
from app.schemas.resume import Skill
from evals.loader import load_resume_eval_dataset
from evals.providers import EnrichedResumeProvider
from evals.scorer import score_resume_extraction
from evals.skill_recall_experiment_v4 import (
    EXPERIMENT_VERSION,
)
from evals.skill_recall_experiment_v4 import (
    propose_additional_skills as shadow_v4,
)

# Cases are synthetic development evidence, not real-world holdout data.
CASES = [
    (
        "nested_job_tools",
        "Job Requirements\nTools\nExcel",
        (),
        (),
    ),
    (
        "nested_client_stack",
        "Client Requirements\nTechnology Stack\nTerraform",
        (),
        (),
    ),
    (
        "nested_role_professional_skills",
        "Role Requirements\nProfessional Skills\nGo",
        (),
        (),
    ),
    (
        "nested_references_tools",
        "References\nTools\nSpring",
        (),
        (),
    ),
    (
        "skills_then_nested_job_tools",
        "Skills\nExcel\nJob Description\nTools\nGo",
        (),
        ("Excel",),
    ),
    (
        "excluded_then_valid_section",
        ("Job Requirements\nTechnology Stack\nGo\nEducation\nBSc\nSkills\nExcel"),
        (),
        ("Excel",),
    ),
    (
        "standalone_tools",
        "Tools\nExcel",
        (),
        ("Excel",),
    ),
    (
        "standalone_technology_stack",
        "Technology Stack\nTerraform",
        (),
        ("Terraform",),
    ),
    (
        "ordinary_skills",
        "Skills\nExcel\nSpring",
        (),
        ("Excel", "Spring"),
    ),
    (
        "nested_inline_tools",
        "Job Requirements\nTools: Excel",
        (),
        (),
    ),
    (
        "nested_inline_skills",
        "Client Requirements\nSkills: Terraform",
        (),
        (),
    ),
    (
        "negated_skill",
        "Skills\nNo experience with Go",
        (),
        (),
    ),
    (
        "nested_core_competencies",
        "Role Requirements\nCore Competencies\nExcel",
        (),
        (),
    ),
    (
        "inline_references_boundary",
        "Skills\nGo\nReferences: available upon request\nExcel",
        (),
        ("Go",),
    ),
    (
        "experience_boundary",
        "Skills\nExcel\nWork Experience\nDeveloper\nGo",
        (),
        ("Excel",),
    ),
    (
        "chained_nested_skill_headings",
        ("Job Requirements\nProfessional Skills\nGo\nTechnology Stack\nExcel"),
        (),
        (),
    ),
    (
        "nested_inline_then_standalone",
        ("Client Requirements\nTools: Excel\nTools\nTerraform"),
        (),
        (),
    ),
    (
        "recovery_after_education",
        (
            "Job Requirements\nTools\nExcel\nEducation\n"
            "Bachelor of Science\nTechnology Stack\nSpring"
        ),
        (),
        ("Spring",),
    ),
]


@pytest.mark.parametrize(
    "case",
    CASES,
    ids=[case[0] for case in CASES],
)
def test_nested_section_boundaries(case):
    _, resume, existing, expected = case

    original = list(existing)
    actual = shadow_v4(resume, original)

    assert actual == expected
    assert original == list(existing)
    assert actual == shadow_v4(resume, original)
    assert len(actual) == len(set(actual))


def test_preserves_prior_development_regressions():
    path = Path(__file__).with_name("test_skill_recall_experiment_v2.py")

    previous = runpy.run_path(str(path))["CASES"]

    assert len(previous) == 30
    assert EXPERIMENT_VERSION == "skill-recall-shadow-v4"

    for _, resume, existing, expected in previous:
        assert shadow_v4(resume, existing) == expected


def test_preserves_known_v3_resume_benchmark():
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

            additions = shadow_v4(
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
