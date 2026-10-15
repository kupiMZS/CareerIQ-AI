import asyncio
import runpy
from pathlib import Path

import pytest

from app.providers.rule_based import RuleBasedProvider
from app.schemas.resume import Skill
from evals.loader import load_resume_eval_dataset
from evals.providers import EnrichedResumeProvider
from evals.scorer import score_resume_extraction
from evals.skill_recall_experiment_v3 import (
    EXPERIMENT_VERSION,
    propose_additional_skills,
)


@pytest.mark.parametrize(
    ("resume", "expected"),
    [
        (
            "Skills\nExcel\nJob Description\nSpring",
            ("Excel",),
        ),
        (
            "Skills\nExcel\nProfessional References\nGo",
            ("Excel",),
        ),
        (
            "Skills\nExcel\nClient Requirements\nTerraform",
            ("Excel",),
        ),
        (
            "Skills\nExcel\nReferences: available upon request\nGo",
            ("Excel",),
        ),
        (
            "Job requirements\nSkills\nTerraform",
            (),
        ),
        (
            "Client Requirements\nSkills\nGo",
            (),
        ),
        (
            "Skills\nExcel\nEducation\nGo",
            ("Excel",),
        ),
        (
            (
                "Job requirements\nSkills\nGo\nExperience\n"
                "Software Developer\nSkills\nExcel"
            ),
            ("Excel",),
        ),
    ],
)
def test_boundaries(resume, expected):
    assert propose_additional_skills(resume, ()) == expected


def test_prior_adversarial_regressions():
    path = Path(__file__).with_name("test_skill_recall_experiment_v2.py")
    cases = runpy.run_path(str(path))["CASES"]

    assert len(cases) == 30
    assert EXPERIMENT_VERSION == "skill-recall-shadow-v3"

    for _, resume, existing, expected in cases:
        actual = propose_additional_skills(resume, existing)
        assert actual == expected


def test_v3_preserves_known_resume_benchmark():
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

            proposed = propose_additional_skills(
                case.resume_text,
                [skill.name for skill in original.skills],
            )

            experimental = original.model_copy(
                update={
                    "skills": [
                        *original.skills,
                        *[Skill(name=name) for name in proposed],
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
