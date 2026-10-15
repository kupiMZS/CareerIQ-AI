import pytest

from evals.skill_recall_experiment_v1 import (
    EXPERIMENT_VERSION,
    propose_additional_skills,
)


@pytest.mark.parametrize(
    ("resume", "existing", "expected"),
    [
        (
            "Skills\nExcel\nSpring\nGo\nTerraform",
            [],
            ("Excel", "Spring", "Go", "Terraform"),
        ),
        (
            "Technical Skills: Terraform, Go",
            [],
            ("Terraform", "Go"),
        ),
        (
            "Skills: Spring, Excel",
            [],
            ("Spring", "Excel"),
        ),
        (
            "Python, AWS, Docker, Terraform",
            ["Python", "AWS", "Docker"],
            ("Terraform",),
        ),
        (
            "Skills\n- Excel\n- Go",
            [],
            ("Excel", "Go"),
        ),
        (
            "Career Goals\nPython, AWS, Terraform",
            ["Python", "AWS"],
            (),
        ),
        (
            "Job requirements\nPython, AWS, Terraform",
            ["Python", "AWS"],
            (),
        ),
        (
            "Experience\nGo",
            [],
            (),
        ),
        (
            "Languages\nExcel",
            [],
            (),
        ),
        (
            "Skills\nNever used Go",
            [],
            (),
        ),
        (
            "Skills\nSpring 2026",
            [],
            (),
        ),
        (
            "I go to work every day.",
            [],
            (),
        ),
        (
            "Skills\nGo to college",
            [],
            (),
        ),
        (
            "Skills\nExcel\nExcel\nGo\nGo",
            [],
            ("Excel", "Go"),
        ),
    ],
)
def test_conservative_skill_proposals(
    resume,
    existing,
    expected,
):
    assert propose_additional_skills(resume, existing) == expected


def test_does_not_reintroduce_existing_skills():
    assert propose_additional_skills(
        "Skills\nExcel\nGo\nSpring",
        ["Excel", "Go"],
    ) == ("Spring",)


def test_does_not_mutate_existing_skill_list():
    existing = ["Python", "AWS", "Docker"]
    before = existing.copy()

    result = propose_additional_skills(
        "Python, AWS, Docker, Terraform",
        existing,
    )

    assert result == ("Terraform",)
    assert existing == before
    assert EXPERIMENT_VERSION == "skill-recall-shadow-v1"
