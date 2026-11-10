"""Known adversarial regression cases; not an unbiased holdout."""

import asyncio
from pathlib import Path

import pytest

from app.providers.rule_based import RuleBasedProvider
from app.schemas.resume import Skill
from evals.loader import load_resume_eval_dataset
from evals.providers import EnrichedResumeProvider
from evals.scorer import score_resume_extraction
from evals.skill_recall_experiment_v1 import propose_additional_skills as shadow_v1
from evals.skill_recall_experiment_v2 import (
    EXPERIMENT_VERSION,
    EXPERIMENTAL_TERMS,
)
from evals.skill_recall_experiment_v2 import (
    propose_additional_skills as shadow_v2,
)

# Case ID, resume text, baseline skills, expected additional skills.
CASES = (
    ("positive_multiline", "Skills\nGo\nExcel", (), ("Go", "Excel")),
    (
        "positive_bullets",
        "Technical Skills\n- Terraform\n- Spring",
        (),
        ("Terraform", "Spring"),
    ),
    ("positive_inline", "Skills: Spring, Excel", (), ("Spring", "Excel")),
    ("positive_single", "Core Skills\nTerraform", (), ("Terraform",)),
    ("positive_pipe", "Skills\nExcel | Go", (), ("Excel", "Go")),
    ("positive_semicolon", "Skills: Go; Terraform", (), ("Go", "Terraform")),
    (
        "positive_early",
        "Python, AWS, Docker, Terraform",
        ("Python", "AWS", "Docker"),
        ("Terraform",),
    ),
    (
        "positive_compact",
        "Olivia Brown | olivia@example.com\nCloud Engineer\nPython, AWS, Docker, Terraform",
        ("Python", "AWS", "Docker"),
        ("Terraform",),
    ),
    ("positive_casefold", "SKILLS\nEXCEL\nSPRING", (), ("Excel", "Spring")),
    ("positive_duplicates", "Skills\nGo\nGo\nExcel\nExcel", (), ("Go", "Excel")),
    ("negative_ordinary_go", "I go to work every day.", (), ()),
    ("negative_season", "Experience\nSpring 2026", (), ()),
    ("negative_education", "Education\nGo", (), ()),
    ("negative_languages", "Languages\nExcel", (), ()),
    ("negative_rejection", "Skills\nNever used Go", (), ()),
    ("negative_career_goal", "Career Goals\nGo", (), ()),
    ("negative_job_requirements", "Job requirements\nTerraform", (), ()),
    ("negative_role_requirements", "Role requirements\nSpring", (), ()),
    ("nested_job_skills", "Job requirements\nSkills: Terraform", (), ()),
    ("nested_career_skills", "Career Goals\nTechnical Skills: Go, Spring", (), ()),
    ("nested_requirement_list", "Job requirements\nSkills: Excel, Terraform", (), ()),
    ("unknown_requirements", "Skills\nExcel\nRequirements\nGo", (), ("Excel",)),
    ("unknown_references", "Skills\nSpring\nReferences\nTerraform", (), ("Spring",)),
    ("recognized_boundary", "Skills\nExcel\nEducation\nGo", (), ("Excel",)),
    ("professional_heading", "Professional Skills\nExcel", (), ("Excel",)),
    ("technology_heading", "Technology Stack\nTerraform", (), ("Terraform",)),
    ("tools_inline", "Tools: Excel", (), ("Excel",)),
    ("go_parenthetical", "Skills\nGo (Golang)", (), ("Go",)),
    ("microsoft_excel", "Skills\nMicrosoft Excel", (), ("Excel",)),
    (
        "terraform_qualification",
        "Skills\nTerraform (Infrastructure as Code)",
        (),
        ("Terraform",),
    ),
)


@pytest.mark.parametrize("case", CASES, ids=[case[0] for case in CASES])
def test_adversarial_case(case):
    _, resume, existing, expected = case
    before = list(existing)
    predicted = shadow_v2(resume, before)
    assert predicted == expected
    assert before == list(existing)
    assert predicted == shadow_v2(resume, before)
    assert len(predicted) == len(set(predicted))
    assert set(predicted) <= set(EXPERIMENTAL_TERMS)


def test_v1_v2_comparison():
    assert EXPERIMENT_VERSION == "skill-recall-shadow-v2"
    assert len(CASES) == 30
    assert len({case[0] for case in CASES}) == 30

    def measure(extractor):
        exact = matched = predicted = expected = 0
        for _, resume, existing, gold in CASES:
            actual = set(extractor(resume, existing))
            reference = set(gold)
            exact += actual == reference
            matched += len(actual & reference)
            predicted += len(actual)
            expected += len(reference)
        return exact, matched, predicted, expected

    assert measure(shadow_v1) == (19, 20, 27, 26)
    assert measure(shadow_v2) == (30, 26, 26, 26)


def test_v3_skill_recall_is_preserved():
    async def evaluate():
        cases = load_resume_eval_dataset(
            Path("evals/datasets/resume_extraction_v3.jsonl")
        )
        provider = EnrichedResumeProvider(RuleBasedProvider())
        legacy = [0, 0, 0]
        shadow = [0, 0, 0]
        recovered = {}

        for case in cases:
            original = await provider.analyze_resume(case.resume_text)
            before = original.model_dump()
            additions = shadow_v2(
                case.resume_text, [skill.name for skill in original.skills]
            )
            experimental = original.model_copy(
                update={
                    "skills": [*original.skills, *[Skill(name=n) for n in additions]]
                }
            )
            for totals, intelligence in ((legacy, original), (shadow, experimental)):
                score = score_resume_extraction(case.expected, intelligence).skills
                totals[0] += score.matched_count
                totals[1] += score.actual_count
                totals[2] += score.expected_count
            if additions:
                recovered[case.case_id] = additions
            assert original.model_dump() == before

        assert len(cases) == 25
        assert legacy == [61, 61, 66]
        assert shadow == [66, 66, 66]
        assert recovered == {
            "missing_email": ("Excel",),
            "education_without_institution": ("Spring",),
            "experience_en_dash_format": ("Go",),
            "company_first_experience": ("Spring",),
            "compact_contact_and_inline_skills": ("Terraform",),
        }

    asyncio.run(evaluate())
